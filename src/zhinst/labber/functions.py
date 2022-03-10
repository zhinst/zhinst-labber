"""Translates between Labber and a toolkit function."""
from pathlib import Path
import numpy as np
from enum import Enum
import csv
from itertools import repeat
import inspect
import typing as t


from zhinst.toolkit import Waveforms

NumpyArray = t.TypeVar("NumpyArray")
Instrument = t.TypeVar("Instrument")

FUNCTIONPOSTFIX = "EXECUTEFUNC"


class QuantType(Enum):
    """Supported quant types Types."""

    GENERIC = 0
    SEQUENCER = 1
    WAVEFORM = 2


def _csv_row_to_vector(csv_row: t.List[str]) -> t.Optional[NumpyArray]:
    """Convert a csv row into a numpy array.

    Args:
        csv_row: Parsed CSV row
    Returns:
        Numpy array.
    """
    if not csv_row:
        return None
    datatype = type(eval(csv_row[0]))
    return np.array(csv_row[:-1], dtype=datatype.__name__)


def _import_waveforms(
    wave1: Path, wave2: Path = None, marker: Path = None
) -> Waveforms:
    """Import Waveforms from CSV files.

    Args:
        wave1: csv for real part waves
        wave2: csv for imag part waves
        marker: csv for markers

    Returns:
        Waveform object
    """
    wave1_reader = csv.reader(wave1.open("r", newline=""), delimiter=",", quotechar="|")
    wave2_reader = repeat([])
    if wave2 and wave2.exists():
        wave2_reader = csv.reader(
            wave2.open("r", newline=""), delimiter=",", quotechar="|"
        )
    marker_reader = repeat([])
    if marker and marker.exists():
        marker_reader = csv.reader(
            marker.open("r", newline=""), delimiter=",", quotechar="|"
        )

    waves = Waveforms()
    for i, row in enumerate(zip(wave1_reader, wave2_reader, marker_reader)):
        if not row[0]:
            continue
        waves[i] = (
            _csv_row_to_vector(row[0]),
            _csv_row_to_vector(row[1]),
            _csv_row_to_vector(row[2]),
        )
    return waves


def get_waveform_arg_names(function):
    arg_names = []
    for key, value in inspect.signature(function).parameters.items():
        if "waveform.Waveforms" in str(value.annotation):
            arg_names.append(key)
    return arg_names

def _process_function_returns(function, *args):
    name = function.__name__
    if name == "test":
        return None
    return args

def execute_function(
    function_group: str, instrument: Instrument, all_quants: t.List
) -> t.Any:
    """Execute a toolkit function.

    Args:
        function_group: Labber group of the function.
        instrument: instrument of the function.
        all_quants: all available quants.
    """

    # get function object
    function = instrument
    for name in function_group.lower().split(" - "):
        if name.isnumeric():
            function = function[int(name)]
        else:
            function = getattr(function, name)

    # get arguments
    arg_quant = []
    waveform_count = 0
    for other_quant in all_quants.values():
        if function_group == other_quant.group and FUNCTIONPOSTFIX not in name:
            quant_type = QuantType.GENERIC
            if other_quant.datatype == other_quant.PATH:
                if "csv" in other_quant.set_cmd:
                    quant_type = QuantType.WAVEFORM
                    waveform_count += 1
                else:
                    quant_type = QuantType.SEQUENCER
            arg_quant.append[(other_quant, quant_type)]

    if waveform_count not in [0, 1, 3]:
        raise RuntimeError(f"Invalid amount of waveform paths. {waveform_count}")

    # get argument values
    kwargs = {}
    waveform_paths = []
    for other_quant, quant_type in arg_quant:
        arg_name = other_quant.name.lower().split(" - ")[-1]
        if quant_type == QuantType.SEQUENCER:
            with Path(other_quant.getValue()).open("r") as file:
                kwargs[arg_name] = file.read()
        elif quant_type == QuantType.WAVEFORM:
            waveform_paths.append(Path(other_quant.getValue()))
            if len(waveform_paths) == waveform_count:
                # TODO only one Waveform argument per function call supported
                arg_names = get_waveform_arg_names(function)
                kwargs[arg_names[0]] = _import_waveforms(*waveform_paths)
        else:
            kwargs[arg_name] = other_quant.getValue()
    return _process_function_returns(function, function(**kwargs))

