import tempfile
from unittest import mock
from unittest.mock import call
import pytest

from click.testing import CliRunner
from zhinst.labber.cli_script import main
from zhinst.labber import generate_labber_files


def test_cli_script_main():
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0


def test_cli_script_setup_help():
    runner = CliRunner()
    result = runner.invoke(main, ["setup", "--help"])
    assert result.exit_code == 0


@mock.patch(
    "zhinst.labber.cli_script.generate_labber_files",
    return_value=[["bar"], ["foo"]],
    wraps=generate_labber_files,
)
@pytest.mark.parametrize(
    "inp, outp",
    [
        (
            ["dev1234", "localhost"],
            {
                "device_id": "dev1234",
                "server_host": "localhost",
                "mode": "NORMAL",
                "upgrade": False,
                "server_port": None,
                "hf2": False,
            },
        ),
        (
            [
                "dev1234",
                "localhost",
                "--server_port=812",
                "--hf2",
                "--upgrade",
                "--mode=ADVANCED",
            ],
            {
                "device_id": "dev1234",
                "server_host": "localhost",
                "mode": "ADVANCED",
                "upgrade": True,
                "server_port": 812,
                "hf2": True,
            },
        ),
        (
            ["dev1234", "localhost", "--server_port=812"],
            {
                "device_id": "dev1234",
                "server_host": "localhost",
                "mode": "NORMAL",
                "upgrade": False,
                "server_port": 812,
                "hf2": False,
            },
        ),
    ],
)
def test_cli_script_setup(mock_gen, inp, outp):
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdirname:
        result = runner.invoke(main, ["setup", tmpdirname] + inp)
        calls = {"driver_directory": tmpdirname}
        calls.update(outp)
        mock_gen.assert_called_with(**calls)
        assert result.exit_code == 0
        assert (
            result.output == "Generating Zurich Instruments Labber device drivers...\n"
            "Generated file: bar\n"
            "Upgraded file: foo\n"
        )


@mock.patch("zhinst.labber.cli_script.generate_labber_files", return_value=[[], []])
def test_cli_script_no_files(mock_gen):
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdirname:
        result = runner.invoke(
            main, ["setup", tmpdirname, "dev1234", "localhost", "--server_port=812"]
        )
        assert result.exit_code == 0
        assert "Error: It appears that the driver already exists" in result.output


@mock.patch("zhinst.labber.cli_script.generate_labber_files")
def test_cli_script_setup_errors(mock_gen):
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdirname:
        command = ["setup"]
        result = runner.invoke(main, command)
        mock_gen.assert_not_called()
        assert result.exit_code == 2
        assert "Missing argument 'DRIVER_DIRECTORY'." in result.output

        command = ["setup", tmpdirname]
        result = runner.invoke(main, command)
        mock_gen.assert_not_called()
        assert result.exit_code == 2
        assert "Missing argument 'DEVICE_ID'." in result.output

        command = ["setup", tmpdirname, "dev123"]
        result = runner.invoke(main, command)
        mock_gen.assert_not_called()
        assert result.exit_code == 2
        assert "Error: Missing argument 'SERVER_HOST'." in result.output
