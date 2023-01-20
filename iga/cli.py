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

from iga.exit_codes import ExitCode
from iga.exceptions import GitHubError, InvenioRDMError, InternalError
from iga.github import valid_github_release_url, github_account_repo_tag
from iga.invenio import invenio_write
from iga.record import valid_record, record_from_release


# Main command-line interface.
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# Style preferences for rich_click module .....................................

click.rich_click.STYLE_HELPTEXT = ""
click.rich_click.USE_MARKDOWN = True
click.rich_click.STYLE_ERRORS_SUGGESTION = "bold italic"
click.rich_click.ERRORS_EPILOGUE = "Suggestion: use the --help flag to get help."


# Callback functions used in click interface ..................................

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
    return debug_dest


def _read_token(ctx, param, file_):
    '''Read the file and set the environment variable RDM_TOKEN.'''
    if ctx.params.get('url_or_tag', None) == 'help':
        print_help_and_exit(ctx)
    elif file_:
        log('reading token from file')
        os.environ['RDM_TOKEN'] = file_.read()
    elif 'RDM_TOKEN' in os.environ:
        log('RDM_TOKEN found in environment')
    else:
        alert(ctx, 'Cannot proceed without a Personal Access Token. (Tip: provide'
              ' the `--token` option or set the environment variable **RDM_TOKEN**.)')
        sys.exit(int(ExitCode.bad_arg))
    return os.environ['RDM_TOKEN']


def _read_server(ctx, param, value):
    '''Read the server address and set the environment variable RDM_SERVER.'''
    if ctx.params.get('url_or_tag', None) == 'help':
        print_help_and_exit(ctx)
    elif value:
        log('server address given on command line: ' + value)
        os.environ['RDM_SERVER'] = value
    elif 'RDM_SERVER' in os.environ:
        log('RDM_SERVER found in environment')
    else:
        alert(ctx, 'Cannot proceed without an InvenioRDM server address. (Tip:'
              ' provide the `--server` option or set the environment variable'
              ' **RDM_SERVER**.)')
        sys.exit(int(ExitCode.bad_arg))
    return os.environ['RDM_SERVER']


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


# Note #1: the default rich_click help feature does not offer a -h short form,
# hence the need to use our own explicit help_option() definition below.
#
# Note #2: The `\r` in the doc string below is a hack to introduce a blank
# lines between paragraphs. Rich_click version 1.6.0 collapses blank lines,
# which I hate.  This use of `\r` assumes the use of Markdown (as set above).

@click.command(add_help_option=False)
@click.help_option('--help', '-h', help='Show this message and exit')
#
@click.option('--account', '-a', metavar='TEXT',
              help='GitHub account name (if not using a release URL)')
#
@click.option('--community', '-c', metavar='ID',
              help='ID of RDM community to update with item')
#
@click.option('--dry-run', '-n', is_flag=True,
              help='Print what would be created but do not create it')
#
@click.option('--file', '-f', 'given_files', metavar='FILE', multiple=True,
              help='File to upload (repeat for multiple files)')
#
@click.option('--record', '-r', 'given_record', metavar='FILE', type=File('r'),
              help='Record to use for the entry in InvenioRDM')
#
@click.option('--repo', '-p', metavar='TEXT',
              help='GitHub repository name (if not using a release URL)')
#
@click.option('--server', '-s', metavar='URL', callback=_read_server,
              help='Address of InvenioRDM server')
#
@click.option('--token', '-t', metavar='FILE', type=File('r'), callback=_read_token,
              help="File ('-' for stdin) containing a PAT for InvenioRDM")
#
@click.option('--version', '-V', callback=_print_version_and_exit, is_flag=True,
              help='Print version info and exit', expose_value=False)
#
@click.option('--debug'  , '-@', metavar='OUT', type=File('w', lazy=False),
              callback=_config_debug, help='Write debug output to destination "OUT"')
#
@click.argument('url_or_tag', required=True)
@click.pass_context
def cli(ctx, url_or_tag, account=None, community=None, dry_run=False,
        given_files=None, given_record=None, repo=None, server=None,
        token=None, help=False, version=False, debug=False):  # noqa A002
    '''InvenioRDM GitHub Archiver (IGA) command-line interface.
\r
IGA retrieves a GitHub software release and archives it in an InvenioRDM
server. The release can be specified using _either_ a full URL, _or_ an
account + repository + tag combination (see below). By default, IGA constructs
a record based on information extracted from the GitHub repository; this can be
overriden by command-line options described below.
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
server, visit the page `/account/settings/applications` on the server after
logging in to your account and use the interface there to create a token.)
\r
_**Specification of a GitHub release**_
\r
A GitHub release can be specified to IGA in one of two mutually-exclusive ways:
 1. The full URL of the web page on GitHub of a tagged release. In this case,
    the URL must be the final argument on the command line invocation of IGA
    and the options `--account` and `--repo` must be omitted.
 2. A combination of _account name_, _repository name_, and _tag_. In this
    case, the final argument on the command line must be the _tag_, and in
    addition, values for the options `--account` and `--repo` must be provided.
\r
Here's an example using approach #1:
```
iga --server https://data.caltech.edu --token token.txt \\
    https://github.com/mhucka/taupe/releases/tag/v1.2.0
```
and here's the equivalent using approach #2:
```
iga --server https://data.caltech.edu --token token.txt \\
    --account mhucka --repo taupe v1.2.0
```
_**Construction of an InvenioRDM record**_
\r
The record created in InvenioRDM is constructed using information extracted
from the software release and its source repository using GitHub's API. The
information includes the following:
 * the data available from GitHub for the release
 * the data available from GitHub for the repository
 * (if one exists) a `codemeta.json` file in the repository
 * (if one exists) a `CITATION.cff` file
 * the file assets associated with the release
\r
To override the auto-created record, use the option `--record` followed by the
path to a JSON file structured according to the InvenioRDM schema used by
the destination server. When `--record` is provided, IGA does _not_ extract
the data above, but still obtains the file assets from GitHub.
\r
_**Specification of GitHub file assets**_
\r
By default, IGA attaches to the InvenioRDM record all file assets associated
with the software release in GitHub. To override which file assets are attached
to the InvenioRDM record, you can use the option `--file` followed by a path to
a file to be uploaded. The option `--file` can be repeated to upload multiple
file assets. Note that if `--file` is provided, then IGA does not use any
file assets from GitHub.
\r
If _both_ `--record` and `--file` are used, then IGA does not actually contact
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
  3 = no network detected – cannot proceed  
  4 = encountered a problem with a file or directory  
  5 = encountered a problem interacting with GitHub  
  6 = encountered a problem interacting with InvenioRDM  
  7 = a miscellaneous exception or fatal error occurred  
'''
    # Process arguments & handle early exits ..................................

    if url_or_tag == 'help':  # Detect if the user typed "help" without dashes.
        print_help_and_exit(ctx)
    elif url_or_tag.startswith('http'):
        if any([account, repo]):
            alert(ctx, 'The use of a URL and the use of options `--account`'
                  " and `--repo` are mutually exclusive; can't use both.")
            sys.exit(int(ExitCode.bad_arg))
        elif not valid_github_release_url(url_or_tag):
            alert(ctx, 'Malformed release URL: ' + str(url_or_tag))
            sys.exit(int(ExitCode.bad_arg))
        else:
            account, repo, tag = github_account_repo_tag(url_or_tag)
    elif not all([account, repo, url_or_tag]):
        alert(ctx, 'When not using a release URL, the options `--account` and'
              ' `--repo` and a tag name must all be provided.')
        sys.exit(int(ExitCode.bad_arg))
    else:
        tag = url_or_tag

    if given_record:
        path = given_record.name
        log('reading user-provided record from ' + path)
        given_record = given_record.read().strip()
        if not valid_record(given_record):
            alert(ctx, 'File not in valid JSON format for InvenioRDM: ' + path)
            sys.exit(int(ExitCode.file_error))

    from commonpy.network_utils import network_available
    if not network_available():
        alert(ctx, 'No network – cannot proceed.')
        sys.exit(int(ExitCode.no_network))

    # Do the main work ........................................................

    exit_code = ExitCode.success
    try:
        record = given_record or record_from_release(account, repo, tag)
        if dry_run:
            report_actions(ctx, record)
        else:
            invenio_write(record, server, token)
    except KeyboardInterrupt:
        # Catch it, but don't treat it as an error; just stop execution.
        log('keyboard interrupt received')
        exit_code = ExitCode.user_interrupt
    except GitHubError as ex:
        log('quitting due to GitHub error: ' + str(ex))
        exit_code = ExitCode.github_error
    except InvenioRDMError as ex:
        log('quitting due to InvenioRDM error: ' + str(ex))
        exit_code = ExitCode.inveniordm_error
    except Exception as ex:             # noqa: PIE786
        exit_code = ExitCode.exception
        import traceback
        exception = sys.exc_info()
        details = ''.join(traceback.format_exception(*exception))
        log('exception: ' + str(ex) + '\n\n' + details)
        import iga
        alert(ctx, 'IGA experienced an unrecoverable error. Please report this'
              f' to the developers. Your version of IGA is {iga.__version__}.'
              f' For information about how to report errors, please see the'
              f' project page at {iga.__url__}/.\n\nError text: {str(ex)}', False)

    # Exit with status code ...................................................

    log(f'exiting with exit code {int(exit_code)}.')
    sys.exit(int(exit_code))


# Helper functions used above.
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def print_help_and_exit(ctx):
    '''Print the help text and exit with a success code.'''
    click.echo(ctx.get_help())
    sys.exit(int(ExitCode.success))


def report_actions(ctx, record):
    from rich.console import Console
    from rich.markdown import Markdown
    from rich.panel import Panel
    from rich import print_json

    comment = (f'Option `--dry-run` is in effect. The following is the record'
               f' that _would_ have been sent to **{os.environ["RDM_SERVER"]}**'
               f' if `--dry-run` were _not_ in effect.')
    console = Console()
    console.print(
        Panel(
            Markdown(comment),
            style='yellow',
            border_style='yellow',
            title='Note'
        )
    )
    print_json(data=record)


def alert(ctx, msg, print_usage=True):
    '''Print an error message in the style of rich_click.
    This is meant to be used when reporting errors involving UI options, in
    situations where rich_click's own error reporting can't be used directly.'''
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
    if print_usage:
        console.print(Padding(highlighter(ctx.get_usage()), 1))
    console.print(
        Panel(
            Markdown(msg),
            border_style=STYLE_ERRORS_PANEL_BORDER,
            title=ERRORS_PANEL_TITLE,
            title_align=ALIGN_ERRORS_PANEL,
        )
    )
