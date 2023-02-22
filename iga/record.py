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
from   commonpy.data_structures import CaseFoldSet
import json5
from   sidetrack import log
import sys

from iga.data_utils import deduplicated, similar_urls, listified, cleaned_text
from iga.exceptions import MissingData
from iga.github import (
    github_account,
    github_release,
    github_repo,
    github_repo_file,
    github_repo_filenames,
    github_repo_languages,
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
    # Description types come from DataCite, and can be: "abstract", "methods",
    # "series-information", "table-of-contents", "technical-info", "other".

    descriptions = []

    # We don't want to reuse the text that we put in the InvenioRDM description
    # field, hence the need for the logic that follows.
    desc = description(repo, release)

    # Add the release notes if we didn't use that as the main description.
    rel_notes = repo.codemeta.get('releaseNotes', '').strip()
    if rel_notes != desc and not rel_notes.startswith('http'):
        descriptions.append({'description': rel_notes,
                             'type': {'id': 'other',
                                      'title': {'en': 'Other'}}})

    # Add one of Codemeta's "description", CFF's "abstract", or the GitHub repo
    # description if we didn't that as the main description. These are listed
    # as equivalent by the Codemeta crosswalk. If more than one is set, it's
    # likely that they're all similar anyway, so add only one of them.
    #
    # Note #1: we could use a string distance measure (e.g., Levenshtein) to
    # evaluate the values really are different and add them individually if
    # they are not too similar. However, finding a threshold that works for all
    # cases would be difficult if not impossible, and it would still risk that
    # the values essentially say the same thing using different words. There
    # seems to be little value in adding all 3, especially since they describe
    # the software as a whole and not the release per se. Adding one is enough.
    #
    # Note #2: the fact that DataCite offers a description type of "abstract"
    # makes it tempting to use that for the CFF "abstract" field, but IMHO that
    # would be wrong because CFF's definition of "abstract" is that it's "a
    # description of the software or dataset" -- in other words, the same kind
    # of text as the other fields. Thus, we should use the same type value.
    text = (repo.codemeta.get('description', '')
            or repo.cff.get('abstract', '')
            or repo.description)
    text = text.strip()
    if text != desc:
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
        contributors.append(_entity(contact, role='contactperson'))

    # Codemeta's "maintainer" is a person, but people often use a list here.
    # InvenioRDM roles lack an explicit term for maintainer, so we use "other".
    for maintainer in listified(repo.codemeta.get('maintainer', {})):
        contributors.append(_entity(maintainer, role='other'))

    # Both codemeta & cff files may have lists of contributors. Give priority
    # to codemeta. Comparing names is error-prone and we can't reliably detect
    # duplicates, so use only one or the other, not both.
    for contributor in (listified(repo.codemeta.get('contributor', []))
                        or repo.cff.get('contributors', [])):
        role = 'other'
        if matched := _cv_match('contributor-roles', contributor.get('role', '')):
            role = matched
        contributors.append(_entity(contributor, role=role))

    # FIXME if there is no contributors info, use github contributors &
    # look up peole's names using github api

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
        return deduplicated(_entity(x) for x in authors)

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

    # Codemeta's "description" & CFF's "abstract" (which the Codemeta crosswalk
    # maps as equivalent) and GitHub's repo "description" field refer to the
    # software or dataset overall, not specifically to the release. Still, if
    # there's nothing else, it seems better to use this instead of leaving an
    # empty description in the record.
    if text := (repo.codemeta.get('description', '')
                or repo.cff.get('abstract', '')
                or repo.description):
        return text.strip()

    # Bummer.
    log('could not find a description')
    return ''


def formats(repo, release):
    '''Return InvenioRDM "formats".
    https://inveniordm.docs.cern.ch/reference/metadata/#formats-0-n
    '''
    formats = []
    if release.tarball_url:
        formats.append("application/x-tar-gz")
    if release.zipball_url:
        formats.append("application/zip")
    for asset in release.assets:
        formats.append(asset.content_type)
    return formats


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
            funder_tuples.append(_parsed_funder_info(item))
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
            num_terms = len(item.split())
            award_id = item if num_terms == 1 else ''
            award_name = item if num_terms > 1 else ''
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
                    item_funder, item_funder_id = _parsed_funder_info(fun)
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

    # If releaseNotes is a URL, we will not have used it for either the
    # description or additional descriptions, so add it here.
    relnotes_url = repo.codemeta.get('releaseNotes', '').strip()
    if relnotes_url.startswith('http'):
        identifiers.append({'identifier': url_normalize(relnotes_url),
                            'relation_type': {'id': 'isdescribedby',
                                              'title': {'en': 'Is described by'}},
                            'resource_type': {'id': 'other',
                                              'title': {'en': 'Other'}},
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

    # The issues URL is kind of a supplemental resource.
    issues_url = repo.codemeta.get('issueTracker', '')
    if not issues_url and repo.issues_url:
        issues_url = f'https://github.com/{repo.full_name}/issues'
    if issues_url:
        identifiers.append({'identifier': url_normalize(issues_url),
                            'relation_type': {'id': 'issupplementedby',
                                              'title': {'en': 'Is supplemented by'}},
                            'resource_type': {'id': 'other',
                                              'title': {'en': 'Other'}},
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
    sizes = []
    # FIXME can't get size of tarball & zipball from GitHub for some reason,
    # so need to get it after downloading the files locally.
    sizes.append('unknown')
    sizes.append('unknown')
    for asset in release.assets:
        sizes.append(f'{asset.size} bytes')
    return sizes


def subjects(repo, release):
    '''Return InvenioRDM "subjects".
    https://inveniordm.docs.cern.ch/reference/metadata/#subjects-0-n
    '''
    # Start with the topics list from the GitHub repo. Use a case-insensitive
    # set to try to uniquefy the values added to this.
    subjects = CaseFoldSet(repo.topics)

    # Add values from Codemeta field "keywords". If the whole value is one
    # string, it may contain multiple terms separated by a comma or semicolon.
    keywords = repo.codemeta.get('keywords', [])
    if isinstance(keywords, str):
        # Trying the ';' first, alone, is deliberate in case the values
        # separated by semicolons have commas within them.
        if ';' in keywords:
            subjects.update(keywords.split(';'))
        elif ',' in keywords:
            subjects.update(keywords.split(','))
        else:
            subjects.update(keywords.split())
    else:
        for item in listified(keywords):
            if isinstance(item, str):
                subjects.add(item)
            else:
                log('found keywords with unrecognized format in codemeta.json')
                break

    # In CFF, people usually write lists, but I've seen mistakes. Be safe here.
    for keyword in listified(repo.cff.get('keywords', [])):
        if isinstance(item, str):
            subjects.add(item)
        else:
            log('found keywords with unrecognized format in CITATION.cff')
            break

    # Add languages as topics too.
    for lang in github_repo_languages(repo):
        subjects.add(lang)
    for item in listified(repo.codemeta.get('programmingLanguage', [])):
        if isinstance(item, str):
            subjects.add(item)
        elif isinstance(item, dict):
            if lang := (item.get('name', '') or item.get('@name', '')):
                subjects.add(lang)
        else:
            log('found programmingLanguage item with unrecognized format'
                ' in codemeta.json: ' + str(item))
            break

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

# See https://inveniordm.docs.cern.ch/reference/metadata/#creators-1-n for info
# about the fields for authors in InvenioRDM. Although people sometimes put
# more things in (e.g.) the CFF authors fields (e.g., email addr), there's no
# provision in InvenioRDM for that.

def _entity(data, role=None):
    if isinstance(data, dict):          # Correct data type.
        return _entity_from_dict(data, role)
    elif isinstance(data, str):         # Wrong data type, but we try anyway.
        return _entity_from_string(data, role)
    else:                               # If we get here, it's beyond us.
        log('entity value is neither a string nor a dict -- giving up')
        return {}


def _entity_from_string(data, role):
    # We don't expect strings for this, so everything we do here is heuristics.
    # Possibilities considered:
    #  - an ORCID URL, like "https://orcid.org/0000-0001-9105-5960"
    #  - an ORCID by itself, like "0000-0001-9105-5960"
    #  - an organization's ROR URL, like "https://ror.org/05dxps055"
    #  - an organization's ROR ID by itself, like "05dxps055"
    #  - a GitHub user's name, like "mhucka"
    #  - a GitHub org account name, like "caltechlibrary"
    #  - a person's name, like "Michael Hucka"
    #  - an organization's name, like "California Institute of Technology"

    result = {}
    scheme = recognized_scheme(data)
    if scheme == 'orcid':
        from iga.orcid import name_from_orcid
        orcid = detected_id(data)
        (given, family) = name_from_orcid(orcid)
        if family or given:
            result = {'family_name': flattened_name(family),
                      'given_name': flattened_name(given),
                      'identifiers': [{'identifier': orcid,
                                       'scheme': 'orcid'}],
                      'type': 'personal'}
    elif scheme == 'ror':
        from iga.ror import name_from_ror
        name = name_from_ror(data)
        if name:
            result = {'name': name,
                      'type': 'organizational'}
    elif data.startswith('https://github.com'):
        # Might be the URL to an account page on GitHub.
        tail = data.replace('https://github.com/', '')
        if '/' not in tail and (account := github_account(tail)):
            result = _identity_from_github(account)
        else:
            log('{data} is not interpretable as a GitHub account')
    elif len(data.split()) == 1 and (account := github_account(data)):
        # This is the name of an account in GitHub.
        result = _identity_from_github(account)
    else:
        # We're getting into expensive heuristic guesswork now.
        from iga.name_utils import is_person
        if is_person(data):
            (given, family) = split_name(data)
            if family or given:
                result = {'family_name': flattened_name(family),
                          'given_name': flattened_name(given),
                          'type': 'personal'}
            else:
                log(f'guessing "{data}" is a person but failed to split name')
        else:
            result = {'name': data,
                      'type': 'organizational'}
    if result and role:
        result['role'] = role
    return result


def _entity_from_dict(data, role):
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
    return _identity_from_github(account)


def _identity_from_github(account):
    if account.type == 'User':
        (given, family) = split_name(account.name)
        result = {'given_name': given,
                  'family_name': family,
                  'type': 'personal'}
        if account.company:
            result.update({'affiliations': [{'name': account.company}]})
    else:
        return {'name': account.name,
                'type': 'organizational'}
    return result


def _parsed_funder_info(data):
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
    identifiers = CaseFoldSet()
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
    identifiers = CaseFoldSet()
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
