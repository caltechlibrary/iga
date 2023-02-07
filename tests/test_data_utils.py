from iga.data_utils import deduplicated


def test_deduplicated():
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
