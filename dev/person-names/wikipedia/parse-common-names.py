#!/usr/bin/env python3

import pandas as pd
import lxml
import string
import itertools

url = 'https://en.wikipedia.org/wiki/List_of_common_Chinese_surnames'
page = pd.read_html(url, encoding='UTF-8')

names = set()

# Table "Surname list"

table = page[1]
names.update(table['Character'].values[:, 0].tolist())
names.update(table['Character'].values[:, 1].tolist())

# Table "400 character list"

table = page[2]
names.update(table['Name'].values[:].tolist())

# Table "Taiwan"

table = page[3]
names.update(table['Character'].values[:, 0].tolist())
names.update(table['Character'].values[:, 1].tolist())

# Table "Philippines"

table = page[4]
# This one has slashes in the values.
list_of_lists = [item.split('/') for item in table['Character(s)'].values.tolist()]
flattened = itertools.chain(*list_of_lists)
names.update(flattened)

# Table "Ontario"

table = page[5]
names.update(table['Character(s)'].values[:, 0].tolist())
names.update(table['Character(s)'].values[:, 1].tolist())

# Table "Newer version"

table = page[8]
names.update(table['Character(s)'].values[:, 0].tolist())
names.update(table['Character(s)'].values[:, 1].tolist())

# Table "United States"

table = page[9]
names.update(table['Character(s)'].values[:, 0].tolist())
names.update(table['Character(s)'].values[:, 1].tolist())

print(*names, sep='\n')
