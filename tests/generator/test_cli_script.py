import tempfile
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


@mock.patch("zhinst.labber.cli_script.generate_labber_files", return_value=[['bar'], ['foo']])
@pytest.mark.parametrize("inp, outp", [
    (
        ["dev1234", "localhost"], 
        {
            "device": "dev1234",
            "hf2": False,
            "mode": "NORMAL",
            "server_host": "localhost",
            "server_port": None,
            "upgrade": False
            }
    ),
    (
        ["dev1234", "localhost", "--server_port=812", "--hf2", "--upgrade", "--mode=ADVANCED"], 
        {
            "device": "dev1234",
            "hf2": True,
            "mode": "ADVANCED",
            "server_host": "localhost",
            "server_port": 812,
            "upgrade": True
            }
    ),
    (
        ["dev1234", "localhost", "--server_port=812"], 
        {
            "device": "dev1234",
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
    with tempfile.TemporaryDirectory() as tmpdirname:
        result = runner.invoke(main, ['setup', tmpdirname] + inp)
        outp['filepath'] = tmpdirname
        mock_gen.assert_called_with(**outp)
        assert result.exit_code == 0
        assert result.output == "Generating Zurich Instruments Labber device drivers...\n" \
        "Generated file: bar\n" \
        "Upgraded file: foo\n"


@mock.patch("zhinst.labber.cli_script.generate_labber_files", return_value=[[], []])
def test_cli_script_no_files(mock_gen):
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdirname:
        result = runner.invoke(main, ['setup', tmpdirname, "dev1234", "localhost", "--server_port=812"])
        assert result.exit_code == 0
        assert result.output == "Generating Zurich Instruments Labber device drivers...\n"


@mock.patch("zhinst.labber.cli_script.generate_labber_files")
def test_cli_script_setup_errors(mock_gen):
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdirname:
        command = ["setup"]
        result = runner.invoke(main, command)
        mock_gen.assert_not_called()
        assert result.exit_code == 2
        assert "Missing argument 'FILEPATH'." in result.output

        command = ["setup", tmpdirname]
        result = runner.invoke(main, command)
        mock_gen.assert_not_called()
        assert result.exit_code == 2
        assert "Missing argument 'DEVICE'." in result.output
        
        command = ["setup", tmpdirname, "dev123"]
        result = runner.invoke(main, command)
        mock_gen.assert_not_called()
        assert result.exit_code == 2
        assert "Error: Missing argument 'SERVER_HOST'." in result.output
