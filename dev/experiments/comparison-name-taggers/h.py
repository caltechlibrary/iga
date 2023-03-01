#!/usr/bin/env python3

# import requests

# API_URL = "https://api-inference.huggingface.co/models/opensource/extract_names"
# headers = {"Authorization": f"Bearer {API_TOKEN}"}

# def query(payload):
# 	response = requests.post(API_URL, headers=headers, json=payload)
# 	return response.json()

# output = query({
# 	"inputs": "My name is Sarah Jessica Parker but you can call me Jessica",
# })


from transformers import AutoTokenizer, AutoModelForTokenClassification

model_name = "opensource/extract_names"

tokenizer = AutoTokenizer.from_pretrained(model_name)

model = AutoModelForTokenClassification.from_pretrained(model_name)

breakpoint()
