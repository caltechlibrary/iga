# =============================================================================
# @file    test_cli.py
# @brief   Py.test cases for module command-line interface
# @created 2022-12-08
# @license Please see the file named LICENSE in the project directory
# @website https://github.com/caltechlibrary/iga
# =============================================================================

import click
import click.testing
import os

from iga.exit_codes import ExitCode


def test_no_args(capsys):
    from iga.cli import cli
    runner = click.testing.CliRunner()
    result = runner.invoke(cli)
    assert result.exit_code == int(ExitCode.bad_arg)


def test_unknown_arg(capsys):
    from iga.cli import cli
    runner = click.testing.CliRunner()
    result = runner.invoke(cli, ['--foo'])
    assert 'No such option' in result.output
    assert result.exit_code == int(ExitCode.bad_arg)


def test_help_flag(capsys):
    from iga.cli import cli
    runner = click.testing.CliRunner()
    result = runner.invoke(cli, ['--help'])
    assert 'Usage' in result.output
    assert result.exit_code == int(ExitCode.success)
    result = runner.invoke(cli, ['-h'])
    assert 'Usage' in result.output
    assert result.exit_code == int(ExitCode.success)


def test_help_arg(monkeypatch):
    from iga.cli import cli
    runner = click.testing.CliRunner()
    result = runner.invoke(cli, ['help'])
    assert result.exit_code == int(ExitCode.success)


def test_debug(capsys):
    from iga.cli import cli
    runner = click.testing.CliRunner()
    result = runner.invoke(cli, ['--debug'])
    assert 'requires an argument' in result.output
    assert result.exit_code == int(ExitCode.bad_arg)


def test_version(capsys):
    from iga.cli import cli
    runner = click.testing.CliRunner()
    result = runner.invoke(cli, ['--version'])
    assert 'version' in result.output
    assert result.exit_code == int(ExitCode.success)


def test_server(capsys):
    from iga.cli import cli
    runner = click.testing.CliRunner()
    result = runner.invoke(cli, ['--server', 'foo', '--token', '-', 'fakerecord'])
    assert result.exit_code == int(ExitCode.success)
    assert 'RDM_SERVER' in os.environ
    assert os.environ['RDM_SERVER'] == 'foo'


def test_token(capsys):
    from iga.cli import cli
    runner = click.testing.CliRunner()
    args = ['--server', 'foo', '--token', '-', 'fakerecord']
    result = runner.invoke(cli, args, input='faketoken')
    assert result.exit_code == int(ExitCode.success)
    assert 'RDM_TOKEN' in os.environ
    assert os.environ['RDM_TOKEN'] == 'faketoken'


def test_incomplete_file_arg(capsys):
    from iga.cli import cli
    runner = click.testing.CliRunner()
    result = runner.invoke(cli, ['-f'])
    assert 'requires an argument' in result.output
    assert result.exit_code == int(ExitCode.bad_arg)
