"""The Zurich Instruments Labber driver package (zhinst-labber)"""
try:
    from zhinst.labber._version import version as __version__
except ModuleNotFoundError:
    pass
from zhinst.labber.generator.generator import generate_labber_files
