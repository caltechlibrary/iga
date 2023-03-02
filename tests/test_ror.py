import json5
import os
from   os import path
from   sidetrack import log
from   unittest import mock

from iga.ror import name_from_ror


# Mocks
# .............................................................................

here    = path.dirname(path.abspath(__file__))
ror_dir = path.join(here, 'data/ror-examples/')


def mocked_ror_data(rorid):
    log(f'returing mocked ROR data for {rorid}')
    ror_filename = rorid + '.json'
    with open(path.join(ror_dir, ror_filename), 'r') as f:
        return json5.load(f)


# Tests
# .............................................................................

@mock.patch('iga.ror.ror_data', new=mocked_ror_data)
def test_name_from_ror():
    assert name_from_ror('https://ror.org/05dxps055') == 'California Institute of Technology'
    assert name_from_ror('05dxps055') == 'California Institute of Technology'
    assert name_from_ror('https://ror.org/03ybx0x41') == 'University of Basel'
