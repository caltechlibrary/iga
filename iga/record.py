'''
record.py: record structure creation & manipulation

This file is part of https://github.com/caltechlibrary/iga/.

Copyright (c) 2022 by the California Institute of Technology.  This code
is open-source software released under a BSD-type license.  Please see the
file "LICENSE" for more information.
'''

import arrow
import copy
from   sidetrack import log
from   os import path

from iga.exceptions import InternalError
from iga.github import github_release, github_repo, github_repo_files


# Internal constants.
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

_SCHEMA_PATH = path.join(path.dirname(__file__), 'data/datacite_4.3_schema.json')


# Principal exported functions.
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def valid_record(record):
    '''Return True if the given record is valid.'''
    import json
    import jsonschema

    # Step 1: do basic JSON validation.
    try:
        record_json = json.loads(record)
    except json.decoder.JSONDecodeError as ex:
        log('given record failed to load using Python json library: ' + str(ex))
        return False

    # Step 2: validate against DataCite JSON schema.
    try:
        with open(_SCHEMA_PATH, 'r') as schema_file:
            datacite_schema = schema_file.read()
        schema_json = json.loads(datacite_schema)
        jsonschema.validate(instance=record_json, schema=schema_json)
    except OSError as ex:
        raise InternalError('Unable to read internal JSON schema: ' + str(ex))
    except json.decoder.JSONDecodeError as ex:
        raise InternalError('Internal JSON schema is corrupted: ' + str(ex))
    except jsonschema.exceptions.ValidationError as ex:
        log('given record failed schema validation: ' + str(ex))
        return False
    return True


def record_from_release(account, repo, tag):
    release_url = github_release_url(account, repo, tag)
    release = github_release(release_url)
    repo = github_repo(account, repo)
    record = copy.deepcopy(_RECORD_TEMPLATE)
    for key, value in record.items():
        if callable(value):
            record[key] = value(repo, release)
    breakpoint()
    return record


def github_release_url(account, repo, tag):
    return 'https://api.github.com/repos/'+account+'/'+repo+'/releases/tags/'+tag


# Helper functions.
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def type_extractor(repo, release):
    # FIXME: handle repos that are not software
    return {"resourceTypeGeneral": "Software", "resourceType": "Software"}


def titles_extractor(repo, release):
    return [{'title': repo.name + ': ' + release.name}]


def descriptions_extractor(repo, release):
    return [{'descriptions': release.body}]


def version_extractor(repo, release):
    return release.tag_name


def dates_extractor(repo, release):
    created_date = arrow.get(release.created_at).format('YYYY-MM-DD')
    issued_date = arrow.get(release.published_at).format('YYYY-MM-DD')
    return [
        {'dateType': 'Created', 'date': created_date},
        {'dateType': 'Issued', 'date': issued_date},
    ]


def creators_extractor(repo, release):
    return []


def contributors_extractor(repo, release):
    return []


def pubyear_extractor(repo, release):
    date = arrow.get(release.published_at)
    return str(date.year)


def subjects_extractor(repo, release):
    return [{'subject': x} for x in repo.topics] if repo.topics else []


def identifiers_extractor(repo, release):
    return []


def related_identifiers_extractor(repo, release):
    return []


def sizes_extractor(repo, release):
    return ''


def formats_extractor(repo, release):
    return ''


def rightslist_extractor(repo, release):
    if repo.license.name != 'Other':
        return [{'rights': 'license',
                 'rightsUri': repo.license.url,
                 'rightsIdentifierScheme': 'SPDX',
                 'rightsIdentifier': repo.license.spdx_id,
                 'schemeUri': 'https://spdx.org/licenses/'}]
    else:
        # GitHub didn't fill in the license field because it didn't recognize
        # what's there. Try to find a recognizable license file anyway.
        files = github_repo_files(repo)
        names = [file.path for file in files]
        base_url = 'https://github.com/' + repo.owner.login + '/' + repo.name
        for ext in ['', '.txt', '.md', '.html']:
            for basename in ['LICENSE', 'license', 'License']:
                if basename + ext in names:
                    return [{'rights': 'license',
                             'rightsUri': base_url + '/' + basename + ext}]
        else:
            return []


def funding_extractor(repo, release):
    return []


_RECORD_TEMPLATE = {
    "schemaVersion"      : "http://datacite.org/schema/kernel-4",
    "types"              : type_extractor,
    "titles"             : titles_extractor,
    "descriptions"       : descriptions_extractor,
    "version"            : version_extractor,
    "dates"              : dates_extractor,
    "creators"           : creators_extractor,
    "contributors"       : contributors_extractor,
    "publisher"          : "CaltechDATA",
    "publicationYear"    : pubyear_extractor,
    "subjects"           : subjects_extractor,
    "identifiers"        : identifiers_extractor,
    "relatedIdentifiers" : related_identifiers_extractor,
    "sizes"              : sizes_extractor,
    "formats"            : formats_extractor,
    "rightsList"         : rightslist_extractor,
    "fundingReferences"  : funding_extractor,
    "geoLocations"       : [],
    "language"           : "en",
}
