from unittest import mock
import pytest

from click.testing import CliRunner
from zhinst.labber.cli_script import main


def test_cli_script_main():
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0


def test_cli_script_setup_help():
    runner = CliRunner()
    result = runner.invoke(main, ["setup", "--help"])
    assert result.exit_code == 0


@mock.patch("zhinst.labber.cli_script.generate_labber_files")
@pytest.mark.parametrize("inp, outp", [
    (
        ["setup", "../tests", "dev1234", "localhost"], 
        {
            "device": "dev1234",
            "filepath": "../tests",
            "hf2": False,
            "mode": "NORMAL",
            "server_host": "localhost",
            "server_port": None,
            "upgrade": False
            }
    ),
    (
        ["setup", "../tests", "dev1234", "localhost", "--server_port=812", "--hf2", "--upgrade", "--mode=ADVANCED"], 
        {
            "device": "dev1234",
            "filepath": "../tests",
            "hf2": True,
            "mode": "ADVANCED",
            "server_host": "localhost",
            "server_port": 812,
            "upgrade": True
            }
    ),
    (
        ["setup", "../tests", "dev1234", "localhost", "--server_port=812"], 
        {
            "device": "dev1234",
            "filepath": "../tests",
            "hf2": False,
            "mode": "NORMAL",
            "server_host": "localhost",
            "server_port": 812,
            "upgrade": False
        }
    ),
])
def test_cli_script_setup(mock_gen, inp, outp):
    runner = CliRunner()
    result = runner.invoke(main, inp)
    mock_gen.assert_called_with(**outp)
    assert result.exit_code == 0


@mock.patch("zhinst.labber.cli_script.generate_labber_files")
@pytest.mark.parametrize("inp, err_code, output", [
    (
        ["setup"], 
        2,
        "Missing argument 'FILEPATH'."
    ),
    (
        ["setup", "../tests"], 
        2,
        "Missing argument 'DEVICE'."
    ),
    (
        ["setup", "../tests", "dev1234"], 
        2,
        "Error: Missing argument 'SERVER_HOST'."
    ),
])
def test_cli_script_setup_errors(mock_gen, inp, err_code, output):
    runner = CliRunner()
    result = runner.invoke(main, inp)
    mock_gen.assert_not_called()
    assert result.exit_code == err_code
    assert output in result.output
