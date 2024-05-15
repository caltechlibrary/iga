#!/usr/bin/env python3
# Summary: print names of top South Korean GitHub contributors.
# Data from https://github.com/gayanvoice/top-github-users

import pandas as pd
import lxml
import string

base_url = 'https://raw.githubusercontent.com/gayanvoice/top-github-users/main/markdown/public_contributions'
page_url = f'{base_url}/south_korea.md'

# Despite that the page is .md, the table inside it is actually in raw HTML.
page = pd.read_html(page_url, encoding='UTF-8')
table = page[3]

# Remove non-Korean script characters.
remove_latin = str.maketrans('', '', string.printable)

names = [name.translate(remove_latin) for name in table['Name']]
names = [nonblank for nonblank in names if nonblank]
print(*names, sep='\n')
