#!/usr/bin/env python3

import spacy

nlp = spacy.load('ko_core_news_lg')

with open('korean.txt', 'r') as file:
    names = file.read().splitlines()

def has_entities(result):
    return result if result.ents else None

results = [nlp(n) for n in names]
labels = [x.ents[0].label_ for x in filter(has_entities, results)]

percent = ( len(labels)/len(names) )*100
print(f'Labeled {len(labels)} out of {len(names)} names ({percent:3.1f}%)')

correct = sum(1 for value in labels if value == 'PS')
incorrect = len(labels) - correct

percent_correct = ( correct/len(names) )*100
print(f'Correct: {correct} out of {len(labels)} labels ({percent_correct:3.1f}% of total)')
