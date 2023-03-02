import json5
from   os import path
from   sidetrack import log
from   unittest import mock

from iga.orcid import name_from_orcid


# Mocks
# .............................................................................

here      = path.dirname(path.abspath(__file__))
orcid_dir = path.join(here, 'data/orcid-examples/')


def mocked_orcid_data(orcid):
    log(f'returing mocked ORCID data for {orcid}')
    orcid_filename = orcid + '.json'
    with open(path.join(orcid_dir, orcid_filename), 'r') as f:
        return json5.load(f)


# Tests
# .............................................................................

@mock.patch('iga.orcid.orcid_data', new=mocked_orcid_data)
def test_name_from_orcid():
    assert name_from_orcid('0000-0001-9105-5960') == ('Michael', 'Hucka')
    assert name_from_orcid('https://orcid.org/0000-0003-0900-6903') == ('R. S.', 'Doiel')
    assert name_from_orcid('https://orcid.org/0000-0002-8876-7606') == ('Neil P.', 'Chue Hong')
    assert name_from_orcid('https://orcid.org/0000-0001-6151-2200') == ('', '')
