from iga.ror import name_from_ror


def test_name_from_ror():
    assert name_from_ror('https://ror.org/05dxps055') == 'California Institute of Technology'
    assert name_from_ror('05dxps055') == 'California Institute of Technology'
    assert name_from_ror('https://ror.org/03ybx0x41') == 'University of Basel'
