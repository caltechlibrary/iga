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
import json5
from   sidetrack import log
import sys

from iga.data_utils import deduplicated, similar_urls, listified, cleaned_text
from iga.exceptions import MissingData
from iga.github import (
    github_release,
    github_repo,
    github_repo_file,
    github_repo_filenames,
    github_account
)
from iga.id_utils import detected_id, recognized_scheme
from iga.name_utils import split_name, flattened_name
from iga.reference import reference


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
        try:
            repo.codemeta = json5.loads(github_repo_file(repo, 'codemeta.json'))
            log('found and read codemeta.json file')
        except Exception as ex:
            log('ignoring codemeta.json file because of error: ' + str(ex))
    for name in ['CITATION.cff', 'CITATION.CFF', 'citation.cff']:
        if name in filenames:
            import yaml
            try:
                repo.cff = yaml.safe_load(github_repo_file(repo, name))
                log(f'found and read {name} file')
            except Exception as ex:
                log(f'ignoring {name} file because of error: ' + str(ex))
            break

    _load_vocabularies()

    # Make the metadata dict by iterating over the names in FIELDS and calling
    # the function of that name defined in this (module) file.
    module = sys.modules[__name__]

    def field_function(field):
        return getattr(module, field)(repo, release)

    metadata = {field: field_function(field) for field in FIELDS}
    return {"metadata": metadata}


def valid_record(data):
    '''Perform basic validation on the "metadata" part of the given record.

    The validation process currently on tests that the record has the
    minimum fields; it does not currently check the field values or types.
    '''
    if metadata := data.get('metadata', {}):
        # This could be done by a simple 1-liner, but we want to log failures.
        for field in REQUIRED_FIELDS:
            if field not in metadata:
                log('record metadata lacks required field "' + field + '"')
                return False
        else:
            log('record metadata validated to have minimum fields')
            return True
    else:
        log('record lacks a "metadata" field')
    return False


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
    descriptions = []

    # Description types come from DataCite, and can be: "abstract", "methods",
    # "series-information", "table-of-contents", "technical-info", "other".

    # If the GitHub release object doesn't have a description body, then we'll
    # end up using something else for our InvenioRDM record -- see the function
    # description() in this file. Only add the others here if we didn't there.
    if not release.body:
        desc = description(repo, release)

        rel_notes = repo.codemeta.get('releaseNotes', '').strip()
        if rel_notes != desc and not rel_notes.startswith('http'):
            # We didn't use the release notes as the description, so add it.
            descriptions.append({'description': rel_notes,
                                 'type': {'id': 'other',
                                          'title': {'en': 'Other'}}})

        # Codemeta's "description" and CITATION.cff's "abstract" are equivalent
        # according to the Codemeta crosswalk, so we only use one or the other.
        text = repo.codemeta.get('description', '') or repo.cff.get('abstract', '')
        text = text.strip()
        if text != desc:
            # There's a decision to be made about whether the CFF abstract
            # should be given description type "abstract" here. Examples of cff
            # files show that people invariably use it to describe the software
            # as a whole, not the release. Consequently, as an additional
            # description for the *release*, it's not acting as an abstract.
            descriptions.append({'description': text,
                                 'type': {'id': 'other',
                                          'title': {'en': 'Other'}}})

    # Codemeta's "readme" maps to DataCite's "technical-info". (DataCite's docs
    # say "For software description, this may include a readme.txt ...".)
    if readme := repo.codemeta.get('readme', '').strip():
        if readme.startswith('http'):
            readme = f'Additional information is available at {readme}'
        descriptions.append({'description': readme,
                             'type': {'id': 'technical-info',
                                      'title': {'en': 'Technical Info'}}})

    return descriptions


def additional_titles(repo, release):
    '''Return InvenioRDM "additional titles".
    https://inveniordm.docs.cern.ch/reference/metadata/#additional-titles-0-n
    '''
    # If we can't get a name or title from the codemeta or cff files, give up.
    # The GitHub data doesn't offer anything we can use in this regard.
    if name := (repo.codemeta.get('name', '') or repo.cff.get('title', '')):
        version = repo.codemeta.get('version', '') or repo.cff.get('version', '')
        title = name + (f' (version {version})' if version else '')
        return [{'title': cleaned_text(title),
                 'type': {'id': 'alternative-title',
                          'title': {'en': 'Alternative Title'}},
                 'lang': {'id': 'eng'},
                 }]
    else:
        return []


def contributors(repo, release):
    '''Return InvenioRDM "contributors".
    https://inveniordm.docs.cern.ch/reference/metadata/#contributors-0-n
    '''
    contributors = []

    # CFF's contact field is defined as a single object.
    if contact := repo.cff.get('contact', {}):
        contributors.append(_identity(contact, role='contactperson'))

    # Codemeta's "maintainer" is a person, but people often use a list here.
    # InvenioRDM roles lack an explicit term for maintainer, so we use "other".
    for maintainer in listified(repo.codemeta.get('maintainer', {})):
        contributors.append(_identity(maintainer, role='other'))

    # Both codemeta & cff files may have lists of contributors. Give priority
    # to codemeta. Comparing names is error-prone and we can't reliably detect
    # duplicates, so use only one or the other, not both.
    for contributor in (listified(repo.codemeta.get('contributor', []))
                        or repo.cff.get('contributors', [])):
        role = 'other'
        if matched := _cv_match('contributor-roles', contributor.get('role', '')):
            role = matched
        contributors.append(_identity(contributor, role=role))

    # We're getting data from multiple sources & we might have duplicates.
    return deduplicated(contributors)


def creators(repo, release):
    '''Return InvenioRDM "creators".
    https://inveniordm.docs.cern.ch/reference/metadata/#creators-1-n
    '''
    # Codemeta & CFF files contain more complete author info than the GitHub
    # release data, so try them 1st.
    if authors := (listified(repo.codemeta.get('author', []))
                   or repo.cff.get('author', [])):
        return deduplicated(_identity(x) for x in authors)

    # Couldn't get authors from codemeta.json or CITATION.cff. Try the release
    # author first, followed by the repo owner.
    if identity := (_release_author(release) or _repo_owner(repo)):
        return [identity]

    # A release in InvenioRDM can't be made without author data.
    raise MissingData('Unable to extract author info from GitHub release or repo.')


def dates(repo, release):
    '''Return InvenioRDM "dates".
    https://inveniordm.docs.cern.ch/reference/metadata/#dates-0-n
    '''
    dates = []

    # Codemeta has a "dateCreated" field, which the codemeta crosswalk equates
    # to the GitHub repo "created_at" date.
    created_date = repo.codemeta.get('dateCreated', '') or repo.created_at
    dates.append({'date': arrow.get(created_date).format('YYYY-MM-DD'),
                  'type': {'id': 'created', 'title': {'en': 'Created'}}})

    # Codemeta has a "dateModified" field, which the codemeta crosswalk equates
    # to the GitHub repo "updated_at" date.
    mod_date = repo.codemeta.get('dateModified', '') or repo.updated_at
    dates.append({'date': arrow.get(mod_date).format('YYYY-MM-DD'),
                  'type': {'id': 'updated', 'title': {'en': 'Updated'}}})

    # If we used a different date for the publication_date value than the
    # release date in GitHub, we add the GitHub date as another type of date.
    pub_date = publication_date(repo, release)
    github_date = arrow.get(release.published_at).format('YYYY-MM-DD')
    if pub_date != github_date:
        dates.append({'date': github_date,
                      'type': {'id': 'available', 'title': {'en': 'Available'}}})

    # Codemeta has a "copyrightYear", but there's no equivalent elsewhere.
    if copyrighted := repo.codemeta.get('copyrightYear', ''):
        dates.append({'date': arrow.get(copyrighted).format('YYYY-MM-DD'),
                      'type': {'id': 'copyrighted', 'title': {'en': 'Copyrighted'}}})
    return dates


def description(repo, release):
    '''Return InvenioRDM "description".
    https://inveniordm.docs.cern.ch/reference/metadata/#description-0-1
    '''
    # The description that a user provides for a release in GitHub is stored
    # in the release data as "body". If the user omits the text, GitHub
    # automatically (sometimes? always?  not sure) displays text pulled from
    # commit messages. In those cases, the value of release.body that we get
    # through the API is empty. There doesn't seem to be a way to get the text
    # shown by GitHub in those cases, so we try other alternatives after this.
    if release.body:
        return release.body.strip()

    # Codemeta releaseNotes can be either text or a URL. If it's a URL, it
    # often points to a NEWS or ChangeLog or similar file in their repo.
    # Those files often describe every release ever made, and that just
    # doesn't work well for the purposes of an InvenioRDM record description.
    if rel_notes := repo.codemeta.get('releaseNotes', '').strip():
        if not rel_notes.startswith('http'):
            return rel_notes
        else:
            log('codemeta has releaseNotes in the form of a URL -- skipping')

    # Codemeta's "description" and CFF's "abstract" (which the Codemeta
    # crosswalk maps as equivalent) refer to the software or dataset overall,
    # not specifically to the release. Still, if there's nothing else, it seems
    # better to use this instead of leaving an empty description in the record.
    if text := (repo.codemeta.get('description', '') or repo.cff.get('abstract', '')):
        return text.strip()

    # Bummer.
    log('could not find a description')
    return ''


def formats(repo, release):
    '''Return InvenioRDM "formats".
    https://inveniordm.docs.cern.ch/reference/metadata/#formats-0-n
    '''
    # FIXME
    return []


def funding(repo, release):
    '''Return InvenioRDM "funding references".
    https://inveniordm.docs.cern.ch/reference/metadata/#funding-references-0-n
    '''
    # InvenioRDM funding references must have funder; award info is optional.

    # CITATION.cff doesn't have anything for funding currently.
    # codemeta.json has "funding" & "funder": https://codemeta.github.io/terms/.
    # Sometimes people mistakenly put funder info inside the "funding" items.
    funding_field = repo.codemeta.get('funding', '')
    funder_field  = repo.codemeta.get('funder', '')

    # Some people don't actually provide funding info, yet don't leave the
    # fields blank. We don't bother putting these in the InvenioRDM record.
    not_avail = ['n/a', 'not available']
    for item in listified(funding_field):
        if isinstance(item, str) and any(t in item.lower() for t in not_avail):
            return []

    # Funder is supposed to be a single item (a dict), but I've seen people use
    # a string and also a list of dict. If a list, things get tricky later.
    funder_tuples = []
    for item in listified(funder_field):
        if isinstance(item, dict):
            # Correct data type.
            funder_tuples.append(_funder_info(item))
        elif isinstance(item, str):
            # Incorrect data type. Let's take it anyway. Use the whole string.
            funder_tuples.append((item, ''))

    # If we have multiple values for funder, we can only make sense of it if we
    # do NOT also have funding award values. If we have multiple funders and
    # funding values, we have no way to match up funders to funding, so we have
    # to bail. However, InvenioRDM does allow a list of only funders.
    if len(funder_tuples) > 1:
        if not funding_field:
            return [_funding(funder, fid) for (funder, fid) in funder_tuples]
        else:
            log('cannot handle list of funders with separate funding values')
            return []

    # If we get here, we don't have more than one funder/funder_id.
    funder, funder_id = funder_tuples[0] if funder_tuples else ('', '')

    # The correct funding data type is text. Sometimes people use lists or dict.
    results = []
    for item in listified(funding_field):
        if isinstance(item, str):
            if not funder:
                # Maybe the string contains embedded funder info (e.g., if it's
                # a grant + agency name) but we have no way to reliably parse
                # that from a string. FIXME could apply ML-based NER.
                continue
            # If there's only one token in the funding item string, it's likely
            # an award id. If there's more than 1 token, we can't reliably
            # parse out the grant id, so give up and use the whole string.
            award_id = item if len(item) == 1 else ''
            award_name = item if len(item) > 1 else ''
            results.append(_funding(funder, funder_id, award_name, award_id))
        elif isinstance(item, dict):
            award_name = item.get('name', '') or item.get('@name', '')
            award_id = item.get('identifier', '')
            if not (award_name or award_id):
                continue
            # Some people put a funder object in the funding item dict.
            item_funder = ''
            item_funder_id = ''
            if fun := item.get('funder', {}):
                if isinstance(fun, str):
                    item_funder = fun
                elif isinstance(fun, dict):
                    item_funder, item_funder_id = _funder_info(fun)
            # If there's an overall funder name in the codemeta file & this
            # item also has its own funder name, use this item's value.
            item_funder = item_funder or funder
            item_funder_id = item_funder_id or funder_id
            if not item_funder or item_funder_id:
                continue
            results.append(_funding(item_funder, item_funder_id, award_name, award_id))
    return results


def identifiers(repo, release):
    '''Return InvenioRDM "alternate identifiers".
    https://inveniordm.docs.cern.ch/reference/metadata/#alternate-identifiers-0-n

    This is defined as "persistent identifiers for the resource other than the
    ones registered as system-managed internal or external persistent
    identifiers. This field is compatible with 11. Alternate Identifiers in
    DataCite."
    '''
    identifiers = []
    # Codemeta's "identifier" can be a URL, text or dict. CFF's "identifiers"
    # can be an array of dict. Make lists out of all of them & iterate.
    for item in (listified(repo.codemeta.get('identifier', []))
                 + repo.cff.get('identifiers', [])):
        if isinstance(item, str):
            kind = recognized_scheme(item)
            if kind in CV['identifier-types']:
                identifiers.append({'identifier': item,
                                    'scheme': kind})
        elif isinstance(item, dict):
            kind = item.get('type', '') or item.get('@type', '')
            kind = kind.lower()
            value = item.get('value', '')
            if value.startswith('http') and kind != 'url':
                value = detected_id(value) or value
            if value and kind in CV['identifier-types']:
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
    # InvenioRDM's publication_date is the date "when the resource was made
    # available". GitHub's release date is not necessarily the same -- someone
    # might do a release retroactively. So instead, we first try codemeta's
    # "datePublished", then CFF's "date-released", and finally the GitHub date.
    date = (repo.codemeta.get('datePublished', '')
            or repo.cff.get('date-released', '')
            or release.published_at)
    return arrow.get(date).format('YYYY-MM-DD')


def publisher(repo, release):
    '''Return InvenioRDM "publisher".
    https://inveniordm.docs.cern.ch/reference/metadata/#publisher-0-1
    '''
    return 'CaltechDATA'


def references(repo, release):
    '''Return InvenioRDM "references".
    https://inveniordm.docs.cern.ch/reference/metadata/#references-0-n
    '''
    # We also add these items as related identifiers (c.f. the corresponding
    # function) b/c InvenioRDM doesn't do much with "references". Still useful
    # b/c it stores free text references & provides compatibility w/ Zenodo.

    # Codemeta has "referencePublication". CFF has "references" & also
    # "preferred-citation". We collect what we can parse & try to make the list
    # unique. We're hampered by a lack of tools for parsing references from
    # codemeta & CFF files (as of Feb. 2023, even cffconvert doesn't handle
    # "references" or "preferred-citation") & the variety of things people put
    # in. For these reasons, we currently only work with things that have
    # recognizable id's. (Otherwise, we'd have to parse multiple bib formats.)

    # For the output, the InvenioRDM format of this field is very limited:
    #     "references": [{ "reference": "Nielsen et al,..",
    #                      "identifier": "10.1234/foo.bar",
    #                      "scheme": "other" }]
    # The list of allowed schemes is so limited that effectively the only one
    # we can use for publications is "other". The tough one is the "reference"
    # value, which is free text and supposed to be a "full reference string".

    identifiers = _codemeta_references(repo) | _cff_references(repo)
    return [{'reference': reference(_id), 'identifier': _id, 'scheme': 'other'}
            for _id in identifiers]


def related_identifiers(repo, release):
    '''Return InvenioRDM "related identifiers/works".
    https://inveniordm.docs.cern.ch/reference/metadata/#related-identifiersworks-0-n
    '''
    # Note about how to interpret the relations below: the direction is
    #   "this release" --> has relationship to --> "related resource identifier"

    from url_normalize import url_normalize

    identifiers = [{'identifier': url_normalize(release.html_url),
                    'relation_type': {'id': 'isidenticalto',
                                      'title': {'en': 'Is identical to'}},
                    'resource_type': {'id': 'software',
                                      'title': {'en': 'Software'}},
                    'scheme': 'url'}]

    # The GitHub repo is what this release is derived from. Note: you would
    # expect the GitHub repo html_url, the codemeta.json codeRepository, and
    # the CFF repository-code all to be the same value, but we can't be sure,
    # so we have to look at them, and use them in the order of priority.
    if repo_url := (repo.codemeta.get('codeRepository', '')
                    or repo.cff.get('repository-code', '')
                    or repo.html_url):
        identifiers.append({'identifier': url_normalize(repo_url),
                            'relation_type': {'id': 'isderivedfrom',
                                              'title': {'en': 'Is derived from'}},
                            'resource_type': {'id': 'software',
                                              'title': {'en': 'Software'}},
                            'scheme': 'url'})

    # A GitHub repo may give a homepage for the software, though users don't
    # always set it. CFF's "url" field is defined as "The URL of a landing
    # page/website for the software or dataset", which is the same concept.
    # Codemeta's "url" field is more ambiguously defined as "URL of the item",
    # but the codemeta crosswalk table equates it to CFF's url field.
    if homepage_url := (repo.codemeta.get('url', '')
                        or repo.cff.get('url', '')
                        or repo.homepage):
        identifiers.append({'identifier': url_normalize(homepage_url),
                            'relation_type': {'id': 'isdescribedby',
                                              'title': {'en': 'Is described by'}},
                            'resource_type': {'id': 'other',
                                              'title': {'en': 'Other'}},
                            'scheme': 'url'})

    # Codemeta's "sameAs" = "URL of a reference Web page that unambiguously
    # indicates the item’s identity." Note that relative to a release stored
    # in InvenioRDM, it is not "same as"; rather it's closer to "a version of".
    # There's no equivalent in CFF or the GitHub repo data structure.
    if sameas_url := repo.codemeta.get('sameAs', ''):
        identifiers.append({'identifier': url_normalize(sameas_url),
                            'relation_type': {'id': 'isversionof',
                                              'title': {'en': 'Is version of'}},
                            'resource_type': {'id': 'software',
                                              'title': {'en': 'Software'}},
                            'scheme': 'url'})

    # GitHub pages are usually used to document a given software package.
    # That's not necessarily documentation for this release of the software,
    # but it's the best we can do.
    doc_url = repo.codemeta.get('softwareHelp', '')
    if not doc_url and repo.has_pages:
        doc_url = f'https://{repo.owner.login}.github.io/{repo.name}'
    if doc_url:
        identifiers.append({'identifier': url_normalize(doc_url),
                            'relation_type': {'id': 'isdocumentedby',
                                              'title': {'en': 'Is documented by'}},
                            'resource_type': {'id': 'publication-softwaredocumentation',
                                              'title': {'en': 'Software documentation'}},
                            'scheme': 'url'})

    # Codemeta says "relatedLink" value is supposed to be a URL, but most files
    # use a list. The nature of the relationship is more problematic. The
    # codemeta spec says this is "A link related to this object, e.g., related
    # web pages"; however, in the codemeta.json file, we get zero info about
    # what the links are meant to be. Worse, relatedLink has no direct
    # equivalent in the relations CV in InvenioRDM. Since the direction is
    # "this release" --> relatedLink --> "something", the closest relationship
    # term seems to be "references", as in "this release references this link".
    if links := listified(repo.codemeta.get('relatedLink', None)):
        for url in filter(lambda x: x.startswith('http'), links):
            url = url_normalize(url)
            # We don't add URLs we've already added (possibly as another type).
            # The list needs to be recreated in the loop b/c we're adding to it.
            added_urls = [item['identifier'] for item in identifiers]
            # We compare URLs loosely b/c people frequently put https in one
            # place and http in another, or add an extraneous trailing slash.
            if any(similar_urls(url, added) for added in added_urls):
                continue
            # There's no good way to know what the resource type actually is.
            identifiers.append({'identifier': url,
                                'relation_type': {'id': 'references',
                                                  'title': {'en': 'References'}},
                                'resource_type': {'id': 'other',
                                                  'title': {'en': 'Other'}},
                                'scheme': 'url'})

    # We already added codemeta & CFF "references" field values to InvenioRDM's
    # field "references" (c.f. function references() in this file); however,
    # InvenioRDM doesn't do much with the "references" field & data.caltech.edu
    # doesn't currently show it, so we also add the items as related ids here.
    added_identifiers = [detected_id(item['identifier']) for item in identifiers]
    for _id in (_codemeta_references(repo) | _cff_references(repo)):
        if _id not in added_identifiers:
            identifiers.append({'identifier': _id,
                                'relation_type': {'id': 'isreferencedby',
                                                  'title': {'en': 'Is referenced by'}},
                                'scheme': recognized_scheme(_id)})

    return identifiers


def resource_type(repo, release):
    '''Return InvenioRDM "resource type".
    https://inveniordm.docs.cern.ch/reference/metadata/#resource-type-1
    '''
    # The only clear source of info about whether this is software or data is
    # the CFF file field "type", so if we can't use that, default to software.
    if repo.cff.get('type', '') == 'dataset':
        return {'id': 'dataset', 'title': {'en': 'Dataset'}}
    else:
        return {'id': 'software', 'title': {'en': 'Software'}}


def rights(repo, release):
    '''Return InvenioRDM "rights (licenses)".
    https://inveniordm.docs.cern.ch/reference/metadata/#rights-licenses-0-n
    '''
    # Strategy: look in codemeta and citation first, trying to recognize common
    # licenses. If that fails, we look at GitHub's license info for the repo.
    # If that also fails, we go rummaging in the repo files.

    rights = []

    # Codemeta's "license" is usually a URL, but sometimes people don't know
    # that and use the name of a license instead. For CFF, "license" is
    # supposed to be a name. CFF also has a separate "license-url" field.
    if value := (repo.codemeta.get('license', '')
                 or repo.cff.get('license', '')
                 or repo.cff.get('license-url', '')):
        license_id = None
        from iga.licenses import LICENSES, LICENSE_URLS
        from url_normalize import url_normalize
        if value in LICENSES:
            # It's a common license name that we know about.
            license_id = value
        elif value.startswith('http'):
            # Is it a URL for a known license?
            url = url_normalize(value.lower().removesuffix('.html'))
            if url in LICENSE_URLS:
                license_id = LICENSE_URLS[url]
        else:
            log('found a license value but did not recognize it: ' + value)

        if license_id:
            log('license value is a recognized kind: ' + license_id)
            rights = {'id'   : license_id,
                      'title': {'en': LICENSES[license_id].title},
                      'link' : LICENSES[license_id].url}
            if LICENSES[license_id].description:
                rights['description'] = {'en': LICENSES[license_id].description}
            return [rights]

    # We didn't recognize license info in the codemeta or cff files.
    # Look into the GitHub repo data to see if GitHub identified a license.
    if repo.license and repo.license.name != 'Other':
        log('using license info assigned by GitHub')
        spdx_id = repo.license.spdx_id
        rights = {'id': spdx_id,
                  'link': repo.license.url,
                  'title': {'en': repo.license.name}}
        from iga.licenses import LICENSES
        if spdx_id in LICENSES and LICENSES[spdx_id].description:
            rights['description'] = {'en': LICENSES[spdx_id].description}
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
                rights = {'title': {'en': 'License'},
                          'link': base_url + '/' + basename + ext}
                break
        else:
            continue
        break
    return [rights]


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
    # We create a union of the repo topics and "keywords" from codemeta & cff.
    subjects = set(repo.topics)

    if keywords := repo.codemeta.get('keywords', []):
        if isinstance(keywords, str):
            # People sometimes use a single string with keywords separated by
            # a comma or semicolon. Default to blank space.
            if ',' in keywords:
                subjects.update(keywords.split(','))
            elif ';' in keywords:
                subjects.update(keywords.split(';'))
            else:
                subjects.update(keywords.split())
        elif isinstance(keywords, list) and isinstance(keywords[0], str):
            subjects.update(keywords)
        else:
            log('found keywords with unrecognized format in codemeta.json')

    if keywords := repo.cff.get('keywords', []):
        subjects.update(keywords)

    return [{'subject': x} for x in subjects]


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
# info about the fields for authors in InvenioRDM. Although people sometimes
# put more things in (e.g.) CITATION.cff authors info (e.g., email addr),
# there's no provision in InvenioRDM for that.

def _identity(data, role=None):
    person = {}
    org = {}

    _type = data.get('@type', '') or data.get('type', '')
    if _type.lower().strip() == 'person':
        # Deal with field name differences between codemeta & CFF.
        family = data.get('family-names', '') or data.get('familyName', '')
        given  = data.get('given-names', '') or data.get('givenName', '')

        # Do our best to obtain names split into family & given.
        if not (family or given) and (name := data.get('name', '')):
            # Schema.org allows single names too. Try to split it if we can.
            if isinstance(name, list):
                # The name was given as a list. Weird, but let's roll with it.
                name = ' '.join(name)
            (given, family) = split_name(name)
        if family or given:
            person = {'family_name': flattened_name(family),
                      'given_name': flattened_name(given),
                      'type': 'personal'}
        else:
            # We failed to get separate names. Currently there's some ambiguity
            # in the InvenioRDM docs about whether "name" alone is
            # allowed. Since we can't do anything else here anyway, we return
            # it this way, hoping that it'll be correct in the future.
            person = {'name': flattened_name(name),
                      'type': 'personal'}

        if _id := detected_id(data.get('@id', '')):
            id_type = recognized_scheme(_id)
            if id_type in ['orcid', 'isni', 'gnd', 'ror']:
                person.update({'identifiers': [{'identifier': _id,
                                                'scheme': id_type}]})
    else:
        org = {'name': flattened_name(data.get('name', '')),
               'type': 'organizational'}
    structure = {'person_or_org': person or org}

    if affiliation := data.get('affiliation', ''):
        if isinstance(affiliation, str):
            name = affiliation
        elif isinstance(affiliation, dict):
            # In CFF, the field name is 'legalName'. In codemeta, it's 'name'.
            name = affiliation.get('legalName', '') or affiliation.get('name', '')
        else:
            name = affiliation
        structure.update({'affiliations': [{'name': flattened_name(name)}]})
    if role:
        structure['role'] = role
    return structure


def _release_author(release):
    # We can call GitHub's user data API, but it returns very little info
    # about a user (e.g.,, it gives a name but that name is not broken out
    # into family & given name), plus sometimes fields are empty.
    account = github_account(release.author.login)
    return _identity_from_github(account) if account.name else None


def _repo_owner(repo):
    account = github_account(repo.owner.login)
    if account.type == 'Organization':
        return {'name': account.name,
                'type': 'organizational'}
    elif account.name:
        return _identity_from_github(account)
    else:
        return {}


def _identity_from_github(account):
    (given, family) = split_name(account.name)
    person = {'given_name': given,
              'family_name': family,
              'type': 'personal'}
    if account.company:
        person.update({'affiliations': [{'name': account.company}]})
    return person


def _funder_info(data):
    funder_name = data.get('name', '') or data.get('@name', '')
    funder_id = ''
    if recognized_scheme(data.get('@id', '')) == 'ror':
        funder_id = detected_id(data.get('@id', ''))
    return (funder_name, funder_id)


def _funding(funder_name, funder_id, award_name=None, award_id=None):
    # InvenioRDM says funder subfield must have id OR name, and award subfield
    # must have either id or both title and number.
    result = {}

    if funder_name:
        result['funder'] = {'name': funder_name}
    elif funder_id:
        result['funder'] = {'id': funder_id}

    if award_name:
        result['award'] = {'title': {'en': award_name}}
    elif award_id:
        result['award'] = {'id': award_id}

    return result


def _codemeta_references(repo):
    # Codemeta's referencePublication is supposed to be a ScholarlyArticle
    # (dict), but people often make it a list, and moreover, sometimes they
    # make it a list of strings (often URLs) instead of dicts.
    identifiers = set()
    for item in listified(repo.codemeta.get('referencePublication', [])):
        if isinstance(item, str):
            if recognized_scheme(item):
                identifiers.add(detected_id(item))
            else:
                log('unrecognized scheme in item: ' + str(item))
        elif isinstance(item, dict):
            for field in ['id', '@id', 'identifier', '@identifier']:
                if field not in item:
                    continue
                id_field = item[field]
                if recognized_scheme(id_field):
                    identifiers.add(detected_id(id_field))
        else:
            log('unrecognized referencePublication format: ' + str(item))
    return identifiers


def _cff_references(repo):
    # CFF has "preferred-citation" and "references". The former is one CFF
    # "reference" type object, while the latter is a list of those objects.
    # Annoyingly, a "reference" object itself can have a list of identifiers.
    identifiers = set()
    for ref in (listified(repo.cff.get('preferred-citation', []))
                + repo.cff.get('references', [])):
        # These are the relevant field names defined in codemeta & CFF.
        for field in ['doi', 'pmcid', 'isbn']:
            if value := ref.get(field, ''):
                identifiers.add(value)
                break
        else:
            for item in ref.get('identifiers', []):
                item_type = item.get('type', '')
                if item_type == 'doi':
                    identifiers.add(item['doi'])
                elif item_type == 'other':
                    value = ref.get('value', '')
                    if value and recognized_scheme(value):
                        identifiers.add(detected_id(value))
            # Tempting to look in the "url" field if none of the other id
            # fields are present. However, people sometimes set "url" to
            # values that aren't the actual reference => can't trust it.
    return identifiers


def _load_vocabularies():
    from caltechdata_api.customize_schema import get_vocabularies
    for vocab_id, vocab in get_vocabularies().items():
        CV.update({CV_NAMES[vocab_id]: vocab})


def _cv_match(vocab, term):
    from stringdist import levenshtein
    if not term:
        return None
    for entry in CV[vocab]:
        entry_title = entry['title']['en']
        distance = levenshtein(entry_title, term)
        if distance < 2:
            return entry['id']
    return None
