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

from iga.exceptions import InternalError
from iga.github import (
    github_release,
    github_release_url,
    github_repo,
    github_repo_file,
    github_repo_filenames,
    github_file_url
)


# Constants.
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# InvenioRDM schema info: https://inveniordm.docs.cern.ch/reference/metadata/.
# A record can have these top-level fields (but might not contain all):
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
# The minimum for a record sent to InvenioRDM is the "metadata" field. The
# following is the full set of subfields in "metadata".

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

# A number of these fields are created by InvenioRDM itself; a user doesn't
# put them in a record sent to InvenioRDM.  Based on the test cases in the repo
# https://github.com/inveniosoftware/invenio-rdm-records, the min fields are:
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


# Exported module functions.
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def valid_record(json_dict):
    '''Perform basic validation on the given JSON record for InvenioRDM.'''

    # The validation process currently on tests that the record has the
    # minimum fields; it does not check the field values.
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


def record_from_release(account, repo, tag):
    '''Return InvenioRDM record created from the account/repo/tag release.'''
    release_url = github_release_url(account, repo, tag)
    release = github_release(release_url)
    repo = github_repo(account, repo)

    # We use codemeta.json & CITATION.cff often. Get them now & add as property.
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
        from cffconvert.citation import Citation
        file_url = github_file_url(repo, cff_filename)
        contents = github_repo_file(repo, cff_filename)
        cff_object = Citation(contents, src=file_url)
        repo.cff = json5.loads(cff_object.as_schemaorg())

    # Make the metadata dict by iterating over the names in FIELDS and calling
    # the function of that name defined in this (module) file.
    module = sys.modules[__name__]
    metadata = dict((f, getattr(module, f)(repo, release)) for f in FIELDS)
    return {"metadata": metadata}


# Field value functions.
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Summary of the approach: the functions for extracting values from GitHub
# are named after the fields themselves, so that record_from_release(...)
# above can create a record by simply iterating over the names in FIELDS and
# calling the function of that name to get the value for that field.

def additional_descriptions(repo, release):
    descriptions = []
    # The codemeta and CFF descriptions tend to be better and longer than
    # what people write in GitHub repo descriptions, so use that if possible.
    # It doesn't seem useful to put both one of these *and* the GitHub repo
    # description; that's why the conditional below is an if-else.
    text = repo.codemeta.get('description', None) or repo.cff.get('description', None)
    if text:
        descriptions.append({'description': text,
                             'type': {'id': 'other', 'title': {'en': 'Other'}}})
    elif repo.description:
        descriptions.append({'description': repo.description,
                             'type': {'id': 'other', 'title': {'en': 'Other'}}})
    return descriptions


def additional_titles(repo, release):
    return []


def contributors(repo, release):
    if repo.codemeta.get('contributor', []):
        return [_person(x) for x in repo.codemeta.get('contributor', [])]
    if repo.cff.get('contributors', []):
        return [_person(x) for x in repo.cff.get('contributors', [])]
    return []


def creators(repo, release):
    # Codemeta & CITATION.cff files contain more complete author info than the
    # GitHub release data, so try them 1st.
    if repo.codemeta:
        return [_person(x) for x in repo.codemeta.get('author', [])]
    elif repo.cff:
        return [_person(x) for x in repo.cff.get('author', [])]
    else:
        # We can call GitHub's user data API, but it returns very little info
        # about a user (e.g.,, it gives a name but that name is not broken out
        # into family & given name.
        breakpoint()


def dates(repo, release):
    created_date = arrow.get(release.created_at)
    return [{'date': created_date.format('YYYY-MM-DD'),
             'type': {'id': 'created', 'title': {'en': 'Created'}}}]


def description(repo, release):
    return release.body.strip()


def formats(repo, release):
    # fixme
    return []


def funding(repo, release):
    return []


def identifiers(repo, release):
    return []


def languages(repo, release):
    # GitHub doesn't provide a way to deal with any other human language.
    return [{"id": "eng"}]


def locations(repo, release):
    return []


def publication_date(repo, release):
    return arrow.get(release.published_at).format('YYYY-MM-DD')


def publisher(repo, release):
    return 'CaltechDATA'


def references(repo, release):
    # FIXME some people put paper citation info in CITATION.cff
    # See eg https://github.com/plasma-umass/scalene
    return []


def related_identifiers(repo, release):
    return [{'identifier': release.html_url,
             'relation_type': {'id': 'isidenticalto',
                               'title': {'en': 'Is identical to'}},
             'scheme': 'url'}]


def resource_type(repo, release):
    # InvenioRDM requires that the resource_type id comes from a CV. We only
    # recognize specific types, so we hardwire the values here.

    # FIXME handle other types like datasets
    return {'id': 'software', 'title': {'en': 'Software'}}


def rights(repo, release):
    if repo.license and repo.license.name != 'Other':
        spdx_id = repo.license.spdx_id
        rights = [{'id': spdx_id,
                   'link': repo.license.url,
                   'title': {'en': repo.license.name}}]
        from iga.licenses import LICENSE_DESCRIPTIONS
        if spdx_id in LICENSE_DESCRIPTIONS:
            rights[0].update({'description': {'en': LICENSE_DESCRIPTIONS[spdx_id]}})
        return rights

    # GitHub didn't fill in the license info -- maybe it didn't recognize
    # the license or its format. Try to look for a license file ourselves.
    filenames = github_repo_filenames(repo)
    base_url = 'https://github.com/' + repo.owner.login + '/' + repo.name
    # The FSF guide on how to use the GPL suggests COPYING. The Producing
    # Open Source Software book suggests either COPYING or LICENSE.
    for basename in ['LICENSE', 'License', 'license', 'COPYING',
                     'COPYRIGHT', 'Copyright', 'copyright']:
        for ext in ['', '.txt', '.md', '.html']:
            if basename + ext in filenames:
                # There's no safe way to summarize arbitrary license
                # text, so we can't provide 'description' field value.
                return [{'title': {'en': 'License'},
                         'link': base_url + '/' + basename + ext}]

    # We didn't find a license file. Try codemeta.json & CITATION.cff.
    value = repo.codemeta.get('license', None) or repo.cff.get('license', None)
    if value:
        if 'http' in value:
            return [{'title': {'en': 'License'},
                     'link': value}]
        else:
            # Not a URL. Assume it's a license name.
            return [{'title': {'en': value}}],

    # We didn't find anything usable.
    return []


def sizes(repo, release):
    # fixme
    return []


def subjects(repo, release):
    return [{'subject': x} for x in repo.topics if x.lower() != 'github']


def title(repo, release):
    return repo.full_name + ': ' + release.name


def version(repo, release):
    return release.tag_name


# Miscellaneous helper functions.
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def _person(person_dict):
    # See https://inveniordm.docs.cern.ch/reference/metadata/#creators-1-n
    # Although people sometimes put more things in the CITATION.cff authors
    # info (e.g., email addr), there's no provision in InvenioRDM for that.
    person = {'family_name': person_dict['familyName'],
              'given_name': person_dict['givenName'],
              'type': 'personal'}
    if 'orcid' in person_dict.get('@id', ''):
        orcid = person_dict['@id'].split('/')[-1]
        person.update({'identifiers': [{'scheme': 'orcid',
                                        'identifier': orcid}]})
    if 'affiliation' in person_dict:
        if isinstance(person_dict['affiliation'], dict):
            affiliation = person_dict['affiliation']['legalName']
        else:
            affiliation = person_dict['affiliation']
        person.update({'affiliations': [{'name': affiliation}]})
    return person
