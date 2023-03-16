'''
markdown_utils.py: utilities for dealing with Markdown conversion

This file is part of https://github.com/caltechlibrary/iga/.

Copyright (c) 2023 by the California Institute of Technology.  This code
is open-source software released under a BSD-type license.  Please see the
file "LICENSE" for more information.
'''

import markdown


# List of extensions for python-markdown:
# https://github.com/Python-Markdown/markdown/wiki/Third-Party-Extensions


# Supposed to use this form:
# import markdown
# from markdown_checklist.extension import ChecklistExtension
# html = markdown.markdown(source, extensions=[ChecklistExtension()])
#
# https://python-markdown.github.io/reference/

def html_from_md(md):
    return markdown.markdown(md, extensions=['pymdownx.superfences',
                                             'pymdownx.extra',
                                             'pymdownx.emoji',
                                             'mdx_breakless_lists',
                                             'markdown_checklist.extension',
                                             ])
