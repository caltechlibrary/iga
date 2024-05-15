#!/usr/bin/env python3 -u

import sys

# ja_ginza
# ja_ginza_electra
# ja_core_news_lg
# ja_core_news_trf

if len(sys.argv) < 2:
    exit('Need one argument: a model name')

model = sys.argv[1]

import spacy
print(f'Loading spacy model {model} ...')
nlp = spacy.load(model)
print(f'Loading spacy model {model} ... Done.')

with open('../../person-names/japanese-surnames.txt', 'r') as file:
    names = file.read().splitlines()

names_subset = names[::10]

def spacy_result(name):
    print('.', end='')
    return nlp(name)

def has_entities(result):
    return result if result.ents else None

results = [spacy_result(n) for n in names_subset]
labels = [x.ents[0].label_ for x in filter(has_entities, results)]

percent = ( len(labels)/len(names_subset) )*100
print(f'Labeled {len(labels)} out of {len(names_subset)} names ({percent:3.1f}%)')

correct = sum(1 for value in labels if value.lower() == 'person')
incorrect = len(labels) - correct

percent_correct = ( correct/len(names_subset) )*100
print(f'Correct: {correct} out of {len(labels)} labels ({percent_correct:3.1f}% of total)')
