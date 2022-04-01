"""The Zurich Instruments Labber driver package (zhinst-labber)"""
try:
    from zhinst.labber._version import version as __version__
except ModuleNotFoundError:
    __version__ = "dev"
from zhinst.labber.generator import generate_labber_files
from zhinst.labber.helper import export_waveforms
