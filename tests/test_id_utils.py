# =============================================================================
# @file    test_id_utils.py
# @brief   Py.test cases for parts of id_utils.py
# @created 2023-03-02
# @license Please see the file named LICENSE in the project directory
# @website https://github.com/caltechlibrary/iga
# =============================================================================

from iga.id_utils import (
    contains_pmcid,
    detected_id,
    normalize_pmcid,
    recognized_scheme,
    is_invenio_rdm,
)

sample_ids = [
    ('arXiv:2012.13117v1'                                 , 'arxiv'),
    ('10.48550/arXiv.2012.13117'                          , 'doi'),
    ('PMC4908318'                                         , 'pmcid'),
    ('26861819'                                           , 'pmid'),
    ('18183754'                                           , 'pmid'),
    ('10.1093/bioinformatics/btw056'                      , 'doi'),
    ('10.1007/978-1-4939-3283-2_19'                       , 'doi'),
    ('10.1103/PhysRevD.90.124021'                         , 'doi'),
    ('26677194'                                           , 'pmid'),
    ('978-0982477373'                                     , 'isbn'),
    ('9780898714128'                                      , 'isbn'),
    ('9781979381208'                                      , 'isbn'),
    ('978-65-87773-12-4'                                  , 'isbn'),
    ('04dkp9463'                                          , 'ror'),
    ('swh:1:cnt:94a9ed024d3859793618152ea559a168bbcbb5e2' , 'swh'),
    ('bknz4-bch35'                                        , 'rdm'),
    ('ry4vm-wny44'                                        , 'rdm'),
    ('https://a.b/records/ry4vm-wny44'                    , 'rdm'),
    ('https://a.b/records/jx193-a0e45?preview=1'          , 'rdm'),
    ('https://a.b/uploads/ry4vm-wny44'                    , 'rdm'),
    ('https://a.b/something/ry4vm-wny44'                  , 'url'),
]


def test_contains_pmcid():
    for _id, scheme in sample_ids:
        if scheme == 'pmcid':
            assert contains_pmcid(_id)


def test_normalize_pmcid():
    assert normalize_pmcid('pmc4908318') == 'PMC4908318'


def test_recognized_scheme():
    for _id, scheme in sample_ids:
        assert recognized_scheme(_id) == scheme


sample_unnormalized_ids = [
    ('http://orcid.org/0000-0001-9105-5960'      , '0000-0001-9105-5960'),
    ('https://doi.org/10.5281/zenodo.1095472'    , '10.5281/zenodo.1095472'),
    ('https://ror.org/027m9bs27'                 , '027m9bs27'),
    ('10.1088/0264-9381/26/22/225003'            , '10.1088/0264-9381/26/22/225003'),
    ('PMCID; PMC4908318'                         , ''),
    ('22110403'                                  , '22110403'),
    ('pmc4908318'                                , 'PMC4908318'),
    ('PMC3217025'                                , 'PMC3217025'),
    ('https://ror.org/04dkp9463'                 , '04dkp9463'),
    ('https://a.b/records/ry4vm-wny44'           , 'ry4vm-wny44'),
    ('https://a.b/records/ry4vm-wny44?preview=1' , 'ry4vm-wny44'),
    ('https://a.b/records/ry4vm-wny44/draft'     , 'ry4vm-wny44'),
    ('https://a.b/uploads/ry4vm-wny44'           , 'ry4vm-wny44'),
    # If it's not detected as an RDM record id   , it's considered to be just a URL.
    ('https://a.b/something/ry4vm-wny44'         , 'https://a.b/something/ry4vm-wny44'),
]


def test_detected_id():
    for text, id_ in sample_unnormalized_ids:
        assert detected_id(text) == id_


def test_is_invenio_rdm():
    assert is_invenio_rdm('https://a.b/records/ry4vm-wny44')
    assert not is_invenio_rdm('https://a.b/something/ry4vm-wny44')
