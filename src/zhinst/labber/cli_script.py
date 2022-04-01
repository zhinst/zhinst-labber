import click

from zhinst.labber import generate_labber_files


@click.group()
def main():
    """A command line application to generate Zurich Instruments Labber drivers.

    The drivers include a settings file, configuration file (.ini) and a generated
    Python driver code for Zurich Instruments devices and modules."""


@main.command()
@click.argument(
    "driver_directory",
    required=True,
    type=click.Path(exists=True),
)
@click.argument(
    "device_id",
    required=True,
    type=str,
)
@click.argument(
    "server_host",
    required=True,
    type=str,
)
@click.option(
    "--server_port",
    required=False,
    type=int,
    help="Zurich Instruments Data Server port",
)
@click.option("--hf2", required=False, is_flag=True, help="HF2 Dataserver")
@click.option(
    "--mode",
    required=False,
    type=click.Choice(["NORMAL", "ADVANCED"], case_sensitive=False),
    default="NORMAL",
    help="""Select labber configuration mode.

    NORMAL:

        The most important nodes and functions are visible in the Labber GUI.

    ADVANCED:

        Most of the nodes and functions are visible. The mode opens new
    functionalities, but also increases complexity.
    """,
)
@click.option(
    "--upgrade",
    required=False,
    is_flag=True,
    help="""Upgrade existing drivers.

    It is recommended to use this option when Zurich instruments LabOne or device
    has it's version, option or any other configuration changed, that can affect the device
    functionality or nodes.
    """,
)
def setup(driver_directory, device_id, server_host, server_port, hf2, mode, upgrade):
    """Generate Zurich Instruments Labber drivers.

    This script generates the necessary files to control Zurich Instruments
    devices with Labber. The script generates a Labber driver based on the current
    status of the selected Zurich Instruments DataServer, device and modules.

    DRIVER_DIRECTORY: Directory where the drivers are saved. Usually in the Labber Driver-directory.

    DEVICE_ID: Zurich Instruments device ID

    SERVER_HOST: Server host

    Example:

    >>> zhinst-labber setup C:/Labber/Drivers DEV1234 localhost
    """
    click.echo("Generating Zurich Instruments Labber device drivers...")
    generated, upgraded = generate_labber_files(
        driver_directory=driver_directory,
        device_id=device_id,
        server_host=server_host,
        mode=mode.upper(),
        upgrade=upgrade,
        server_port=server_port,
        hf2=hf2,
    )
    if not upgrade and not generated:
        click.echo(
            "Error: It appears that the driver already exists. "
            "Please delete the files manually or "
            "use --upgrade options to overwrite the existing drivers."
        )
    for file in generated:
        click.echo(f"Generated file: {file}")
    for file in upgraded:
        click.echo(f"Upgraded file: {file}")
