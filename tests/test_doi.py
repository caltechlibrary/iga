# =============================================================================
# @file    test_doi.py
# @brief   Py.test cases for doi.py
# @created 2022-12-08
# @license Please see the file named LICENSE in the project directory
# @website https://github.com/caltechlibrary/iga
# =============================================================================

from iga.doi import doi_for_publication, _doi_for_pubmed


# Tests
# .............................................................................

def test_doi_for_publication():
    assert doi_for_publication('') == ''
    assert doi_for_publication('10.1093/bioinformatics/btw056', 'doi') == '10.1093/bioinformatics/btw056'
    assert doi_for_publication('arXiv:2012.13117v1', 'arxiv') == '10.48550/arXiv.2012.13117v1'
    assert doi_for_publication('arXiv:2012.13117v1') == '10.48550/arXiv.2012.13117v1'
    assert doi_for_publication('PMC4908318') == '10.1093/bioinformatics/btw056'
    assert doi_for_publication('x965x9092') == ''
    assert doi_for_publication('26360422') == '10.1371/journal.pone.0137946'


def test__doi_for_pubmed():
    assert _doi_for_pubmed('PMC4908318', 'pmcid') == '10.1093/bioinformatics/btw056'
    assert _doi_for_pubmed('34674411', 'pmid') == '10.1515/jib-2021-0026'
    assert _doi_for_pubmed('001001010100101', 'pmid') == ''
    assert _doi_for_pubmed('', 'pmid') == ''
    assert _doi_for_pubmed('_', 'pmid') == ''
