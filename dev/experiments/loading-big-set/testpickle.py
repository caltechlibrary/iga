#!/usr/bin/env python3

import gzip
import pickle
from commonpy.data_structures import CaseFoldSet
from timeit import timeit


def read_from_file():
    orgs = CaseFoldSet()
    with open('github-orgs.txt', 'r') as f:
        for line in f.readlines():
            orgs.add(line)
    return orgs


def make_pickle():
    orgs = CaseFoldSet()
    with open('github-orgs.txt', 'r') as f:
        for line in f.readlines():
            orgs.add(line)
    with open('pickle.p', 'wb') as f:
        pickle.dump(orgs, f)


def read_from_pickle():
    with open('pickle.p', 'rb') as f:
        return pickle.load(f)


def read_from_gzipped_pickle():
    with gzip.open('pickle.p.gz', 'rb') as pickle_file:
        return pickle.load(pickle_file)


print('file = ', timeit(read_from_file, number=10))
print('pickle = ', timeit(read_from_pickle, number=10))
print('gzipped pickle = ', timeit(read_from_gzipped_pickle, number=10))
