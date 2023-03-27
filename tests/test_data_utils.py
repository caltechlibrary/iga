# =============================================================================
# @file    test_data_utils.py
# @brief   Py.test cases for parts of data_utils.py
# @created 2023-03-02
# @license Please see the file named LICENSE in the project directory
# @website https://github.com/caltechlibrary/iga
# =============================================================================

from typing import Generator
from iga.data_utils import (
    deduplicated,
    listified,
    similar_urls,
    normalized_url,
)


def test_deduplicated():
    assert deduplicated([]) == []
    assert deduplicated('') == []

    a = {'a': 1, 'b': 2, 'c': 3}
    assert deduplicated(a) == a
    assert deduplicated([a]) == [a]
    assert deduplicated([a, a]) == [a]

    b = {'c': 3, 'a': 1, 'b': 2}
    assert deduplicated([a, b]) == [a]

    c = {'d': {'e': {'f': 4}, 'g': 5}, 'h': 6}
    assert deduplicated([c, c]) == [c]

    d = {'d': [{'e': {'f': 4}, 'g': 5}, {'i': 7}], 'h': 6}
    assert deduplicated([d, d]) == [d]
    assert deduplicated([d, c]) == [d, c]
    assert deduplicated([d, d, a]) == [d, a]

    p = [{'person_or_org':
          {'family_name': 'Sjoberg', 'given_name': 'Daniel D.', 'type': 'personal',
           'identifiers': [{'scheme': 'orcid', 'identifier': '0000-0003-0862-2018'}]},
          'role': 'other'},
         {'person_or_org':
          {'family_name': 'Bai', 'given_name': 'Xing', 'type': 'personal'},
          'role': 'other'},
         {'person_or_org':
          {'family_name': 'Drill', 'given_name': 'Esther', 'type': 'personal',
           'identifiers': [{'scheme': 'orcid', 'identifier': '0000-0002-3315-4538'}]},
          'role': 'other'},
         {'person_or_org':
          {'family_name': 'Flynn', 'given_name': 'Jessica', 'type': 'personal',
           'identifiers': [{'scheme': 'orcid', 'identifier': '0000-0001-8310-6684'}]},
          'role': 'other'},
         {'person_or_org':
          {'family_name': 'Hannum', 'given_name': 'Margie', 'type': 'personal',
           'identifiers': [{'scheme': 'orcid', 'identifier': '0000-0002-2953-0449'}]},
          'role': 'other'},
         {'person_or_org':
          {'family_name': 'Lobaugh', 'given_name': 'Stephanie', 'type': 'personal'},
          'role': 'other'},
         {'person_or_org':
          {'family_name': 'Pileggi', 'given_name': 'Shannon', 'type': 'personal',
           'identifiers': [{'scheme': 'orcid', 'identifier': '0000-0002-7732-4164'}]},
          'role': 'other'},
         {'person_or_org':
          {'family_name': 'Tin', 'given_name': 'Amy', 'type': 'personal',
           'identifiers': [{'scheme': 'orcid', 'identifier': '0000-0002-8005-0694'}]},
          'role': 'other'},
         {'person_or_org':
          {'family_name': 'Zapata Wainberg', 'given_name': 'Gustavo', 'type': 'personal', 'identifiers':
           [{'scheme': 'orcid', 'identifier': '0000-0002-2524-3637'}]},
          'role': 'other'}
         ]
    assert deduplicated(p) == p

    assert deduplicated(x for x in [1, 2, 3]) == [1, 2, 3]
    assert deduplicated(filter(None, [1, 2, 3])) == [1, 2, 3]
    assert deduplicated(filter(lambda x: x == 2, [1, 2, 3])) == [2]


def test_similar_urls():
    assert similar_urls('https://foo.com/bar'  , 'http://foo.com/bar')
    assert similar_urls('http://foo.com/bar'   , 'https://foo.com/bar')
    assert similar_urls('https://foo.com/bar/' , 'https://foo.com/bar')
    assert similar_urls('https://foo.com/bar'  , 'https://foo.com/bar/')
    assert similar_urls('http://foo.com/bar/'  , 'https://foo.com/bar')
    assert similar_urls('http://foo.com/bar'   , 'https://foo.com/bar/')


def test_lisitifed():
    assert listified([]) == []
    assert listified('') == []
    assert listified('a') == ['a']
    assert listified('a b') == ['a b']
    assert listified(['a']) == ['a']
    assert listified(['a', 'b']) == ['a', 'b']
    assert isinstance(listified(x for x in ['a', 'b']), Generator)


def test_normalized_url():
    assert normalized_url('git@github.com:IonicaBizau/node-git-url-parse.git') == 'https://github.com/IonicaBizau/node-git-url-parse'
    assert normalized_url('https://github.com/IonicaBizau/node-git-url-parse.git') == 'https://github.com/IonicaBizau/node-git-url-parse'
    assert normalized_url('git+ssh://git@github.com:organization/repo.git#hashbrowns') == 'https://github.com/organization/repo'
    assert normalized_url('git+https://github.com/cds-astro/tutorials') == 'https://github.com/cds-astro/tutorials'
