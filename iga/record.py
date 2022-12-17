'''
record.py: record structure creation & manipulation

This file is part of https://github.com/caltechlibrary/iga/.

Copyright (c) 2022 by the California Institute of Technology.  This code
is open-source software released under a BSD-type license.  Please see the
file "LICENSE" for more information.
'''

_RECORD_TEMPLATE = {
    "schemaVersion"      : "http://datacite.org/schema/kernel-4",
    "types"              : type_extractor,
    "titles"             : titles_extractor,
    "descriptions"       : descriptions_extractor,
    "version"            : version_extractor,
    "dates"              : dates_extractor,
    "creators"           : creators_extractor,
    "contributors"       : contributors_extractor,
    "publisher"          : "GitHub",
    "publicationYear"    : year_extractor,
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

def record_for_release(github_release):
    import copy
    record = copy.deepcopy(_RECORD_TEMPLATE)
    for key, value in record.items():
        if callable(value):
            record[key] = value(github_release)
    return record
