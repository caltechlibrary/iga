'''
cli.py: command-line interface for IGA

This file is part of https://github.com/caltechlibrary/iga/.

Copyright (c) 2022 by the California Institute of Technology.  This code
is open-source software released under a BSD-type license.  Please see the
file "LICENSE" for more information.
'''

import bdb
import os
import rich_click as click
from   rich_click import File
import sys
from   sidetrack import set_debug, log

from iga.exit_codes import ExitCode
from iga.exceptions import GitHubError, InvenioRDMError
from iga.github import valid_github_release_url, github_account_repo_tag
from iga.invenio import invenio_write
from iga.record import record_for_release, record_from_file


# Main command-line interface.
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# Style preferences for rich_click module .....................................

click.rich_click.STYLE_HELPTEXT = ""
click.rich_click.USE_MARKDOWN = True
click.rich_click.STYLE_ERRORS_SUGGESTION = "bold italic"
click.rich_click.ERRORS_EPILOGUE = "Suggestion: use the --help flag to get help."


# Callback functions used in click interface ..................................

def _config_mode(ctx, param, mode):
    '''Handle the --mode option and configure the run mode as needed.'''
    mode = 'normal' if mode is None else mode.lower()
    if mode not in ['quiet', 'normal', 'verbose', 'debug']:
        _alert(ctx, f'Unrecognized mode: "{mode}". The mode value must be'
               ' chosen from `quiet`, `normal`, `verbose`, or `debug`. Please'
               ' use `--help` for more information.')
        sys.exit(int(ExitCode.bad_arg))
    os.environ['IGA_RUN_MODE'] = mode
    if mode in ['verbose', 'debug']:
        set_debug(True)
    if mode == 'debug':
        import faulthandler
        faulthandler.enable()
        if os.name != 'nt':                 # Can't use next part on Windows.
            import signal
            from boltons.debugutils import pdb_on_signal
            pdb_on_signal(signal.SIGUSR1)
    return mode


def _config_log(ctx, param, log_dest):
    '''Handle the --log option and configure settings as needed.'''
    if not log_dest:
        return None

    if log_dest.name == 'og':
        # The user almost certainly typed "-log" instead of "--log".
        _alert(ctx, 'No such option: `-log`. Did you mean `--log`?')
        sys.exit(int(ExitCode.bad_arg))
    elif log_dest.name == '<stdout>':
        dest = '-'
    else:
        dest = log_dest.name

    if os.environ.get('IGA_RUN_MODE', 'normal') in ['verbose', 'debug']:
        set_debug(True, dest)
        os.environ['IGA_LOG_DEST'] = dest
    return dest


def _read_param_value(ctx, param, value, env_var, thing, required=True):
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
        _print_help_and_exit(ctx)
    elif value:
        log(f'using CLI option "--{param.name} {value}" for the {thing}')
        os.environ[env_var] = value
    elif env_var in os.environ:
        log(f"using value of environment variable {env_var} as the {thing}")
    elif required:
        opt = param.name.replace('_', '-')
        _alert(ctx, f'Cannot proceed without a value for the {thing}. (Tip:'
               f' use the `--{opt}` option or set the variable **{env_var}**.'
               ' For more information, use the option `--help`.)')
        sys.exit(int(ExitCode.bad_arg))
    else:
        log(f'environment variable {env_var} not set')
    return os.environ[env_var] if env_var in os.environ else None


def _read_github_token(ctx, param, value):
    '''Read the file and set the environment variable GITHUB_TOKEN.'''
    return _read_param_value(ctx, param, value, 'GITHUB_TOKEN',
                             'GitHub personal access token', required=False)


def _read_invenio_token(ctx, param, value):
    '''Read the file and set the environment variable INVENIO_TOKEN.'''
    return _read_param_value(ctx, param, value, 'INVENIO_TOKEN',
                             'InvenioRDM personal access token')


def _read_server(ctx, param, value):
    '''Read the server address & set the environment variable INVENIO_SERVER.'''
    result = _read_param_value(ctx, param, value, 'INVENIO_SERVER',
                               'InvenioRDM server address')
    server = os.environ.get('INVENIO_SERVER', '')
    # Do some basic checks on the value to prevent possibly misleading errors
    # later if we blindly tried to do an http 'post' on the given destination.
    if not server.startswith('http'):
        from iptools import ipv4, ipv6
        if not ipv4.validate_ip(server) and not ipv6.validate_ip(server):
            from validators import domain
            if domain(server):
                os.environ['INVENIO_SERVER'] = 'https://' + server
                log(f'modifying the supplied InvenioRDM server address'
                    f' ({server}) to prepend https://')
            else:
                _alert(ctx, f'The given InvenioRDM server address ({server})'
                       ' does not appear to be a valid host or IP address.')
                sys.exit(int(ExitCode.bad_arg))
    return result


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


def _print_help_and_exit(ctx):
    '''Print the help text and exit with a success code.'''
    click.echo(ctx.get_help())
    sys.exit(int(ExitCode.success))


def _print_text(text, color, end='\n'):
    import shutil
    from rich.console import Console
    from textwrap import wrap
    width = (shutil.get_terminal_size().columns - 2) or 78
    console = Console(width=width)
    console.print('\n'.join(wrap(text, width=width)), style=color, end=end)


def _alert(ctx, msg, print_usage=True):
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


def _inform(text, end='\n'):
    log('[inform] ' + text)
    if os.environ.get('IGA_RUN_MODE') != 'quiet':
        _print_text(text, 'green', end=end)


# Note #1: the default rich_click help feature does not offer a -h short form,
# hence the need to use our own explicit help_option() definition below.
#
# Note #2: The `\r` in the doc string below is a hack to introduce a blank
# lines between paragraphs. Rich_click version 1.6.0 collapses blank lines,
# which I hate.  This use of `\r` assumes the use of Markdown (as set above).

@click.command(add_help_option=False)
@click.option('--community', '-c', metavar='STR',
              help='Send record to the RDM community with the given ID')
#
@click.option('--file', '-f', 'given_files', metavar='FILE', multiple=True,
              help='File to upload (repeat for multiple files)')
#
@click.option('--github-account', '-a', 'account', metavar='STR',
              help='GitHub account name (if not using a release URL)')
#
@click.option('--github-repo', '-r', 'repo', metavar='STR',
              help='GitHub repository name (if not using a release URL)')
#
@click.option('--github-token', '-g', metavar='STR', callback=_read_github_token,
              help="GitHub acccess token (avoid – use variable)")
#
@click.help_option('--help', '-h', help='Show this message and exit')
#
@click.option('--invenio-server', '-s', 'server', metavar='STR', callback=_read_server,
              help='InvenioRDM server address')
#
@click.option('--invenio-token', '-t', metavar='STR', callback=_read_invenio_token,
              help="InvenioRDM access token (avoid – use variable)")
#
@click.option('--log-dest', '-l', metavar='FILE', type=File('w', lazy=False),
              expose_value=False, callback=_config_log, is_eager=True,
              help='Send log output to FILE (use "-" for stdout)')
#
@click.option('--mode', '-m', metavar='STR', callback=_config_mode, is_eager=True,
              help='Run mode: "quiet", "normal", "verbose", or "debug"')
#
@click.option('--record-dest', '-o', metavar='FILE', type=File('w', lazy=False),
              help='Save the metadata record to FILE; don\'t upload it')
#
@click.option('--source-record', '-u', 'source', metavar='FILE', type=File('r'),
              help='Use the given metadata record; don\'t build one')
#
@click.option('--version', '-V', callback=_print_version_and_exit, is_flag=True,
              help='Print version info and exit', expose_value=False, is_eager=True)
#
@click.argument('url_or_tag', required=True)
@click.pass_context
def cli(ctx, url_or_tag, community=None, given_files=None,
        account=None, repo=None, github_token=None,
        server=None, invenio_token=None,
        log_dest=None, mode='normal', record_dest=None, source=None,
        help=False, version=False):  # noqa A002
    '''InvenioRDM GitHub Archiver (IGA) command-line interface.
\r
By default, IGA creates a metadata record for a GitHub software release
and uploads it along with the release assets to a designated InvenioRDM server.
The GitHub release can be specified using _either_ a full release URL, _or_ a
combination of GitHub account + repository + tag. Different command-line
options can be used to adjust this behavior.
\r
_**Specification of the InvenioRDM server and access token**_
\r
The server address must be provided either as the value of the option
`--invenio-server` _or_ in an environment variable named `INVENIO_SERVER`.
If the server address does not begin with "https://", IGA will prepended it
automatically.
\r
A Personal Access Token (PAT) for making API calls to the InvenioRDM server
must be also supplied when invoking IGA. The preferred method is to set the
value of the environment variable `INVENIO_TOKEN`. Alternatively, you can use
the option `--invenio-token` to pass the token on the command line, but **you
are strongly advised to avoid this practice because it is insecure**.  The
option is provided for convenience during testing but should never be used in
production.
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
is provided for convenience during testing but should never be used in
production.
\r
To obtain a PAT from GitHub, visit https://docs.github.com/en/authentication
and follow the instructions for creating a "classic" personal access token.
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
To override the auto-created record, use the option `--source-record` followed
by the path to a JSON file structured according to the InvenioRDM schema used
by the destination server. When `--source-record` is provided, IGA does _not_
extract the data above, but still obtains the file assets from GitHub.
\r
_**Specification of GitHub file assets**_
\r
By default, IGA attaches to the InvenioRDM record all file assets associated
with the software release in GitHub. To override which file assets are attached
to the InvenioRDM record, you can use the option `--file` followed by a path to
a file to be uploaded. The option `--file` can be repeated to upload multiple
file assets. Note that if `--file` is provided, then IGA does not use any
file assets from GitHub; it is the user's responsibility to supply all the
files that should be uploaded.
\r
If _both_ `--source-record` and `--file` are used, then IGA does not actually
contact GitHub for any information.
\r
_**Other options recognized by IGA**_
\r
Running IGA with the option `--record-dest` will make it create a metadata
record, but instead of uploading the record (and any assets) to the InvenioRDM
server, IGA will output the result to the given destination. This can be useful
not only for debugging but also for creating a starting point for a custom
metadata record: first run IGA with `--record-dest` to save a record to a file,
edit the result, then finally run IGA with the `--source-record` option to use
the modified record to create a release in the InvenioRDM server.
\r
The `--mode` option can be used to change the run mode. Four run modes are
available: `quiet`, `normal`, `verbose`, and `debug`. The default mode is
`normal`, in which IGA prints a few messages while it's working. The mode
`quiet` will make it avoid printing anything unless an error occurs, the mode
`verbose` will make it print a detailed trace of what it is doing, and the
mode `debug` will make IGA even more verbose. In addition, in `debug` mode,
IGA will drop into the `pdb` debugger if it encounters an exception during
execution. On Linux and macOS, debug mode also installs a signal handler on
signal USR1 that causes IGA to drop into the `pdb` debugger if the signal
USR1 is received. (Use `kill -USR1 NNN`, where NNN is the IGA process id.)
\r
By default, the output of the `verbose` and `debug` run modes is sent to the
standard output (normally the terminal console). The option `--log-dest` can
be used to send the output to the given destination instead. The value can be
`-` to indicate console output, or a file path to send the output to the file.
\r
If given the `--version` option, this program will print its version and other
information, and exit without doing anything else.
\r
Running IGA with the option `--help` will make it print help text and exit
without doing anything else.
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
  7 = an exception or fatal error occurred  
'''
    # Process arguments & handle early exits ..................................

    if url_or_tag == 'help':  # Detect if the user typed "help" without dashes.
        _print_help_and_exit(ctx)
    elif url_or_tag.startswith('http'):
        if any([account, repo]):
            _alert(ctx, 'The use of a URL and the use of options `--account`'
                   " and `--repo` are mutually exclusive; can't use both.")
            sys.exit(int(ExitCode.bad_arg))
        elif not valid_github_release_url(url_or_tag):
            _alert(ctx, 'Malformed release URL: ' + str(url_or_tag))
            sys.exit(int(ExitCode.bad_arg))
        else:
            account, repo, tag = github_account_repo_tag(url_or_tag)
    elif not all([account, repo, url_or_tag]):
        _alert(ctx, 'When not using a release URL, all of the following must be'
               ' provided: the options `--account`, `--repo`, and a tag name.')
        sys.exit(int(ExitCode.bad_arg))
    else:
        tag = url_or_tag

    from commonpy.network_utils import network_available
    if not network_available():
        _alert(ctx, 'No network; cannot proceed further.')
        sys.exit(int(ExitCode.no_network))

    # Do the main work ........................................................

    exit_code = ExitCode.success
    try:
        if source:
            record = record_from_file(source)
            if record is None:
                _alert(ctx, 'Record not in valid format: ' + source.name)
                sys.exit(int(ExitCode.file_error))
            _inform(f'Using {source.name} instead of building a record.')
        else:
            _inform(f'Building record for {account}/{repo} release "{tag}"', end='...')
            record = record_for_release(account, repo, tag)
            if record is None:
                _alert(ctx, f'Failed to construct record for release "{tag}"'
                       f' in repository "{repo}" of GitHub account "{account}".')
                sys.exit(int(ExitCode.github_error))
            _inform(' done.')

        if record_dest:
            import json
            record_dest.write(json.dumps(record, indent=2))
            record_dest.write('\n')
            _inform(f'Wrote metadata record to {record_dest.name}')
        else:
            _inform(f'Sending record to {os.environ["INVENIO_SERVER"]} ...')
            invenio_write(record)
            _inform('Done.')
    except KeyboardInterrupt:
        # Catch it, but don't treat it as an error; just stop execution.
        log('keyboard interrupt received')
        exit_code = ExitCode.user_interrupt
    except bdb.BdbQuit:
        # Exiting the debugger will do this. Ignore it.
        pass
    except Exception as ex:             # noqa: PIE786
        exit_code = ExitCode.exception
        if isinstance(ex, GitHubError):
            exit_code = ExitCode.github_error
        elif isinstance(ex, InvenioRDMError):
            exit_code = ExitCode.inveniordm_error

        if os.environ.get('IGA_DEBUG_MODE', 'False') == 'True':
            import rich
            import traceback
            exception = sys.exc_info()
            details = ''.join(traceback.format_exception(*exception))
            log(f'{ex.__class__.__name__}: ' + str(ex) + '\n\n' + details)
            rich.console.Console().print_exception(show_locals=True)
            import pdb
            pdb.post_mortem(exception[2])
        else:
            import iga
            error_type = ex.__class__.__name__
            _alert(ctx, 'IGA experienced an error. Please report this to the'
                   f' developers. This version of IGA is {iga.__version__}.'
                   f' For information about how to report errors, please see'
                   f' {iga.__url__}/.\n\n{error_type}: {str(ex)}', False)

    # Exit with status code ...................................................

    log(f'exiting with exit code {int(exit_code)}.')
    sys.exit(int(exit_code))
