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
from iga.record import valid_record, record_for_release


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


def _read_param_value(ctx, param, value, env_var, purpose):
    '''Handle reading a CLI argument.

    If a value is passed on the command line, the environment variable
    env_var is set to the value, and the value is returned.

    If CLI argument value is None, the environment variable env_var is checked
    and if it has a value, it's returned; otherwise, this function prints an
    error message and exits with a status code signifying "bad argument".

    If the value is "help", this function prints help text and causes the
    program to exit.
    '''
    if ctx.params.get('url_or_tag', None) == 'help':
        print_help_and_exit(ctx)
    elif value:
        log(f'using {value} for the {purpose} passed on the command line')
        os.environ[env_var] = value
    elif env_var in os.environ:
        log(f'env var {env_var} is set; using it as the value for the {purpose}')
    else:
        opt = param.name.replace('_', '-')
        alert(ctx, f'Cannot proceed without a value for the {purpose}. (Tip:'
              f' use the `--{opt}` option or set the variable **{env_var}**.'
              ' For more information, use the option `--help`.)')
        sys.exit(int(ExitCode.bad_arg))
    return os.environ[env_var]


def _read_github_token(ctx, param, value):
    '''Read the file and set the environment variable GITHUB_TOKEN.'''
    return _read_param_value(ctx, param, value, 'GITHUB_TOKEN',
                             'GitHub personal access token')


def _read_invenio_token(ctx, param, value):
    '''Read the file and set the environment variable INVENIO_TOKEN.'''
    return _read_param_value(ctx, param, value, 'INVENIO_TOKEN',
                             'InvenioRDM personal access token')


def _read_server(ctx, param, value):
    '''Read the server address and set the environment variable INVENIO_SERVER.'''
    return _read_param_value(ctx, param, value, 'INVENIO_SERVER',
                             'InvenioRDM server address')


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
@click.option('--community', '-c', metavar='STR',
              help='ID of RDM community to update with item')
#
@click.option('--dry-run', '-n', is_flag=True,
              help='Print what would be created but do not create it')
#
@click.option('--file', '-f', 'given_files', metavar='FILE', multiple=True,
              help='File to upload (repeat for multiple files)')
#
@click.option('--github-account', '-a', metavar='STR',
              help='GitHub account name (if not using a release URL)')
#
@click.option('--github-repo', '-r', metavar='STR',
              help='GitHub repository name (if not using a release URL)')
#
@click.option('--github-token', '-g', metavar='STR', callback=_read_github_token,
              help="GitHub acccess token (avoid – use variable)")
#
@click.option('--invenio-server', '-s', metavar='URL', callback=_read_server,
              help='InvenioRDM server address')
#
@click.option('--invenio-token', '-t', metavar='STR', callback=_read_invenio_token,
              help="InvenioRDM access token (avoid – use variable)")
#
@click.option('--record', '-R', 'given_record', metavar='FILE', type=File('r'),
              help='Metadata record to use for the InvenioRDM entry')
#
@click.option('--version', '-V', callback=_print_version_and_exit, is_flag=True,
              help='Print version info and exit', expose_value=False, is_eager=True)
#
@click.option('--debug'  , '-@', metavar='DEST', type=File('w', lazy=False),
              callback=_config_debug, help='Write debug output to destination "DEST"')
#
@click.argument('url_or_tag', required=True)
@click.pass_context
def cli(ctx, url_or_tag, account=None, community=None, dry_run=False,
        given_files=None, given_record=None, repo=None, server=None,
        github_token=None, rdm_token=None,
        help=False, version=False, debug=False):  # noqa A002
    '''InvenioRDM GitHub Archiver (IGA) command-line interface.
\r
IGA retrieves a GitHub software release and archives it in an InvenioRDM
server. The release can be specified using _either_ a full URL, _or_ a GitHub
account + repository + tag combination (see below). By default, IGA constructs
a record based on information extracted from the GitHub repository; this can be
overriden by command-line options described below.
\r
_**Specification of the InvenioRDM server and access token**_
\r
The server address must be provided either as the value of the option
`--invenio-server` _or_ in an environment variable named `INVENIO_SERVER`.
\r
A Personal Access Token (PAT) for making API calls to the InvenioRDM server
must be also supplied when invoking IGA. The preferred way of doing that is to
set the value of the environment variable `INVENIO_TOKEN`. Alternatively, you
can use the option `--invenio-token` to pass the token on the command line, but
**you are strongly advised to avoid this practice because it is insecure**.
The option is provided for convenience during testing but should not be used
in production.
\r
To obtain a PAT from an InvenioRDM server, first log in to the server, then
visit the page at `/account/settings/applications` and use the interface there
to create a token.
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
Here's an example using approach #1 (assuming environment variables
INVENIO_SERVER, INVENIO_TOKEN, and GITHUB_TOKEN have all been set):
```
    iga https://github.com/mhucka/taupe/releases/tag/v1.2.0
```
and here's the equivalent using approach #2:
```
    iga --github-account mhucka --github-repo taupe v1.2.0
```
\r
_**Use of a GitHub access token**_
\r
It is possible to run IGA without providing a GitHub access token. GitHub
allows up to 60 API calls per minute when running without credentials, and
though IGA makes several API calls to GitHub each time it runs, for many
repositories, IGA will not hit the limit. However, if you run IGA multiple
times in a row or your repository has many contributors (IGA has to ask about
each contributor individually), then you may need to supply a GitHub access
token. The preferred way of doing that is to set the value of the environment
variable `GITHUB_TOKEN`. Alternatively, you can use the option
`--github-token` to pass the token on the command line, but **you are
strongly advised to avoid this practice because it is insecure**.  The option
is provided for convenience during testing but should not be used in
production.
\r
To obtain a PAT from GitHub, visit https://docs.github.com/en/authentication
and look for instructions about creating a "classic" personal access token.
\r
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
Running IGA with the option `--dry-run` will make it do the work of creating
a metadata record, but instead of creating an archive in the InvenioRDM server,
it will only print the record to the terminal.
\r
If given the `--version` option, this program will print its version and other
information, and exit without doing anything else.
\r
If given the `--debug` argument, IGA will output details about what it is
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
        alert(ctx, 'When not using a release URL, all of the following must be'
              ' provided: the options `--account`, `--repo`, and a tag name.')
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
        alert(ctx, 'No network; cannot proceed further.')
        sys.exit(int(ExitCode.no_network))

    # Do the main work ........................................................

    exit_code = ExitCode.success
    try:
        record = given_record or record_for_release(account, repo, tag)
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
               f' that _would_ have been sent to **{os.environ["INVENIO_SERVER"]}**'
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
