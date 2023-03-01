#!/usr/bin/env python3

from transformers import AutoTokenizer, AutoModelForTokenClassification
from transformers import pipeline

tokenizer = AutoTokenizer.from_pretrained("xlm-roberta-large-finetuned-conll03-english")
model = AutoModelForTokenClassification.from_pretrained("xlm-roberta-large-finetuned-conll03-english")
classifier = pipeline("ner", model=model, tokenizer=tokenizer)

from pprint import pprint
pprint(classifier('Martin Luther King, Jr.'))
breakpoint()
