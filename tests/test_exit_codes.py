from iga.exit_codes import ExitCode


def test_exitcode():
    assert int(ExitCode.success) == 0
    assert ExitCode.success.meaning == "success – program completed normally"
