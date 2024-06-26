'''
__init__.py for iga

This file is part of https://github.com/caltechlibrary/iga/.

Copyright (c) 2022-2024 by the California Institute of Technology.  This code
is open-source software released under a BSD-type license.  Please see the
file "LICENSE" for more information.
'''

# Package metadata
# .............................................................................
#
#  ╭────────────────────── Notice ── Notice ── Notice ─────────────────────╮
#  │    The following values are automatically updated at every release    │
#  │    by the Makefile. Manual changes to these values will be lost.      │
#  ╰────────────────────── Notice ── Notice ── Notice ─────────────────────╯

__version__     = '1.3.0'
__description__ = 'The InvenioRDM GitHub Archiver (IGA) automatically archives GitHub releases in an InvenioRDM repository.'
__url__         = 'https://caltechlibrary.github.io/iga'
__author__      = 'Michael Hucka'
__email__       = 'mhucka@caltech.edu'
__license__     = 'https://github.com/caltechlibrary/iga/blob/main/LICENSE'


# Miscellaneous utilities.
# .............................................................................

def print_version():
    print(f'{__name__} version {__version__}')
    print(f'Authors: {__author__}')
    print(f'URL: {__url__}')
    print(f'License: {__license__}')
