#!/usr/bin/env python3

from transformers import AutoTokenizer, AutoModelForTokenClassification
from transformers import pipeline

model_name = "Davlan/distilbert-base-multilingual-cased-ner-hrl"

tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForTokenClassification.from_pretrained(model_name)
nlp = pipeline("ner", model=model, tokenizer=tokenizer, aggregation_strategy="max")

from pprint import pprint
pprint(nlp('Martin Luther King, Jr.'))
breakpoint()
