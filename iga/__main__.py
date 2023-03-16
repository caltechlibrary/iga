'''
__main__.py: main entry point for IGA.

This file is part of https://github.com/caltechlibrary/iga/.

Copyright (c) 2022-2023 by the California Institute of Technology.  This code
is open-source software released under a BSD-type license.  Please see the
file "LICENSE" for more information.
'''

import sys
if sys.version_info <= (3, 9):
    print('IGA requires Python version 3.9 or higher,')
    print('but the current version of Python is ' + str(sys.version_info.major)
          + '.' + str(sys.version_info.minor) + '.')
    sys.exit(1)

from iga.cli import cli


# The following entry point definition is for the console_scripts keyword
# option to setuptools.  The entry point for console_scripts has to be a
# function that takes zero arguments.
def console_scripts_main():
    cli()


# The following allows users to invoke this using "python3 -m iga".
if __name__ == '__main__':
    cli()
