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

def _config_debug(ctx, param, debug_dest):
    '''Handle the --debug option and configure debug settings as needed.'''
    if debug_dest:
        if debug_dest.name == '<stdout>':
            set_debug(True, '-')
        else:
            set_debug(True, debug_dest.name)
        import faulthandler
        faulthandler.enable()
        if os.name != 'nt':                 # Can't use next part on Windows.
            import signal
            from boltons.debugutils import pdb_on_signal
            pdb_on_signal(signal.SIGUSR1)
            log(f'installed signal handler on {signal.SIGUSR1}')


def _print_help_and_exit(ctx):
    '''Print the help text and exit with a success code.'''
    click.echo(ctx.get_help())
    sys.exit(int(ExitCode.success))


def _print_version_and_exit(ctx, param, value):
    '''Handle the --version option by printing version info if asked.'''
    if not value or ctx.resilient_parsing:
        return
    # Precaution: add parent dir in case user is running from our source dir.
    from os import path
    sys.path.append(path.join(path.dirname(path.abspath(__file__)), '..'))
    from iga import print_version
    print_version()
    sys.exit(int(ExitCode.success))


def _read_token(ctx, param, file_):
    '''Read the file and set the environment variable RDM_TOKEN.'''
    if ctx.params.get('record', None) == 'help':
        _print_help_and_exit(ctx)
    elif file_:
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
    if ctx.params.get('record', None) == 'help':
        _print_help_and_exit(ctx)
    elif value:
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
@click.option('--record', '-r', metavar='FILE',
              help='Record to use for the entry in InvenioRDM')
@click.option('--server', '-s', metavar='URL', callback=_read_server,
              help='Address of InvenioRDM server')
@click.option('--token', '-t', metavar='FILE', type=File('r'), callback=_read_token,
              help="File ('-' for stdin) containing a PAT for InvenioRDM")
@click.option('--version', '-V', callback=_print_version_and_exit, is_flag=True,
              help='Print version info and exit', expose_value=False)
@click.option('--debug'  , '-@', metavar='OUT', type=File('w', lazy=False),
              callback=_config_debug, help='Write debug output to destination "OUT"')
#
@click.argument('release', required=True)
@click.pass_context
def cli(ctx, release, community=None, file=None, server=None, token=None,
        help=False, version=False, debug=False):  # noqa A002
    '''InvenioRDM GitHub Archiver command-line interface.
\r
IGA is a program that retrieves the GitHub software release identified by
**RELEASE** and archives it in an InvenioRDM server. By default, it will
create a record based on information extracted from the GitHub repository; this
can be overriden by command-line options described below. Also by default, it
will attach to the InvenioRDM record all the file assets associated with the
software release in GitHub; this can also be overriden by command-line options.
\r
_**InvenioRDM server and access token**_
\r
The server address must be provided either as the value of the option
`--server` _or_ in an environment variable named `RDM_SERVER`.
\r
A Personal Access Token (PAT) for making API calls to the InvenioRDM server
must be also supplied when invoking IGA, either in a file whose path is given
as the value of the option `--token` (use `-` for standard input), _or_ in an
environment variable named `RDM_TOKEN`. (To obtain a PAT from an InvenioRDM
server, visit the page `/account/settings/applications` after logging in to
your account and use the interface there to create a token.)
\r
_**GitHub releases and assets**_
\r
Releases in GitHub are identified by git tags. The value of **RELEASE**
(which must always be provided on the command line when invoking IGA) should
be a complete URL pointing at a tagged release in a public GitHub repository.
Here is an example command:
```
iga --server https://data.caltech.edu --token token.txt \\
    https://github.com/mhucka/taupe/releases/tag/v1.2.0
```
\r
The record created in InvenioRDM is constructed using information extracted
from the software release and repository using GitHub's API. The information
includes:
 * the data provided by GitHub for the release
 * the data provided by GitHub for the repository
 * a `CITATION.cff` file in the repository (if one exists)
 * the file assets associated with the release
\r
To override the auto-created record, you can use the option `--record` followed
by a path to a JSON file in DataCite 4.3 format. If `--record` is provided, IGA
does not extract the data above, but still obtains the file assets from GitHub.
\r
To override which file assets are attached to the record created in InvenioRDM,
you can use the option `--file` followed by a path to a file to be uploaded.
The option `--file` can be repeated to upload multiple file assets. Note that
if `--file` is provided, then IGA does _not_ use any file assets from GitHub.
\r
If both `--record` and `--file` are used, then IGA does not actually contact
GitHub for any information.
\r
_**Other options recognized by IGA**_
\r
Running IGA with the option `--help` will make it print help text and exit
without doing anything else.
\r
If given the `--version` option, this program will print its version and other
information, and exit without doing anything else.
\r
If given the `--debug` argument, taupe will output details about what it is
doing. The debug trace will be sent to the given destination, which can be `-`
to indicate console output, or a file path to send the debug output to a file.
\r
_**Return values**_
\r
This program exits with a return status code of 0 if no problem is encountered.
Otherwise, it returns a nonzero status code. The following table lists the
possible values:
\r
  0 = success – program completed normally  
  1 = the user interrupted the program's execution  
  2 = encountered a bad or missing value for an option  
  3 = file error – encountered a problem with a file  
  4 = an exception or fatal error occurred  

'''
    # Detect if the user types "help" without dashes, and be helpful.
    if record == 'help':
        _print_help_and_exit(ctx)
