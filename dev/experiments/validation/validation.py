from os import path
from iga.exceptions import InternalError

_SCHEMA_PATH = path.join(path.dirname(__file__), 'data/datacite_4.3_schema.json')

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

