# =============================================================================
# @file    test_reference.py
# @brief   Py.test cases for parts of reference.py
# @created 2023-03-02
# @license Please see the file named LICENSE in the project directory
# @website https://github.com/caltechlibrary/iga
# =============================================================================

from iga.reference import (
    reference,
    reference_from_bibtex,
    reference_from_doi,
)


_BIBTEX_TESTS = [
    ('''@inproceedings{Myers2017briefb,
    title = {A brief history of {COMBINE}},
    doi = {10.1109/WSC.2017.8247840},
    booktitle = {2017 {Winter} {Simulation} {Conference} ({WSC})},
    author = {Myers, C. J. and Bader, G. and Gleeson, P. and Golebiewski, M. and Hucka, M. and Nov{\\`e}re, N. Le and Nickerson, D. P. and Schreiber, F. and Waltemath, D.},
    month = dec,
    year = {2017},
    pages = {884--895},
    }''', '''Myers, C. J., Bader, G., Gleeson, P., Golebiewski, M., Hucka, M., Novère, N. L., Nickerson, D. P., Schreiber, F., & Waltemath, D. (2017, December). A brief history of COMBINE. 2017 Winter Simulation Conference (WSC) (pp. 884–895). doi:10.1109/WSC.2017.8247840'''),

    ('''@article{bornstein2008libsbml,
    title={{L}ib{SBML}: an {API} library for {SBML}},
    author={Bornstein, Benjamin J and Keating, Sarah M and Jouraku, Akiya and Hucka, Michael},
    journal={Bioinformatics},
    volume={24},
    number={6},
    pages={880--881},
    year={2008},
    doi = {10.1093/bioinformatics/btn051},
    publisher={Oxford University Press}
    }''', '''Bornstein, B. J., Keating, S. M., Jouraku, A., & Hucka, M. (2008). LibSBML: an API library for SBML. Bioinformatics, 24(6), 880–881. doi:10.1093/bioinformatics/btn051'''),

    ('''@article{courtot2011controlled,
    author = {Courtot, M\\'{e}lanie  and Juty, Nick J. and Kn\\"{u}pfer, Christian  and Waltemath, Dagmar  and Zhukova, Anna  and Dr\\"{a}ger, Andreas  and Dumontier, Michel  and Finney, Andrew  and Golebiewski, Martin  and Hastings, Janna  and Hoops, Stefan  and Keating, Sarah  and Kell, Douglas B.  and Kerrien, Samuel  and Lawson, James  and Lister, Allyson  and Lu, James  and Machne, Rainer  and Mendes, Pedro  and Pocock, Matthew  and Rodriguez, Nicolas  and Villeger, Alice J. and Wilkinson, Darren J.  and Wimalaratne, Sarala  and Laibe, Camille  and Hucka, Michael  and Le Nov\\`{e}re, Nicolas},
    title = {Controlled vocabularies and semantics in systems biology},
    journal = {Molecular Systems Biology},
    volume = {7},
    number = {543},
    pages = {1},
    month = oct,
    year = {2011},
    doi = {10.1038/msb.2011.77},
    }''', '''Courtot, M., Juty, N. J., Knüpfer, C., Waltemath, D., Zhukova, A., Dräger, A., Dumontier, M., Finney, A., Golebiewski, M., Hastings, J., Hoops, S., Keating, S., Kell, D. B., Kerrien, S., Lawson, J., Lister, A., Lu, J., Machne, R., Mendes, P., Pocock, M., et al. (2011, October). Controlled vocabularies and semantics in systems biology. Molecular Systems Biology, 7(543), 1. doi:10.1038/msb.2011.77'''),

    ('''@article{Draeger2009b,
    author = {Dr\\"ager, Andreas and Planatscher, Hannes and Wouamba, Dieudonn{\\'e}
    Motsou and Schr\\"oder, Adrian and Hucka, Michael and Endler, Lukas
    and Golebiewski, Martin and M\\"uller, Wolfgang and Zell, Andreas},
    title = {{SBML2LaTeX: Conversion of SBML files into human-readable reports}},
    journal = {Bioinformatics},
    year = {2009},
    volume = {25},
    pages = {1455--1456},
    number = {11},
    month = apr,
    doi = {10.1093/bioinformatics/btp170},
    pdf = {http://bioinformatics.oxfordjournals.org/cgi/reprint/25/11/1455.pdf},
    }''', '''Dräger, A., Planatscher, H., Wouamba, D. M., Schröder, A., Hucka, M., Endler, L., Golebiewski, M., Müller, W., & Zell, A. (2009, April). SBML2LaTeX: Conversion of SBML files into human-readable reports. Bioinformatics, 25(11), 1455–1456. doi:10.1093/bioinformatics/btp170'''),

    ('''@book{Klipp:SystemsBiologyATextbook:2011,
    title={Systems biology: a textbook},
    author={Klipp, Edda and Liebermeister, Wolfram and Wierling, Christoph and Kowald, Axel and Herwig, Ralf},
    year={2016},
    publisher={John Wiley \\& Sons}
    }''', '''Klipp, E., Liebermeister, W., Wierling, C., Kowald, A., & Herwig, R. (2016). Systems biology: a textbook. John Wiley & Sons.'''),

    ('''@incollection{chaouiya2012logical,
    title={Logical modelling of gene regulatory networks with {GINsim}},
    author={Chaouiya, Claudine and Naldi, Aur\\'{e}lien and Thieffry, Denis},
    booktitle={Bacterial Molecular Networks},
    pages={463--479},
    year={2012},
    publisher={Springer}
    }''', '''Chaouiya, C., Naldi, A., & Thieffry, D. (2012). Logical modelling of gene regulatory networks with GINsim. Bacterial Molecular Networks (pp. 463–479). Springer.'''),

    ('''@techreport{Watanabe2018dynamic,
    author = {Watanabe, Leandro H. and K{\\"o}nig, Matthias and Myers, Chris J.},
    title = {Dynamic Flux Balance Analysis Models in SBML},
    year = {2018},
    doi = {10.1101/245076},
    institution = {Cold Spring Harbor Laboratory},
    URL = {https://www.biorxiv.org/content/early/2018/01/08/245076},
    eprint = {https://www.biorxiv.org/content/early/2018/01/08/245076.full.pdf},
    journal = {bioRxiv}
    }''', '''Watanabe, L. H., König, M., & Myers, C. J. (2018). Dynamic Flux Balance Analysis Models in SBML. Cold Spring Harbor Laboratory.'''),
]


def test_reference_from_bibtex():
    for bibtex, formatted in _BIBTEX_TESTS:
        assert reference_from_bibtex(bibtex) == formatted


def test_reference():
    assert reference('PMC4908318') == 'Gómez, H. F., Hucka, M., Keating, S. M., Nudelman, G., Iber, D., & Sealfon, S. C. (2016). MOCCASIN: converting MATLAB ODE models to SBML. Bioinformatics, 32(12), 1905–1906. https://doi.org/10.1093/bioinformatics/btw056'
    assert reference('978-1848162204') == 'Bolouri, H. (2008). Computational Modeling Of Gene Regulatory Networks - A Primer. Imperial College Press.'
