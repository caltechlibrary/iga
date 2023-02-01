'''
record.py: record structure creation & manipulation

This file is part of https://github.com/caltechlibrary/iga/.

The code in this file constructs a metadata record in the format expected by
InvenioRDM. It uses data provided in a GitHub release as well as the repository
(and files in the repository), but because GitHub releases and repos don't
directly contain the information needed, we have to resort to looking for and
parsing files in the repo to try to extract the info we want. The most useful
such files are codemeta.json and CITTATION.cff, but we resort to other things
if we can't find them.

CITATION.cff and codemeta.json overlap in their contents, so a natural question
is which one to try to use first. Stephan Druskat wrote the following about
them in https://github.com/citation-file-format/cff-converter-python/issues/4:

* "CodeMeta aims to, generally, provide a minimal schema for metadata
  for research software. It isn't necessarily tailored for citation metadata
  but can be used to provide metadata that can be used for citation."

* "CFF aims to provide a format for the explicit and exclusive provision of
  citation metadata for research software. Things like transformability to
  BibTeX and RIS have been taken into account. As such, CFF is both less
  comprehensive in terms of general metadata (although I will extend it to
  cover the whole key set of CodeMeta at some point), and more "detailed" in
  terms of citation metadata."

Since the use of InvenioRDM is more about archiving repository code than about
citing software, the code below looks for and uses codemeta.json first,
followed by CITATION.cff if a codemeta file can't be found.

Copyright (c) 2022 by the California Institute of Technology.  This code
is open-source software released under a BSD-type license.  Please see the
file "LICENSE" for more information.
'''

import arrow
import copy
import json5
from   os import path
from   sidetrack import log
import sys

from iga.exceptions import InternalError, MissingData
from iga.github import (
    github_release,
    github_repo,
    github_repo_file,
    github_repo_filenames,
    github_file_url,
    github_user
)


# Constants.
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# It's useful to understand the context of what's going on. A record stored
# in InvenioRDM may have these top-level fields (but might not contain all):
#
# {
#    "$schema": "local://records/record-vX.Y.Z.json",
#    "id": "q5jr8-hny72",
#    "pid": { ... },
#    "pids" : { ... },
#    "parent": { ... },
#    "access" : { ... },
#    "metadata" : { ... },
#    "files" : { ... },
#    "tombstone" : { ... },
#    "created": "...",
#    "updated": "...",
# }
#
# However, what is uploaded to an InvenioRDM server should only contain the
# 'metadata' field, because of the other fields above are added by the system.
# Consequently, IGA only needs to construct the 'metadata' field value. I.e.,
# referring to https://inveniordm.docs.cern.ch/reference/metadata, we are only
# concerned with https://inveniordm.docs.cern.ch/reference/metadata/#metadata
#
# The following is the full set of possible subfields in "metadata".

FIELDS = [
    "additional_descriptions",
    "additional_titles",
    "contributors",
    "creators",
    "dates",
    "description",
    "formats",
    "funding",
    "identifiers",
    "languages",
    "locations",
    "publication_date",
    "publisher",
    "references",
    "related_identifiers",
    "resource_type",
    "rights",
    "sizes",
    "subjects",
    "title",
    "version",
]

# Not all of these need to be provided.  Based on the test cases in
# https://github.com/inveniosoftware/invenio-rdm-records, the minimum set of
# fields that needs to be provided seems to be this:
#
# {
#    "metadata": {
#        "resource_type": { "id": "XYZ", ... },          # note below
#        "title": "ABC",
#        "creators": [
#              {
#                  "person_or_org": {
#                      "family_name": "A",
#                      "given_name": "B",
#                      "type": "C",
#                  }
#              },
#            ],
#        "publication_date": "...date...",
#    }

REQUIRED_FIELDS = [
    "creators",
    "publication_date",
    "resource_type",
    "title"
]

# Vocabularies variable CV gets loaded only if record_for_release(...) is
# called. The name mapping is to map the values from caltechdata_api's
# get_vocabularies to something more self-explanatory when used in this file.

CV = {}
CV_NAMES = {'crr'   : 'creator-roles',
            'cor'   : 'contributor-roles',
            'rsrct' : 'resource-types',
            'dty'   : 'description-types',
            'dat'   : 'data-types',
            'rlt'   : 'relation-types',
            'ttyp'  : 'title-types;',
            'idt'   : 'identifier-types'}


# Exported module functions.
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def record_for_release(account, repo, tag):
    '''Return the "metadata" part of an InvenioRDM record.

    Data is gathered from the GitHub release identified by "tag" in the
    repository "repo" of the given GitHub "account".
    '''
    release = github_release(account, repo, tag)
    repo = github_repo(account, repo)

    # We use codemeta.json & CITATION.cff often. Get them now & augment the
    # repo object with them so that field extraction functions can access them.
    repo.codemeta = {}
    repo.cff = {}
    filenames = github_repo_filenames(repo)
    if 'codemeta.json' in filenames:
        repo.codemeta = json5.loads(github_repo_file(repo, 'codemeta.json'))
    cff_filename = None
    if 'CITATION.cff' in filenames:
        cff_filename = 'CITATION.cff'
    elif 'CITATION.CFF' in filenames:
        cff_filename = 'CITATION.CFF'
    if cff_filename:
        import yaml
        repo.cff = yaml.safe_load(github_repo_file(repo, cff_filename))

    load_vocabularies()

    # Make the metadata dict by iterating over the names in FIELDS and calling
    # the function of that name defined in this (module) file.
    module = sys.modules[__name__]

    def field_function(field):
        return getattr(module, field)(repo, release)

    metadata = {field: field_function(field) for field in FIELDS}
    return {"metadata": metadata}


def valid_record(json_dict):
    '''Perform basic validation on the "metadata" part of the given record.

    The validation process currently on tests that the record has the
    minimum fields; it does not currently check the field values or types.
    '''
    if 'metadata' not in json_dict:
        log('record lacks a "metadata" field')
        return False
    metadata = json_dict['metadata']
    # Yes, this could be done by a simple 1-liner, but we want to log failures.
    for field in REQUIRED_FIELDS:
        if field not in metadata:
            log('record metadata lacks required field "' + field + '"')
            return False
    log('record metadata has the required minimum set of fields')
    return True


# Field value functions.
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Summary of the approach: the functions for extracting values from GitHub
# are named after the fields themselves, so that record_from_release(...)
# above can create a record by simply iterating over the names in FIELDS and
# calling the function of that name to get the value for that field.

def additional_descriptions(repo, release):
    '''Return InvenioRDM "additional descriptions".
    https://inveniordm.docs.cern.ch/reference/metadata/#additional-descriptions-0-n
    '''
    # First try to use "description" from codemeta.json, then "abstract" from
    # citation.cff. If neither are available, default to the repo description,
    # but since the repo descriptions rarely seem to add anything beyond the
    # codemeta/cff ones, don't add both.
    #
    # Note: InvenioRDM's metadata schema offers a type value "abstract" as
    # one of the possible type values for an additional_description, but I
    # think it's better to use the type "other" here even if we do extract
    # the "abstract" from the CITATION.cff file. My reasoning is that the
    # abstract in the CITATION.cff file refers to the whole repository, not
    # the release, so in the way it's being used here (as part of a description
    # of a software release), it's not being used as an abstract.
    text = (repo.codemeta.get('description', None)
            or repo.cff.get('abstract', None)
            or repo.description)
    if text:
        return [{'description': text,
                 'type': {'id': 'other', 'title': {'en': 'Other'}}}]
    else:
        return []


def additional_titles(repo, release):
    '''Return InvenioRDM "additional titles".
    https://inveniordm.docs.cern.ch/reference/metadata/#additional-titles-0-n
    '''
    # If we can't get a name or title from the codemeta or cff files, give up.
    # The GitHub data doesn't offer anything we can use in this regard.
    if name := repo.codemeta.get('name', '') or repo.cff.get('title', ''):
        version = repo.codemeta.get('version', '') or repo.cff.get('version', '')
        title = name + (f' (version {version})' if version else '')
        return [{'title': title,
                 'type': {'id': 'alternative-title',
                          'title': {'en': 'Alternative Title'}},
                 'lang': {'id': 'eng'},
                 }]
    else:
        return []


# fixme: role must be set for contributors, and it uses a CV

def contributors(repo, release):
    '''Return InvenioRDM "contributors".
    https://inveniordm.docs.cern.ch/reference/metadata/#contributors-0-n
    '''
    clist = repo.codemeta.get('contributor', []) or repo.cff.get('contributors', [])
    return [_person(x) for x in clist]


def creators(repo, release):
    '''Return InvenioRDM "creators".
    https://inveniordm.docs.cern.ch/reference/metadata/#creators-1-n
    '''
    # Codemeta & CITATION.cff files contain more complete author info than the
    # GitHub release data, so try them 1st.
    authors = repo.codemeta.get('author', []) or repo.cff.get('author', [])
    if authors:
        return [_person(x) for x in authors]

    # Couldn't get authors from codemeta.json or CITATION.cff. Try the release
    # user first and not the repo owner, because the latter may be an org.
    account = _release_author(release) or _repo_owner(repo)
    if account:
        return [account]

    # A release in InvenioRDM can't be made without author data.
    raise MissingData('Unable to extract author info from GitHub release or repo.')


def dates(repo, release):
    '''Return InvenioRDM "dates".
    https://inveniordm.docs.cern.ch/reference/metadata/#dates-0-n
    '''
    created_date = arrow.get(release.created_at)
    return [{'date': created_date.format('YYYY-MM-DD'),
             'type': {'id': 'created', 'title': {'en': 'Created'}}}]


def description(repo, release):
    '''Return InvenioRDM "description".
    https://inveniordm.docs.cern.ch/reference/metadata/#description-0-1
    '''
    return release.body.strip() if release.body else ''


def formats(repo, release):
    '''Return InvenioRDM "formats".
    https://inveniordm.docs.cern.ch/reference/metadata/#formats-0-n
    '''
    # fixme
    return []


# FIXME: funding function currently doesn't try to get id's at all, and only
# works with names, to avoid having to match up CVs. This could be improved.

def funding(repo, release):
    '''Return InvenioRDM "funding references".
    https://inveniordm.docs.cern.ch/reference/metadata/#funding-references-0-n
    '''
    # codemeta.json has "funding" & "funder": https://codemeta.github.io/terms/.
    # CITATION.cff doesn't have anything for funding currently.
    funding = repo.codemeta.get('funding', '')
    funder  = repo.codemeta.get('funder', '')

    # Funding references in InvenioRDM must have both funder & award info. We
    # need to extract both, or we give up. But sometimes people put funder info
    # into the funding field, so here we only test for non-empty "funding".
    if not funding:
        return []

    # Some people don't actually provide funding info but also don't leave the
    # fields blank. Don't bother putting these in the InvenioRDM record.
    na = ['n/a', 'not available']
    if isinstance(funding, str) and any(text in funding.lower() for text in na):
        return []

    # OK, we're diving in. Things get messy because codemeta.json files often
    # have user errors and don't adhere to the codemeta spec. Officially,
    # funding is supposed to be a text string, and funder is supposed to be a
    # person or org (=> dict). But we can't count on it. Need to be flexible.

    funder_name = ''
    if isinstance(funder, dict):
        # Correct data type. People seem unsure what to use as the name key.
        funder_name = funder.get('name', '') or funder.get('@name', '')
    elif isinstance(funder, str) and funder:
        # Incorrect data type, but let's take it anyway. Use the whole string.
        funder_name = funder

    if isinstance(funding, str):
        # Correct data type. If there's only one token, it's probably an award
        # identifier or number. If there's more than one token, then we can't
        # reliably parse out the grant id, so give up and use the whole string.
        if len(funding) == 1:
            if funder_name:
                return [funding_item(funder_name, award_id=funding)]
            else:
                # Got a funding id of some kind, but no funder => incomplete.
                return []
        else:
            # String has more than one token. Assume it's NOT an award id.
            return [funding_item(funder_name, award_name=funding)]
    elif isinstance(funding, list):
        # Not the intended data type, but a lot of codemeta.json files use it.
        if all(isinstance(item, str) for item in funding):
            # List of strings => treat each as separate grant name or desc.
            return [funding_item(funder_name, award_name=item) for item in funding]
        elif all(isinstance(item, dict) for item in funding):
            # List of dicts is really not the correct data type, but we can try
            # our best based on examples seen in the wild.
            results = []
            for item in funding:
                item_name = item.get('name', '') or item.get('@name', '')
                if not item_name:
                    continue
                item_type = item.get('@type', '').lower()
                if item_type in ['award', 'grant']:
                    results.append(funding_item(funder_name, award_name=item_name))
                else:
                    continue
            return results
        else:
            # It's not a list of strings or dicts, so this is beyond us.
            return []
    elif isinstance(funding, dict):
        # Wrong data type, but we might be able to handle a simple case.
        award_id = ''
        if 'funder' in funding:
            if funder_name:
                # We've already found a funder in the codemeta file, and now
                # this has another value. This is beyond what we can handle.
                return []
            fun = funding['funder']
            if isinstance(fun, str):
                funder_name = fun
            elif isinstance(fun, dict):
                funder_name = fun.get('name', '') or fun.get('@name', '')
        award_id = funding.get('identifier', '')
        if funder_name and award_id:
            return [funding_item(funder_name, award_name=award_id)]

    # Fall-through for when nothing else works.
    return []


def identifiers(repo, release):
    '''Return InvenioRDM "alternate identifiers".
    https://inveniordm.docs.cern.ch/reference/metadata/#alternate-identifiers-0-n
    '''
    # Codemeta has 'identifier', which can be a URL, text or dict. If it's a
    # URL or string, we currently don't handle it b/c it requires intelligently
    # figuring out a corresponding InvenioRDM id scheme. (FIXME: should be able
    # to handle some cases like PURLs.)  CITATION.cff has 'identifiers'.

    identifiers = []
    items = [repo.codemeta.get('identifier', '')] + repo.cff.get('identifiers', [])
    for item in items:
        if not isinstance(item, dict):
            continue
        kind = item.get('propertyID', '') or item.get('type', '')
        kind = kind.lower()
        value = item.get('value', '')
        # We skip DOI and OAI id's in this particular context.
        if value and kind in CV['identifier-types'] and kind not in ['doi', 'oai']:
            identifiers.append({'identifier': value,
                                'scheme': kind})
    return identifiers


def languages(repo, release):
    '''Return InvenioRDM "languages".
    https://inveniordm.docs.cern.ch/reference/metadata/#languages-0-n
    '''
    # GitHub doesn't provide a way to deal with any other human language.
    return [{"id": "eng", 'title': {'en': 'English'}}]


def locations(repo, release):
    '''Return InvenioRDM "locations".
    https://inveniordm.docs.cern.ch/reference/metadata/#locations-0-n
    '''
    return []


def publication_date(repo, release):
    '''Return InvenioRDM "publication date".
    https://inveniordm.docs.cern.ch/reference/metadata/#publication-date-1
    '''
    return arrow.get(release.published_at).format('YYYY-MM-DD')


def publisher(repo, release):
    '''Return InvenioRDM "publisher".
    https://inveniordm.docs.cern.ch/reference/metadata/#publisher-0-1
    '''
    return 'CaltechDATA'


def references(repo, release):
    '''Return InvenioRDM "references".
    https://inveniordm.docs.cern.ch/reference/metadata/#references-0-n
    '''
    # FIXME some people put paper citation info in CITATION.cff
    # See eg https://github.com/plasma-umass/scalene
    return []


def related_identifiers(repo, release):
    '''Return InvenioRDM "related identifiers/works".
    https://inveniordm.docs.cern.ch/reference/metadata/#related-identifiersworks-0-n
    '''
    from url_normalize import url_normalize

    identifiers = [{'identifier': release.html_url,
                    'relation_type': {'id': 'isidenticalto',
                                      'title': {'en': 'Is identical to'}},
                    'resource_type': {'id': 'software',
                                      'title': {'en': 'Software'}},
                    'scheme': 'url'}]
    if repo.homepage:
        identifiers.append({'identifier': url_normalize(repo.homepage),
                            'relation_type': {'id': 'isdescribedby',
                                              'title': {'en': 'Is described by'}},
                            'resource_type': {'id': 'other',
                                              'title': {'en': 'Other'}},
                            'scheme': 'url'})
    if repo.has_pages:
        pages_url = f'https://{repo.owner.login}.github.io/{repo.name}'
        identifiers.append({'identifier': pages_url,
                            'relation_type': {'id': 'isdocumentedby',
                                              'title': {'en': 'Is documented by'}},
                            'resource_type': {'id': 'publication-softwaredocumentation',
                                              'title': {'en': 'Software documentation'}},
                            'scheme': 'url'})

    if ispartof := repo.codemeta.get('isPartOf', ''):
        identifiers.append({'identifier': ispartof,
                            'relation_type': {'id': 'ispartof',
                                              'title': {'en': 'Is part of'}},
                            'resource_type': {'id': 'collection',
                                              'title': {'en': 'Collection'}},
                            'scheme': 'url'})

    # The codemeta spec says "relatedLink" value is supposed to be a URL, but
    # lots of codemeta.json files use a list. The nature of the relation is
    # more problematic.  We don't really know what the links are meant to be,
    # nor the direction of the relationships. The codemeta spec says this is
    # "A link related to this object, e.g., related web pages", and examples
    # of codemeta.json files in the wild suggest that people put links to
    # pages that describe or reference this repo and/or this release; for
    # these reasons, this code uses IsReferencedBy, but it's only a guess.
    if related_links := repo.codemeta.get('relatedLink', None):
        if isinstance(related_links, str):
            related_links = [related_links]
        for url in filter(lambda x: x.startswith('http'), related_links):
            url = url_normalize(url)
            # Don't add URLs we've already added (possibly as another type).
            if url in [item['identifier'] for item in identifiers]:
                continue
            identifiers.append({'identifier': url,
                                'relation_type': {'id': 'isreferencedby',
                                                  'title': {'en': 'Is referenced by'}},
                                'resource_type': {'id': 'other',
                                                  'title': {'en': 'Other'}},
                                'scheme': 'url'})

    return identifiers


def resource_type(repo, release):
    '''Return InvenioRDM "resource type".
    https://inveniordm.docs.cern.ch/reference/metadata/#resource-type-1
    '''
    # FIXME handle other types like datasets
    return {'id': 'software', 'title': {'en': 'Software'}}


def rights(repo, release):
    '''Return InvenioRDM "rights (licenses)".
    https://inveniordm.docs.cern.ch/reference/metadata/#rights-licenses-0-n
    '''
    if value := repo.codemeta.get('license', '') or repo.cff.get('license', ''):
        license_id = None
        from iga.licenses import LICENSES
        from url_normalize import url_normalize
        # People tend to put either a URL or the name of a license here.
        if value.startswith('http'):
            # Is it a link to an spdx license?
            license_urls = [lic.url.lower() for lic in LICENSES.values()]
            url =  url_normalize(value.lower())
            if url in license_urls or url.rstrip('html') in license_urls:
                license_id = value.rstrip('.html').split('/')[-1]
        elif value in LICENSES:
            # Not a URL but a name, and we recognize it.
            license_id = value
        else:
            log('found a license value but did not recognize it: ' + value)

        if license_id:
            log('license value is a recognized kind: ' + license_id)
            return [{'id'         : license_id,
                     'title'      : {'en': LICENSES[license_id].title},
                     'description': {'en': LICENSES[license_id].description},
                     'link'       : LICENSES[license_id].url}]

    # We don't have a codemeta or cff file, or else found no license in them.
    # Look into the GitHub repo data to see if GitHub identified a license.
    if repo.license and repo.license.name != 'Other':
        log('using license info assigned by GitHub')
        spdx_id = repo.license.spdx_id
        rights = {'id': spdx_id,
                  'link': repo.license.url,
                  'title': {'en': repo.license.name}}
        from iga.licenses import LICENSES
        if spdx_id in LICENSES:
            rights['description'] = {'en': LICENSES[spdx_id]}
        return [rights]

    # GitHub didn't fill in the license info -- maybe it didn't recognize
    # the license or its format. Try to look for a license file ourselves.
    filenames = github_repo_filenames(repo)
    base_url = 'https://github.com/' + repo.owner.login + '/' + repo.name
    for basename in ['LICENSE', 'License', 'license',
                     'LICENCE', 'Licence', 'licence',
                     'COPYING', 'COPYRIGHT', 'Copyright', 'copyright']:
        for ext in ['', '.txt', '.md', '.html']:
            if basename + ext in filenames:
                log('found a license file in the repo: ' + basename + ext)
                # There's no safe way to summarize arbitrary license text,
                # so we can't provide a 'description' field value.
                return [{'title': {'en': 'License'},
                         'link': base_url + '/' + basename + ext}]

    log('could not find a license')
    return []


def sizes(repo, release):
    '''Return InvenioRDM "sizes".
    https://inveniordm.docs.cern.ch/reference/metadata/#sizes-0-n
    '''
    # fixme
    return []


def subjects(repo, release):
    '''Return InvenioRDM "subjects".
    https://inveniordm.docs.cern.ch/reference/metadata/#subjects-0-n
    '''
    return [{'subject': x} for x in repo.topics if x.lower() != 'github']


def title(repo, release):
    '''Return InvenioRDM "title".
    https://inveniordm.docs.cern.ch/reference/metadata/#title-1
    '''
    return repo.full_name + ': ' + (release.name or release.tag_name)


def version(repo, release):
    '''Return InvenioRDM "version".
    https://inveniordm.docs.cern.ch/reference/metadata/#version-0-1
    '''
    # Note: this is not really the same as a version number. However, there is
    # no version number in the GitHub release data -- there is only the tag.
    # The following does a weak heuristic to try to guess at a version number
    # from certain common tag name patterns, but that's the best we can do.
    tag = release.tag_name
    if tag.startswith('v'):
        import re
        tag = re.sub(r'v(er|version)?[ .]?', '', tag)
    return tag.strip()


# Miscellaneous helper functions.
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# See https://inveniordm.docs.cern.ch/reference/metadata/#creators-1-n for
# info about the fields for authors in InvenioRDM.

# fixme ROR

def _person(person_dict):
    # Although people sometimes put more things in the CITATION.cff authors
    # info (e.g., email addr), there's no provision in InvenioRDM for that.
    person = {'family_name': _flattened_name(person_dict.get('familyName', '')),
              'given_name': _flattened_name(person_dict.get('givenName', '')),
              'type': 'personal'}
    if 'orcid' in person_dict.get('@id', ''):
        orcid = person_dict['@id'].split('/')[-1]
        person.update({'identifiers': [{'scheme': 'orcid',
                                        'identifier': orcid}]})

    structure = {'person_or_org': person}
    if 'affiliation' in person_dict:
        affiliation = person_dict['affiliation']
        if isinstance(affiliation, dict):
            # In CITATION.cff, the field name is 'legalName'.
            # In codemeta.json, it's 'name'.
            name = affiliation.get('legalName', '') or affiliation.get('name', '')
        else:
            name = affiliation
        structure.update({'affiliations': [{'name': name}]})
    return structure


def _person_from_github(github_user):
    (given, surname) = _split_name(github_user.name)
    person = {'given_name': given,
              'family_name': surname,
              'type': 'personal'}
    if github_user.company:
        person.update({'affiliations': [{'name': github_user.company}]})
    return person


def _release_author(release):
    # We can call GitHub's user data API, but it returns very little info
    # about a user (e.g.,, it gives a name but that name is not broken out
    # into family & given name), plus sometimes fields are empty.
    user = github_user(release.author.login)
    return None if not user.name else _person_from_github(user)


def _repo_owner(repo):
    owner = github_user(repo.owner.login)
    if owner.type == 'Organization':
        return {'name': owner.name,
                'type': 'organizational'}
    elif owner.name:
        return _person_from_github(owner)
    else:
        return {}


def _split_name(name):
    # Trying to split names automatically into parts is not only impossible
    # in general, but also undesirable: not all cultures use names with only
    # first and/or last name components, or just one last name, or in the
    # same order as Western names, etc. However, we have no choice in this
    # program, because the InvenioRDM record format wants first & last names.
    #
    # The approach taken here is roughly:
    #  1) strip non-Latin characters and non-alpha characters from the string
    #  2) if the result is only a single word, treat it as a surname only
    #  3) invoke a machine learning-based name parser (ProbablePeople) to do
    #     a best-effort attempt at splitting the name into given + surname
    #  4) PP is prone to failures on some names, so if it fails, fall back to
    #     using a different name parser (nameparser) that doesn't split names
    #     quite as correctly as PP, but is better than nothing.

    log('splitting name ' + name)
    name = _cleaned_name(name)
    if len(name.split(' ')) == 1:
        # Only one word in the name. Either it is really a single name (e.g.,
        # in cultures where people have single names) or someone is being cute.
        log('treating single name as the family name')
        given = ''
        surname = name
    else:
        try:
            log('trying to split name using probablepeople')
            import probablepeople as pp
            from_pp = pp.tag(name)
            # PP gets better results if you DON'T supply the 'type' parameter.
            # (I don't know why.) Use that 1st, unless it guesses wrong about
            # the type, in which case, we run it again using type=person.
            if from_pp[1] != 'Person':
                from_pp = pp.tag(_cleaned_name(name), type='person')
            parsed = from_pp[0]
            # If it found initials instead of full names, use those.
            if parsed.get('FirstInitial', ''):
                given = parsed.get('FirstInitial')
            else:
                # Get rid of periods at the end, in case someone got cute.
                given = parsed.get('GivenName', '').rstrip('.')

            # For some reason, it seems the InvenioRDM records include the
            # middle names as part of the first/given names, so:
            if parsed.get('MiddleInitial', ''):
                given += (' ' + parsed.get('MiddleInitial'))
            elif parsed.get('MiddleName', ''):
                given += (' ' + parsed.get('MiddleName'))

            if parsed.get('LastInitial', '') and not parsed.get('Surname', ''):
                surname = parsed.get('LastInitial').title()
            else:
                surname = parsed.get('Surname', '')
        except Exception:                   # noqa: PIE786
            log(f'switching to nameparser b/c probablepeople failed on "{name}"')
            from nameparser import HumanName
            parsed = HumanName(name)
            # (Noted above) InvenioRDM includes middle name as part of 1st name:
            given = parsed.first + ' ' + parsed.middle
            surname = parsed.last

    # Carefully upper-case the first letters.
    given = _upcase_first_letters(given)
    if _plain_word(surname):
        surname = surname.title()
    given = given.strip()
    surname = surname.strip()

    return (given, surname)


def _cleaned_name(name):
    import re
    import demoji
    # Remove parenthetical text like "Somedude [somedomain.io]".
    name = re.sub(r"\(.*?\)|\[.*?\]", "", name)
    # Remove CJK characters because the name parsers can't handle them.
    # This regex is from https://stackoverflow.com/a/2718268/743730
    name = re.sub(u'[⺀-⺙⺛-⻳⼀-⿕々〇〡-〩〸-〺〻㐀-䶵一-鿃豈-鶴侮-頻並-龎]', '', name)
    # Remove miscellaneous weird characters if there are any.
    name = demoji.replace(name)
    name = re.sub(r'[~`!@#$%^&*_+=?<>(){}|[\]]', '', name)
    # Replace typographical quotes with regular quotes, for PP's benefit.
    name = re.sub(r'[“”‘’]', '"', name)
    # Make sure periods are followed by spaces.
    name = name.replace('.', '. ')
    # Normalize runs of multiple spaces to one.
    name = re.sub(r' +', ' ', name)
    return name.strip()                 # noqa PIE781


def _plain_word(name):
    return (' ' not in name
            and not any(str.isdigit(c) for c in name)
            and (all(str.isupper(c) for c in name)
                 or not any(str.isupper(c) for c in name[1:])))


def _upcase_first_letters(name):
    return ' '.join(word[0].upper() + word[1:] for word in name.split())


def _flattened_name(name):
    '''Return name as a string even if it's a list and not a simple string.'''
    if isinstance(name, list):
        return ' '.join(part for part in name)
    else:
        return name


def funding_item(funder_name, award_id=None, award_name=None):
    # InvenioRDM says funder subfield must have id OR name, and award subfield
    # must have either id or both title and number.
    if award_id:
        return {'funder': {'name': funder_name},
                'award': {'id': award_id}}
    elif award_name:
        return {'funder': {'name': funder_name},
                'award': {'title': {'en': award_name}}}
    else:
        {}


def load_vocabularies():
    from caltechdata_api.customize_schema import get_vocabularies
    for name, vocab in get_vocabularies().items():
        CV.update({CV_NAMES[name]: vocab})
