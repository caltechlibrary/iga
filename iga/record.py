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
    github_release_url,
    github_repo,
    github_repo_file,
    github_repo_filenames,
    github_file_url,
    github_user
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
    # The codemeta and CITATION.cff descriptions tend to be better than what
    # people put in GitHub repo descriptions, so try them 1st. An argument
    # could be made to use both one of the codemeta/cff descriptions *and* the
    # github repo description, as two additional descriptions, but the repo
    # descriptions rarely seem to add anything beyond the codemeta/cff ones.
    text = (repo.codemeta.get('description', None)
            or repo.cff.get('description', None)
            or repo.description)
    if text:
        return [{'description': text,
                 'type': {'id': 'other', 'title': {'en': 'Other'}}}]
    else:
        return []


def additional_titles(repo, release):
    return []


def contributors(repo, release):
    clist = repo.codemeta.get('contributor', []) or repo.cff.get('contributors', [])
    return [_person(x) for x in clist]


def creators(repo, release):
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
    created_date = arrow.get(release.created_at)
    return [{'date': created_date.format('YYYY-MM-DD'),
             'type': {'id': 'created', 'title': {'en': 'Created'}}}]


def description(repo, release):
    return release.body.strip() if release.body else ''


def formats(repo, release):
    # fixme
    return []


def funding(repo, release):
    return []


def identifiers(repo, release):
    return []


def languages(repo, release):
    # GitHub doesn't provide a way to deal with any other human language.
    return [{"id": "eng", 'title': {'en': 'English'}}]


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
             'resource_type': {'id': 'software', 'title': {'en': 'Software'}},
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
    return repo.full_name + ': ' + (release.name or release.tag_name)


def version(repo, release):
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

def _person(person_dict):
    # Although people sometimes put more things in the CITATION.cff authors
    # info (e.g., email addr), there's no provision in InvenioRDM for that.
    person = {'family_name': person_dict['familyName'],
              'given_name': person_dict['givenName'],
              'type': 'personal'}
    if 'orcid' in person_dict.get('@id', ''):
        orcid = person_dict['@id'].split('/')[-1]
        person.update({'identifiers': [{'scheme': 'orcid',
                                        'identifier': orcid}]})

    structure = {'person_or_org': person}
    if 'affiliation' in person_dict:
        if isinstance(person_dict['affiliation'], dict):
            affiliation = person_dict['affiliation']['legalName']
        else:
            affiliation = person_dict['affiliation']
        structure.update({'affiliations': [{'name': affiliation}]})
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
        return ('', name)
    try:
        log('trying to split name using probablepeople')
        import probablepeople as pp
        from_pp = pp.tag(name)
        # PP gets better results if you DON'T supply the 'type' parameter. (I
        # don't know why.) So, we use that 1st, unless it guesses wrong about
        # the type, in which case, we run it again using type=person.
        if from_pp[1] != 'Person':
            from_pp = pp.tag(_cleaned_name(name), type='person')
        parsed = from_pp[0]
        # If it found initials instead of full names, use those.
        if parsed.get('FirstInitial', ''):
            given = parsed.get('FirstInitial')
        else:
            given = parsed.get('GivenName', '')

        # For some reason, it seems the InvenioRDM records include the middle
        # names as part of the first/given names.
        if parsed.get('MiddleInitial', ''):
            given += (' ' + parsed.get('MiddleInitial'))
        elif parsed.get('MiddleName', ''):
            given += (' ' + parsed.get('MiddleName'))

        if parsed.get('LastInitial', '') and not parsed.get('Surname', ''):
            surname = parsed.get('LastInitial')
        else:
            surname = parsed.get('Surname', '')

        return (given, surname)
    except Exception:                   # noqa: PIE786
        log(f'switching to nameparser after probablepeople faulted on "{name}"')
        from nameparser import HumanName
        parsed = HumanName(name)
        return (parsed.first + ' ' + parsed.middle, parsed.last)


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
    # Normalize spaces.
    name = re.sub(r' +', ' ', name)
    return name.strip()                 # noqa PIE781

