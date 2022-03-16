import click
from zhinst.labber import generate_labber_files


@click.group()
def main():
    """A command line application to generate Zurich Instruments Labber drivers.

    The drivers include a settings file, configuration file (.ini) and a generated
    Python driver code for Zurich Instruments devices and modules."""
    pass

@main.command()
@click.argument(
    "filepath",
    required=True,
    type=click.Path(exists=True),
)
@click.argument(
    "device",
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
    help='Zurich Instruments Data Server port'
)
@click.option(
    "--hf2",
    required=False,
    is_flag=True,
    help='HF2 Dataserver'
)
@click.option(
    "--mode",
    required=False,
    type=click.Choice(['NORMAL', 'ADVANCED'], case_sensitive=False),
    default='NORMAL',
    help='''Select labber configuration mode.

    NORMAL:

        The most important nodes and functions are visible in the Labber GUI.

    ADVANCED:

        Most of the nodes and functions are visible. The mode opens new
    functionalities, but also increases complexity.
    '''
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
def setup(filepath, device, server_host, server_port, hf2, mode, upgrade):
    """Generate Zurich Instruments Labber drivers.

    This script generates the necessary files to control Zurich Instruments 
    devices with Labber. The script generates a Labber driver based on the current 
    status of the selected Zurich Instruments DataServer, device and modules.

    FILEPATH: Filepath where the files are saved. Usually in the Labber Driver-directory.

    DEVICE: Zurich Instruments device ID

    SERVER_HOST: Server host
    
    Example:

    >>> zhinst-labber setup C:/Labber/Drivers DEV1234 localhost
    """
    generate_labber_files(
        filepath=filepath,
        mode=mode.upper(),
        device=device,
        server_host=server_host,
        upgrade=upgrade,
        server_port=server_port,
        hf2=hf2
    )
