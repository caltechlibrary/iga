#!/usr/bin/env python3

from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline

model_name = 'dslim/bert-large-NER'

bert_tokenizer = AutoTokenizer.from_pretrained(model_name)
bert_model = AutoModelForTokenClassification.from_pretrained(model_name)

nlp = pipeline('ner', model=bert_model, tokenizer=bert_tokenizer)

from pprint import pprint
pprint(nlp('Martin Luther King, Jr.'))

breakpoint()
