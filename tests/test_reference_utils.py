from iga.reference_utils import *
from sidetrack import set_debug


set_debug(True, '/tmp/debug.log')


def test_clean_text():
    assert clean_text('foo <i>bar</i>') == 'foo bar'
    assert clean_text('Sjoberg, D., D., Whiting, K., Curry, M., Lavery, J., A., & Larmarange, J. (2021). Reproducible Summary Tables with the gtsummary Package. The R Journal, 13(1), 570. https://doi.org/10.32614/rj-2021-053\n') == 'Sjoberg, D., D., Whiting, K., Curry, M., Lavery, J., A., & Larmarange, J. (2021). Reproducible Summary Tables with the gtsummary Package. The R Journal, 13(1), 570. https://doi.org/10.32614/rj-2021-053'


def test_doi_from_pubmed():
    assert doi_from_pubmed('PMC4908318', 'pmcid') == '10.1093/bioinformatics/btw056'
    assert doi_from_pubmed('34674411', 'pmid') == '10.1515/jib-2021-0026'


def test_doi_for_publication():
    assert doi_for_publication('10.1093/bioinformatics/btw056', 'doi') == '10.1093/bioinformatics/btw056'
    assert doi_for_publication('arXiv:2012.13117v1', 'arxiv') == '10.48550/arXiv.2012.13117v1'
    assert doi_for_publication('arXiv:2012.13117v1') == '10.48550/arXiv.2012.13117v1'
    assert doi_for_publication('PMC4908318') == '10.1093/bioinformatics/btw056'


def test_reference():
    assert reference('PMC4908318') == 'Gómez, H. F., Hucka, M., Keating, S. M., Nudelman, G., Iber, D., & Sealfon, S. C. (2016). MOCCASIN: converting MATLAB ODE models to SBML. Bioinformatics, 32(12), 1905–1906. https://doi.org/10.1093/bioinformatics/btw056'
    assert reference('978-1848162204') == 'Bolouri, H. (2008). Computational Modeling Of Gene Regulatory Networks - A Primer. Imperial College Press.'
