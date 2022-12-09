'''
cli.py: command-line interface for IGA

This file is part of https://github.com/caltechlibrary/iga/.

Copyright (c) 2022 by the California Institute of Technology.  This code
is open-source software released under a BSD-type license.  Please see the
file "LICENSE" for more information.
'''

import rich_click as click
import sys
from sidetrack import set_debug, log

from .exit_codes import ExitCode


# Helper functions used below.
# .............................................................................

def _print_version(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    # Precaution: add parent dir in case user is running from our source dir.
    from os import path
    sys.path.append(path.join(path.dirname(path.abspath(__file__)), '..'))
    from iga import print_version
    print_version()


def _config_debug(ctx, param, debug_arg):
    set_debug(True, debug_arg)
    import faulthandler
    faulthandler.enable()
    import os
    if os.name != 'nt':                 # Can't use next part on Windows.
        import signal
        from boltons.debugutils import pdb_on_signal
        pdb_on_signal(signal.SIGUSR1)
        log(f'installed signal handler on {signal.SIGUSR1}')


# Main command-line interface.
# .............................................................................

# Rich click style preferences.

click.rich_click.STYLE_HELPTEXT = ""
click.rich_click.USE_MARKDOWN = True


# Note #1: the default rich_click help feature does not offer a -h short form,
# hence the need to use our own explicit definition below.
#
# Note #2: The `\r` after the first line of the doc string below is a hack to
# introduce a blank line at that point in the rendered help output. Rich_click
# version 1.6.0 collapses the first blank line, which I find annoying.
# This use of `\r` assumes the use of Markdown (as set above).

@click.command(add_help_option=False)
@click.help_option('--help', '-h', help='show this message and exit')
@click.option('--version', '-V', help='print version info and exit',
              callback=_print_version, is_flag=True, expose_value=False)
@click.option('--debug'  , '-@', help='write debug output to destination "OUT"',
              callback=_config_debug, metavar='OUT')
@click.argument('archive')
@click.pass_context
def cli(ctx, archive, help=False, test=False, version=False, debug=False):
    '''InvenioRDM GitHub Archiver command-line interface.
    \r
This is a command-line program whose purpose is to upload an archive containing
a software release to an InvenioRDM server. The archive file must be passed as
the final argument (**ARCHIVE**) on the command-line; the various options
described below determine where **ARCHIVE** is uploaded, the version number,
and other information necessary to perform the upload.
'''
    # Detect if the user types "help" without dashes and be accommodating.
    if archive == 'help':
        click.echo(ctx.get_help())
        sys.exit(int(ExitCode.success))
