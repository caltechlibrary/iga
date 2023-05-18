'''
cli.py: command-line interface for IGA

This file is part of https://github.com/caltechlibrary/iga/.

Copyright (c) 2022-2023 by the California Institute of Technology.  This code
is open-source software released under a BSD-type license.  Please see the
file "LICENSE" for more information.
'''

import bdb
import os
import rich
from   rich.console import Console
from   rich.style import Style
import rich_click as click
from   rich_click import File, Path, INT, Choice
import sys
from   sidetrack import set_debug, log

from iga.exit_codes import ExitCode
from iga.exceptions import GitHubError, InvenioRDMError, RecordNotFound
from iga.github import (
    github_account_repo_tag,
    github_release_assets,
    valid_github_release_url,
)
from iga.id_utils import is_invenio_rdm
from iga.invenio import (
    invenio_api_available,
    invenio_communities,
    invenio_community_send,
    invenio_create,
    invenio_publish,
    invenio_server_name,
    invenio_token_valid,
    invenio_upload,
)


# Main command-line interface.
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# Style preferences for the Rich package ......................................

# The default sets the background color and I find the result too hard to read.
rich.default_styles.DEFAULT_STYLES['markdown.code'] = Style(bold=True, color="cyan")

# Style preferences for the rich-click package ................................

click.rich_click.STYLE_HELPTEXT = ""
click.rich_click.USE_MARKDOWN = True
click.rich_click.STYLE_ERRORS_SUGGESTION = "bold italic"
click.rich_click.ERRORS_EPILOGUE = "Suggestion: use the --help flag to get help."

# For some reason, the default style uses a different color for switches vs
# flags, which I find unhelpful and distracting. Make both the same.
click.rich_click.STYLE_SWITCH = 'bold cyan'


# Callback functions used in click interface ..................................

def _config_mode(ctx, param, mode):
    '''Handle the --mode option and configure the run mode as needed.'''
    os.environ['IGA_RUN_MODE'] = mode or 'normal'
    if mode in ['verbose', 'debug']:
        dest = os.environ.get('IGA_LOG_DEST') or '-'
        set_debug(True, dest, show_package=True)
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
    if ctx.params.get('url_or_tag') == 'help':
        _print_help_and_exit(ctx)
    elif value:
        log(f'using CLI option "--{param.name} {value}" for the {thing}')
        os.environ[env_var] = str(value).strip()
    elif env_var in os.environ:
        log(f"using value of environment variable {env_var} as the {thing}")
    elif required:
        opt = param.name.replace('_', '-')
        _alert(ctx, f'Cannot proceed without a value for the {thing}. (Tip:'
               f' use the `--{opt}` option or set the variable **{env_var}**.'
               ' For more information, use the option `--help`.)')
        sys.exit(int(ExitCode.bad_arg))
    else:
        log(f'environment variable {env_var} is not set')
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
    server = os.environ.get('INVENIO_SERVER', '').strip()

    # Do some basic checks on the value to prevent possibly misleading errors
    # later if we blindly tried to do an http 'post' on the given destination.
    if not server.startswith('http'):
        log(f'"{server}" is not a URL; will try to derive one')
        from iptools import ipv4, ipv6
        if ipv4.validate_ip(server):
            server = 'https://' + server
        elif ipv6.validate_ip(server):
            server = 'https://[' + server + ']'
        elif server.startswith('[') and server.endswith(']'):
            # This would imply an IPv6 address, but is it really?
            inner_value = server[1:-1]
            if ipv6.validate_ip(inner_value):
                server = 'https://' + server
            else:
                _alert(ctx, f'The value given to the --server option ({server})'
                       ' looks like an IPv6 address but {inner_value} fails'
                       ' IPv6 validation. Please check the value, or use a'
                       ' different address for the server. If you believe this'
                       ' is in error, please contact the developers of IGA.')
                sys.exit(int(ExitCode.bad_arg))
        else:
            # Not an IP address, so maybe it's a host name?
            from validators import domain
            if domain(server):
                server = 'https://' + server
            else:
                _alert(ctx, f'The given InvenioRDM server address ({server})'
                       ' does not appear to be a valid host or IP address.')
                sys.exit(int(ExitCode.bad_arg))
    if not invenio_api_available(server):
        _alert(ctx, f'The server address ({server}) does not appear to be'
               ' reacheable or does not support the InvenioRDM API.')
        sys.exit(int(ExitCode.bad_arg))
    if not invenio_token_valid(server):
        _alert(ctx, f'The personal access token was rejected by {server}.')
        sys.exit(int(ExitCode.bad_token))
    if name := invenio_server_name(server):
        os.environ['INVENIO_SERVER_NAME'] = name
        log(f'using {name} as the InvenioRDM publisher name')
    else:
        from commonpy.network_utils import hostname
        host_part = hostname(server)
        os.environ['INVENIO_SERVER_NAME'] = host_part
        log(f'unable to get a publisher name from the server; using {host_part}')
    log(f'using {server} as the InvenioRDM server address')
    os.environ['INVENIO_SERVER'] = server
    return result


def _read_timeout(ctx, param, value):
    '''Read the timeout value and perform some basic checks on it.'''
    if result := _read_param_value(ctx, param, value, 'IGA_NETWORK_TIMEOUT',
                                   'network timeout (in seconds)', required=False):
        # Click converts Python-style "_" separators so we don't worry about it.
        os.environ['IGA_NETWORK_TIMEOUT'] = result
        result = int(result)
        if result < 0 or result > 6000:
            _alert(ctx, 'The timeout value must be in the range 0-6000.')
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


def _print_text(text, color='turquoise4', end='\n', wrap=True):
    '''Print text to the console.

    If quiet mode is in effect or the log destination is not stdout, this does
    not print output to the console.
    '''
    log(text)
    if os.environ.get('IGA_RUN_MODE') == 'quiet':
        return
    if os.environ.get('IGA_LOG_DEST', '-') == '-':
        import shutil
        width = (shutil.get_terminal_size().columns - 2) or 78
        if wrap:
            from textwrap import wrap
            text = '\n'.join(wrap(text, width=width))
        console = Console(width=width)
        console.print(text, style=color, end=end, highlight=False)
    else:
        with open(os.environ.get('IGA_LOG_DEST'), 'a') as dest:
            console = Console(file=dest)
            console.print(text)


def _alert(ctx, msg, print_usage=True):
    '''Print an error message in the style of rich_click.

    This is meant to be used when reporting errors involving UI options, in
    situations where rich_click's own error reporting can't be used directly.
    '''
    if (os.environ.get('IGA_RUN_MODE') not in ['debug', 'verbose']
            and os.environ.get('IGA_LOG_DEST') not in ['-', None]):
        with open(os.environ.get('IGA_LOG_DEST'), 'a') as dest:
            console = Console(file=dest)
            console.print('Error: ' + msg)
    else:
        log('error: ' + msg)
    # The following code tries to emulate what rich_click does. It doesn't use
    # private methods or properties, but it might break if rich_click changes.
    from rich.markdown import Markdown
    from rich.padding import Padding
    from rich.panel import Panel
    from rich.theme import Theme
    from rich_click.rich_click import (
        ALIGN_ERRORS_PANEL,
        ERRORS_PANEL_TITLE,
        STYLE_ERRORS_PANEL_BORDER,
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
        "usage": 'gold3',
        'markdown.link': 'dodger_blue1',
        'markdown.link_url': 'dodger_blue3',
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
    '''Print an informative message to the console.'''
    # Detect URLs and convert them into Rich links.
    if contains_url := ('http' in text):
        import re
        if match := re.search(r'(https?://\S+)', text):
            ustart, uend = match.start(), match.end()
            url = text[ustart:uend]
            text = text[:ustart] + '[link=' + url + ']' + url + '[/]' + text[uend:]
    _print_text(text, 'turquoise4', end=end, wrap=(not contains_url))


def _quiet_or_redirected():
    '''Return true if the run mode is 'quiet' or the log dest is not '-'.'''
    return (os.environ.get('IGA_RUN_MODE') == 'quiet'
            or os.environ.get('IGA_LOG_DEST', '-') not in ['-', None])


def _list_communities(ctx, param, value):
    '''Get the list of InvenioRDM communities and print them to the console.'''
    if not value:
        return
    from rich import box
    from rich.table import Table
    server = os.environ.get('INVENIO_SERVER', '')
    table = Table(title=f'Communities available at server {server}',
                  pad_edge=True, box=box.MINIMAL_DOUBLE_HEAD, expand=True)
    table.add_column('Name', style='sky_blue2', no_wrap=True)
    table.add_column('Title', style='medium_turquoise')
    table.add_column('Web page', style='light_cyan3', no_wrap=False)
    try:
        for community in sorted(invenio_communities().values()):
            table.add_row(community.name, community.title,
                          f'[link={community.url}]{community.url}[/]')
        Console().print()
        Console().print(table)
    except KeyboardInterrupt:
        log('keyboard interrupt received')
        sys.exit(int(ExitCode.interrupt))
    except Exception as ex:             # noqa PIE786
        log('exception trying to list communities: ' + str(ex))
        _alert(ctx, 'Unable to get a list of communitities from the InvenioRDM'
               f' server at {server}. Please check the server address and the'
               ' condition of the network.')
        sys.exit(int(ExitCode.exception))
    sys.exit(int(ExitCode.success))


# Note #1: the default rich_click help feature does not offer a -h short form,
# hence the need to use our own explicit help_option() definition below.
#
# Note #2: The `\r` in the doc string below is a hack to introduce a blank
# lines between paragraphs. Rich_click version 1.6.0 collapses blank lines,
# which I hate.  This use of `\r` assumes the use of Markdown (as set above).

@click.command(add_help_option=False, no_args_is_help=True)
@click.option('--all-assets', '-A', is_flag=True,
              help='Attach all GitHub assets, not only a source ZIP')
#
@click.option('--all-metadata', '-M', is_flag=True,
              help='Be more comprehensive when gathering metadata')
#
@click.option('--community', '-c', metavar='STR',
              help='Submit record to the designated RDM community')
#
@click.option('--draft', '-d', is_flag=True,
              help='Mark the record as a draft; don\'t publish it')
#
@click.option('--file', '-f', 'files_to_upload', metavar='FILE', multiple=True,
              type=Path(exists=True), help='Upload _FILE_ (repeat for multiple files)')
#
@click.option('--github-account', '-a', 'account', metavar='STR',
              help='GitHub account name, if not using release URL')
#
@click.option('--github-repo', '-r', 'repo', metavar='STR',
              help='GitHub repository name, if not using release URL')
#
@click.option('--github-token', '-t', metavar='STR', callback=_read_github_token,
              help="GitHub acccess token (**avoid – use variable**)")
#
@click.help_option('--help', '-h', help='Show this help message and exit')
#
@click.option('--invenio-server', '-s', 'server', metavar='STR', callback=_read_server,
              help='InvenioRDM server address', is_eager=True)
#
@click.option('--invenio-token', '-k', metavar='STR', callback=_read_invenio_token,
              help="InvenioRDM access token (**avoid – use variable**)")
#
@click.option('--list-communities', '-L', is_flag=True, callback=_list_communities,
              help='List communities available for `--community`')
#
@click.option('--log-dest', '-l', metavar='FILE', callback=_config_log,
              type=File('w', lazy=False), expose_value=False, is_eager=True,
              help='Send log output to _FILE_ (use "`-`" for stdout)')
#
@click.option('--mode', '-m', metavar='STR', callback=_config_mode, is_eager=True,
              type=Choice(['normal', 'quiet', 'verbose', 'debug'], case_sensitive=False),
              help='Run mode: `quiet`, **`normal`**, `verbose`, `debug`')
#
@click.option('--open', '-o', 'open_in_browser', is_flag=True,
              help='Open the finished record in your web browser')
#
@click.option('--parent-record', '-p', 'parent_id', metavar='STR',
              help='Make this a new version of an existing record')
#
@click.option('--read-metadata', '-R', 'source', metavar='FILE', type=File('r'),
              help='Read metadata record from _FILE_; don\'t build one')
#
@click.option('--save-metadata', '-S', 'dest', metavar='FILE', type=File('w', lazy=False),
              help='Save metadata record to _FILE_; don\'t upload it')
#
@click.option('--timeout', '-T', metavar='NUM', type=INT, callback=_read_timeout,
              help='Wait on network operations a max of _NUM_ seconds')
#
@click.option('--version', '-V', callback=_print_version_and_exit, is_flag=True,
              help='Print IGA version and exit', expose_value=False, is_eager=True)
#
@click.argument('url_or_tag', required=True)
@click.pass_context
def cli(ctx, url_or_tag, all_assets=False, community=None, draft=False,
        files_to_upload=None, account=None, repo=None, github_token=None,
        server=None, invenio_token=None, list_communities=False,
        open_in_browser=False, log_dest=None, mode='normal', parent_id=None,
        all_metadata=False, source=None, dest=None, timeout=None,
        help=False, version=False):  # noqa A002
    '''InvenioRDM GitHub Archiver (IGA) command-line interface.
\r
IGA creates a metadata record in an InvenioRDM server and attaches a GitHub
release archive to the record. The GitHub release can be specified using
_either_ a full release URL, _or_ a combination of GitHub account + repository
\+ tag. Different command-line options can be used to adjust this behavior.
\r
_**Specification of the InvenioRDM server and access token**_
\r
The server address must be provided either as the value of the option
`--invenio-server` or in an environment variable named `INVENIO_SERVER`.
If the server address does not begin with "https://", IGA will prepended it
automatically.
\r
A Personal Access Token (PAT) for making API calls to the InvenioRDM server
must be also supplied when invoking IGA. The preferred method is to set the
value of the environment variable `INVENIO_TOKEN`. Alternatively, you can use
the option `--invenio-token` to pass the token on the command line, but **you
are strongly advised to avoid this practice because it is insecure**.
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
```shell
  iga https://github.com/mhucka/taupe/releases/tag/v1.2.0
```
and here's the equivalent using approach #2:
```shell
  iga --github-account mhucka --github-repo taupe v1.2.0
```
Note that when using this form of the command, the release tag ("v1.2.0" above)
must be the last item given on the command line.
\r
_**Use of a GitHub access token**_
\r
It is possible to run IGA without providing a GitHub access token. GitHub
allows up to 60 API calls per minute when running without credentials, and
though IGA makes several API calls to GitHub each time it runs, for many
repositories, IGA will not hit the limit. However, if you run IGA multiple
times in a row or your repository has many contributors, then you may need to
supply a GitHub access token. The preferred way of doing that is to set the
value of the environment variable `GITHUB_TOKEN`. Alternatively, you can use
the option `--github-token` to pass the token on the command line, but **you
are strongly advised to avoid this practice because it is insecure**.
To obtain a PAT from GitHub, visit https://docs.github.com/en/authentication
and follow the instructions for creating a "classic" personal access token.
\r
_**Construction of an InvenioRDM record**_
\r
The record created in InvenioRDM is constructed using information obtained
using GitHub's API as well as several other APIs as needed. The information
includes the following:
 * (if one exists) a `codemeta.json` file in the GitHub repository
 * (if one exists) a `CITATION.cff` file in the GitHub repository
 * data available from GitHub for the release
 * data available from GitHub for the repository
 * data available from GitHub for the account of the owner
 * data available from GitHub for the accounts of repository contributors
 * file assets associated with the GitHub release
 * data available from ORCID.org for ORCID identifiers
 * data available from ROR.org for Research Organization Registry identifiers
 * data available from DOI.org, NCBI, Google Books, & others for publications
 * data available from spdx.org for software licenses
\r
IGA tries to use `CodeMeta.json` first and `CITATION.cff` second to fill out
the fields of the InvenioRDM record. If neither of those files are present, IGA
uses values from the GitHub repository instead. You can make it always use all
sources of info with the option `--all-metadata`. Depending on how complete and
up-to-date your `CodeMeta.json` and `CITATION.cff` are, this may or may not
make the record more comprehensive and may or may not introduce redundancies or
unwanted values.
\r
To override the auto-created record, use the option `--read-record` followed
by the path to a JSON file structured according to the InvenioRDM schema used
by the destination server. When `--read-record` is provided, IGA does _not_
extract the data above, but still obtains the file assets from GitHub.
\r
_**Specification of GitHub file assets**_
\r
By default, IGA attaches to the InvenioRDM record _only_ the ZIP file asset
created by GitHub for the release. To make IGA attach all assets associated
with the GitHub release, use the option `--all-assets`.
\r
To upload specific file assets and override the default selections made by IGA,
you can use the option `--file` followed by a path to a file to be uploaded.
You can repeat the option `--file` to upload multiple file assets. Note that if
`--file` is provided, then IGA _does not use any file assets from GitHub_; it
is the user's responsibility to supply all the files that should be uploaded.
\r
If both `--read-record` and `--file` are used, then IGA does not actually
contact GitHub for any information.
\r
_**Handling communities**_
\r
To submit your record to a community, use the `--community` option together
with a community name. The option `--list-communities` can be used to get a
list of communities supported by the InvenioRDM server. Note that submitting a
record to a community means that the record will not be finalized and will not
be publicly visible when IGA finishes; instead, the record URL that you receive
will be for a draft version, pending review by the community moderators.
\r
_**Draft versus published records**_
\r
If the `--community` option is not used, then by default, IGA will finalize and
publish the record. To make it stop short and leave the record as a draft
instead, use the option `--draft`. The draft option also takes precedence over
the community option: if you use both `--draft` and `--community`, IGA will
stop after creating the draft record and will _not_ submit it to the community.
(You can nevertheless submit the record to a community manually once the draft
is created, by visiting the record's web page and using the InvenioRDM
interface there.)
\r
_**Versioning of records**_
\r
The option `--parent-record` can be used to indicate that the record being
constructed is a new version of an existing record. This will make IGA use the
InvenioRDM API for record versioning. The newly-created record will be linked
to a parent record identified by the value passed to `--parent-record`. The
value must be either an InvenioRDM record identifier (which is a sequence of
alphanumeric characters of the form _XXXXX-XXXXX_, such as `bknz4-bch35`,
generated by the InvenioRDM server), or a URL to the landing page of the record
in the InvenioRDM server. (Such URLs contain an embedded record identifier.)
Here is an example of using this option:
```shell
  iga --parent-record xbcd4-efgh5 https://github.com/foo/bar/releases/tag/v1
```
\r
_**Other options recognized by IGA**_
\r
Running IGA with the option `--save-record` will make it create a metadata
record, but instead of uploading the record (and any assets) to the InvenioRDM
server, IGA will write the result to the given destination. This can be useful
not only for debugging but also for creating a starting point for a custom
metadata record: first run IGA with `--save-record` to save a record to a file,
edit the result, then finally run IGA with the `--read-record` option to use
the modified record to create a release in the InvenioRDM server.
\r
The `--mode` option can be used to change the amount of diagnostic output. Four
modes are available: `quiet`, `normal`, `verbose`, and `debug`. The default is
`normal`, in which IGA prints only a few messages while it's working. The mode
`quiet` will make IGA avoid printing anything except the final record URL
unless an error occurs, the mode `verbose` will make it print a detailed trace
of what it is doing, and the mode `debug` will make IGA even more verbose. In
addition, in `debug` mode, IGA will drop into the `pdb` debugger if it
encounters an exception during execution. On Linux and macOS, debug mode also
installs a signal handler on signal USR1 that causes IGA to drop into the `pdb`
debugger if the signal USR1 is received. (Use `kill -USR1 NNN`, where NNN is
the IGA process id.)
\r
By default, the output of the `normal`, `verbose`, and `debug` run modes is
sent to the standard output (normally the terminal console). The option
`--log-dest` can be used to send the output to the given destination
instead. The value can be "`-`" to indicate console output, or a file path to
send the output to the file. A special exception is that even if a log
destination is given, IGA will still print the final record URL to stdout.
This makes it possible to invoke IGA from scripts that capture the record URL
while still saving diagnostic output in case debugging is needed. E.g.,
```shell
  record_url=`iga --mode verbose --log-dest iga.out ....`
```
\r
Networks latencies are unpredicatable. Reading and writing large files may take
a long time; on the other hand, IGA should not wait forever before reporting an
error if a server or network becomes unresponsive. To balance these conflicting
needs, IGA automatically scales its network timeout based on file sizes. To
override its adaptive algorithm and set an explicit timeout value, use the
option `--timeout` with a value in seconds.
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
  1 = interrupted  
  2 = encountered a bad or missing value for an option  
  3 = encountered a problem with a file or directory  
  4 = encountered a problem interacting with GitHub  
  5 = encountered a problem interacting with InvenioRDM  
  6 = the personal access token was rejected  
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

    if files_to_upload and all_assets:
        _alert(ctx, 'Option `--all-assets` cannot be used when using `--file`.')
        sys.exit(int(ExitCode.bad_arg))

    if community and community not in invenio_communities():
        _alert(ctx, f'"{community}" is not the name of a known community in'
               ' the InvenioRDM server. The known communities can be obtained'
               ' by using the option `--list-communities`.')
        sys.exit(int(ExitCode.file_error))

    if parent_id and not is_invenio_rdm(parent_id):
        _alert(ctx, f'"{parent_id}" does not appear to be an InvenioRDM'
               ' record identifier.')
        sys.exit(int(ExitCode.file_error))


    # Do the main work ........................................................

    from iga.metadata import metadata_for_release, metadata_from_file

    log(f'invoked with command line: {sys.argv}')
    exit_code = ExitCode.success
    try:
        record = None
        github_assets = []
        if source:
            _inform(f'Using {source.name} instead of building a record.')
            metadata = metadata_from_file(source)
            if metadata is None:
                _alert(ctx, f'The metadata structure in {source.name} is not valid.')
                sys.exit(int(ExitCode.file_error))
        else:
            _inform(f'Building record for {account}/{repo} release "{tag}"', end='...')
            metadata = metadata_for_release(account, repo, tag, all_metadata)
            github_assets = github_release_assets(account, repo, tag, all_assets)
            _inform(' done.')

        if dest:
            import json
            dest.write(json.dumps(metadata, indent=2))
            dest.write('\n')
            _inform(f'Wrote metadata to {dest.name}.')

            if open_in_browser:
                from os import path
                file = path.realpath(dest.name)
                log(f'opening {file}')
                click.launch(file)
        else:
            _inform('Sending metadata to InvenioRDM server', end='...')
            record = invenio_create(metadata, parent_id)
            _inform(' done.')

            _inform('Attaching assets:')
            for item in files_to_upload or github_assets:
                invenio_upload(record, item, _print_text)

            if draft:
                _inform(f'The draft record is available at {record.draft_url}')
            elif community:
                invenio_community_send(record, community)
                _inform(f'The record has been submitted to community "{community}"'
                        f' and the draft is available at {record.draft_url}')
            else:
                invenio_publish(record)
                _inform(f'The published record is available at {record.record_url}')

            if _quiet_or_redirected():
                # If no other output is printed, we still print the URL.
                click.echo(record.record_url or record.draft_url)
            if open_in_browser:
                log(f'opening {record.record_url or record.draft_url}')
                click.launch(record.record_url or record.draft_url)
    except KeyboardInterrupt:
        log('keyboard interrupt received')
        exit_code = ExitCode.user_interrupt
    except bdb.BdbQuit:
        # Exiting the debugger. Not a real exception.
        pass
    except Exception as ex:             # noqa: PIE786
        if isinstance(ex, GitHubError):
            _alert(ctx, f'Experienced an error interacting with GitHub: {ex}')
            exit_code = ExitCode.github_error
        elif isinstance(ex, InvenioRDMError):
            text = 'Experienced an error interacting with InvenioRDM.'
            if record:
                text += (' The partially-completed record can be found at'
                         f' [{record.draft_url}]({record.draft_url}). You'
                         ' may complete it manually, or delete it and try again.')
            if os.environ.get('IGA_RUN_MODE') in ['verbose', 'debug']:
                text += f'\n\nThe error is as follows: **{ex}**'
            _alert(ctx, text)
            exit_code = ExitCode.inveniordm_error
        elif isinstance(ex, RecordNotFound):
            _alert(ctx, f'Unable to continue. {str(ex)}.')
            exit_code = ExitCode.inveniordm_error
        else:
            import iga
            error_type = ex.__class__.__name__
            log(f'exiting due to {error_type}: {str(ex)}')
            _alert(ctx, 'IGA experienced an error. Please report this to the'
                   f' developers. Your version of IGA is {iga.__version__}.'
                   f' For information about how to report errors, please see'
                   f' {iga.__url__}/.\n\n{error_type}: {str(ex)}', False)
            exit_code = ExitCode.exception

        # If mode is debug, drop into pdb unless we're running as a GHA.
        if (os.environ.get('IGA_RUN_MODE') == 'debug'
                and 'GITHUB_ACTION' not in os.environ):
            import pdb
            import traceback
            exception = sys.exc_info()
            details = ''.join(traceback.format_exception(*exception))
            log(f'{ex.__class__.__name__}: ' + str(ex) + '\n\n' + details)
            Console().print_exception()
            pdb.post_mortem(exception[2])

    # Exit with status code ...................................................

    log(f'exiting with exit code {int(exit_code)}.')
    sys.exit(int(exit_code))
