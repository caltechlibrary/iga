from iga.orcid import name_from_orcid


def test_name_from_orcid():
    assert name_from_orcid('https://orcid.org/0000-0002-8876-7606') == ('Neil P.', 'Chue Hong')
    assert name_from_orcid('0000-0001-9105-5960') == ('Michael', 'Hucka')
    assert name_from_orcid('0000-0002-2746-5647') == ('Jessica A.', 'Lavery')
    assert name_from_orcid('https://orcid.org/0000-0003-0900-6903') == ('R. S.', 'Doiel')
