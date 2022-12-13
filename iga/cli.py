'''
cli.py: command-line interface for IGA

This file is part of https://github.com/caltechlibrary/iga/.

Copyright (c) 2022 by the California Institute of Technology.  This code
is open-source software released under a BSD-type license.  Please see the
file "LICENSE" for more information.
'''

import os
import rich_click as click
from   rich_click import File
import sys
from   sidetrack import set_debug, log

from .exit_codes import ExitCode
from .invenio import invenio_write


# Helper functions used below.
# .............................................................................

def _print_version(ctx, param, value):
    '''Handle the --version option by printing version info if asked.'''
    if not value or ctx.resilient_parsing:
        return
    # Precaution: add parent dir in case user is running from our source dir.
    from os import path
    sys.path.append(path.join(path.dirname(path.abspath(__file__)), '..'))
    from iga import print_version
    print_version()


def _config_debug(ctx, param, debug_arg):
    '''Handle the --debug option and configure debug settings as needed.'''
    if not debug_arg:
        return
    set_debug(True, debug_arg)
    import faulthandler
    faulthandler.enable()
    if os.name != 'nt':                 # Can't use next part on Windows.
        import signal
        from boltons.debugutils import pdb_on_signal
        pdb_on_signal(signal.SIGUSR1)
        log(f'installed signal handler on {signal.SIGUSR1}')


def _read_token(ctx, param, file_):
    '''Read the file and set the environment variable RDM_TOKEN.'''
    if file_:
        log('reading token from file')
        os.environ['RDM_TOKEN'] = file_.read()
    elif 'RDM_TOKEN' in os.environ:
        log('RDM_TOKEN found in environment')
        pass
    else:
        _print_error(ctx, 'Cannot proceed without a Personal Access Token.'
                     ' The `--token` option was not given and the'
                     ' environment variable **RDM_TOKEN** is not set.')
        sys.exit(int(ExitCode.bad_arg))


def _read_server(ctx, param, value):
    '''Read the server address and set the environment variable RDM_SERVER.'''
    if value:
        log('server address given on command line: ' + value)
        os.environ['RDM_SERVER'] = value
    elif 'RDM_SERVER' in os.environ:
        log('RDM_SERVER found in environment')
        pass
    else:
        _print_error(ctx, 'Cannot proceed without the address of the InvenioRDM'
                     ' server. The `--server` option was not given and the'
                     ' environment variable **RDM_SERVER** is not set.')
        sys.exit(int(ExitCode.bad_arg))


def _print_error(ctx, msg):
    '''Print an error message in the style of rich_click.
    Meant to be used when reporting errors involving UI options, in situations
    where rich_click's own error reporting can't be used directly.'''
    # The following code tries to emulate what rich_click does. It doesn't use
    # private methods or properties, but it might break if rich_click changes.
    log('error: ' + msg)
    from rich.console import Console
    from rich.markdown import Markdown
    from rich.padding import Padding
    from rich.panel import Panel
    from rich.theme import Theme
    from rich_click.rich_click import (
        ALIGN_ERRORS_PANEL,
        ERRORS_PANEL_TITLE,
        STYLE_ERRORS_PANEL_BORDER,
        STYLE_USAGE,
        STYLE_OPTION,
        STYLE_ARGUMENT,
        STYLE_SWITCH,
        OptionHighlighter,
    )
    highlighter = OptionHighlighter()
    console = Console(theme=Theme({
        "option": STYLE_OPTION,
        "argument": STYLE_ARGUMENT,
        "switch": STYLE_SWITCH,
        "usage": STYLE_USAGE,
    }), highlighter=highlighter)
    console.print(Padding(highlighter(ctx.get_usage()), 1))
    console.print(
        Panel(
            Markdown(msg),
            border_style=STYLE_ERRORS_PANEL_BORDER,
            title=ERRORS_PANEL_TITLE,
            title_align=ALIGN_ERRORS_PANEL,
        )
    )


# Main command-line interface.
# .............................................................................

# Style preferences for rich_click module.

click.rich_click.STYLE_HELPTEXT = ""
click.rich_click.USE_MARKDOWN = True
click.rich_click.STYLE_ERRORS_SUGGESTION = "bold italic"
click.rich_click.ERRORS_EPILOGUE = "Suggestion: use the --help flag to get help."


# Note #1: the default rich_click help feature does not offer a -h short form,
# hence the need to use our own explicit definition below.
#
# Note #2: The `\r` after the first line of the doc string below is a hack to
# introduce a blank line at that point in the rendered help output. Rich_click
# version 1.6.0 collapses the first blank line, which I find annoying.
# This use of `\r` assumes the use of Markdown (as set above).

@click.command(add_help_option=False)
@click.help_option('--help', '-h', help='Show this message and exit')
#
@click.option('--community', '-c', metavar='ID',
              help='ID of RDM community to update with item')
@click.option('--file', '-f', metavar='FILE', multiple=True,
              help='File to upload (repeat for multiple files)')
@click.option('--server', '-s', metavar='URL', callback=_read_server,
              help='Address of InvenioRDM server')
@click.option('--token', '-t', metavar='FILE', type=File('r'), callback=_read_token,
              help="File ('-' for stdin) containing a PAT for InvenioRDM")
@click.option('--version', '-V', callback=_print_version, is_flag=True,
              help='Print version info and exit', expose_value=False)
@click.option('--debug'  , '-@', metavar='OUT', callback=_config_debug,
              help='Write debug output to destination "OUT"')
#
@click.argument('record', required=True)
@click.pass_context
def cli(ctx, record, community=None, file=None, server=None, token=None,
        help=False, version=False, debug=False):  # noqa A002
    '''InvenioRDM GitHub Archiver command-line interface.
\r
This program creates the given **RECORD** in an InvenioRDM server and
attaches one or more files to the record. The server address must be supplied
either as the value of the option `--server` _or_ in an environment variable
named `RDM_SERVER`. Any file(s) to be attached to the record must be supplied
as the value of the option `--file`; this option can be supplied more than
once. Finally, a Personal Access Token for making API calls to the server
must be also supplied, either in a file whose path is given as the value of
the option `--token` (use `-` for standard input), _or_ in an environment
variable named `RDM_TOKEN`.
'''
    # Detect if the user types "help" without dashes, and be helpful.
    if record == 'help':
        click.echo(ctx.get_help())
        sys.exit(int(ExitCode.success))
