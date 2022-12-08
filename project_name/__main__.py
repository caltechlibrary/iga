'''
__main__.py: main function for %PROJECT_NAME%.

Copyright
---------

Copyright (c) %CREATION_YEAR% by the California Institute of Technology.  This code
is open-source software released under a BSD-type license.  Please see the
file "LICENSE" for more information.
'''

import sys
if sys.version_info <= (3, 8):
    print('%PROJECT_NAME% requires Python version 3.8 or higher,')
    print('but the current version of Python is ' + str(sys.version_info.major)
          + '.' + str(sys.version_info.minor) + '.')
    sys.exit(1)

import plac
from   sidetrack import set_debug, log


# Main program.
# .............................................................................

# For more info about how plac works see https://plac.readthedocs.io/en/latest/
@plac.annotations(
    version    = ('print version info and exit'               , 'flag'  , 'V'),
    debug      = ('log debug output to "OUT" ("-" is console)', 'option', '@'),
    args       = 'arguments'
)
def main(version=False, debug='OUT', *args):
    '''%PROJECT_DESCRIPTION%'''

    # Set up debug logging as soon as possible, if requested ------------------

    if debug != 'OUT':
        config_debug(debug)
    else:
        debug = False

    # Preprocess arguments and handle early exits -----------------------------

    if version:
        print_version_info()
        sys.exit()

    # ... PROCESS OTHER ARGS HERE ...

    # Do the real work --------------------------------------------------------

    # ... YOUR MAIN CODE HERE ...


# Miscellaneous helper functions.
# .............................................................................

def config_debug(debug_arg):
    set_debug(True, debug_arg)
    import faulthandler
    faulthandler.enable()
    import os
    if os.name != 'nt':                 # Can't use next part on Windows.
        import signal
        from boltons.debugutils import pdb_on_signal
        pdb_on_signal(signal.SIGUSR1)
        log(f'installed signal handler on {signal.SIGUSR1}')


def print_version_info():
    # Precaution: add parent dir in case user is running from our source dir.
    from os import path
    sys.path.append(path.join(path.dirname(path.abspath(__file__)), '..'))
    from refoliate import print_version
    print_version()


# Main entry point.
# .............................................................................

# The following entry point definition is for the console_scripts keyword
# option to setuptools.  The entry point for console_scripts has to be a
# function that takes zero arguments.
def console_scripts_main():
    plac.call(main)


# The following allows users to invoke this using "python3 -m handprint".
if __name__ == '__main__':
    # Print help if the user supplied no command-line arguments.
    if len(sys.argv) == 1 or (len(sys.argv) > 1 and sys.argv[1] == 'help'):
        plac.call(main, ['-h'])
    else:
        plac.call(main)
