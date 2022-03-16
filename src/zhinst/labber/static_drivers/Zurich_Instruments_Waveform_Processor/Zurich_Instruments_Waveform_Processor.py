from enum import Enum
import typing as t

from BaseDriver import LabberDriver

from zhinst.utils import convert_awg_waveform, parse_awg_waveform
import numpy as np

Quantity = t.TypeVar("Quantity")


class Sources(Enum):
    """Signal Sources"""

    NONE = 0
    WAVES = 1
    INTERLEAVED = 2
    COMPLEX = 3


class Driver(LabberDriver):
    """This class implements a multi-qubit pulse generator."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._source = Sources.NONE

    # def performOpen(self, options={}):
    #     """Perform the operation of opening the instrument connection."""
    #     wave1 = np.array(0.5*np.ones(1008))
    #     wave2 = np.array(-0.6*np.ones(1008))
    #     self.setValue("Wave 1 - Signal", wave1)
    #     self.sendValueToOther("Wave 2 - Signal", wave2)
    #     test = self.getValue("Interleaved - Signal")
    #     print(test)

    def performSetValue(self, quant: Quantity, value: t.Any, **_):
        """Perform the Set Value instrument operation."""
        if quant.name == "Interleaved - Signal":
            self._source = Sources.INTERLEAVED
            return self._update_from_interleaved(quant, value)
        if self._source == Sources.INTERLEAVED and quant.name in [
            "Interleaved - Num - Channels",
            "Interleaved - Marker - Present",
        ]:
            return self._update_from_interleaved(quant, value)
        if quant.name == "Complex - Signal":
            self._source = Sources.COMPLEX
            return self._update_from_complex(quant, value)
        if quant.name in ["Wave 1 - Signal", "Wave 2 - Signal", "Marker - Signal"]:
            self._source = Sources.WAVES
            return self._update_from_waves(quant, value)
        return None

    def _update_from_interleaved(self, quant: Quantity, value: t.Any) -> None:
        """Update quants based on the interleaved waveform.

        Args:
            quant: Changed Quant
            value: New Value of quant
        """
        # get Values
        raw_wave = self._get_array("Interleaved - Signal", quant, value)
        channels = self._get_value("Interleaved - Num - Channels", quant, value)
        markers_present = self._get_value(
            "Interleaved - Marker - Present", quant, value
        )
        if raw_wave is None:
            return
        wave1, wave2, markers = parse_awg_waveform(
            raw_wave, channels=channels, markers_present=markers_present
        )
        complex_wave = np.empty(wave1.shape, dtype=np.complex128)
        complex_wave.real = wave1
        if wave2 is not None:
            complex_wave.imag = wave2
        self.setValue("Wave 1 - Signal", wave1)
        self.setValue("Wave 2 - Signal", wave2)
        self.setValue("Marker - Signal", markers)
        self.setValue("Complex - Signal", complex_wave)

    def _update_from_complex(self, quant, value):
        """Update quants based on the complex waveform.

        Args:
            quant: Changed Quant
            value: New Value of quant
        """
        complex_wave = self._get_array("Complex - Signal", quant, value)
        wave1 = complex_wave.real
        wave2 = complex_wave.imag
        markers = self.getValue("Marker - Signal")
        interleaved_waveform = convert_awg_waveform(
            wave1,
            wave2=wave2,
            markers=markers,
        )
        self.setValue("Wave 1 - Signal", wave1)
        self.setValue("Wave 2 - Signal", wave2)
        self.setValue("Interleaved - Signal", interleaved_waveform)

    def _update_from_waves(self, quant, value):
        """Update quants based on wave1 wave2 and marker.

        Args:
            quant: Changed Quant
            value: New Value of quant
        """
        wave1 = self._get_array("Wave 1 - Signal", quant, value)
        wave2 = self._get_array("Wave 2 - Signal", quant, value)
        markers = self._get_array("Marker - Signal", quant, value)
        if wave1 is not None:
            interleaved_waveform = convert_awg_waveform(
                wave1,
                wave2=wave2,
                markers=markers,
            )
            self.setValue("Interleaved - Signal", interleaved_waveform)

            complex_wave = np.empty(wave1.shape, dtype=np.complex128)
            complex_wave.real = wave1
            if wave2 is not None:
                complex_wave.imag = wave2
            self.setValue("Complex - Signal", complex_wave)

    def _get_value(
        self, quant_name: str, set_quant: Quantity, set_value: t.Any
    ) -> t.Any:
        """Get value for quant

        If the quant it not the current one it will be fetched.

        Args:
            quant_name: Name of the target quant.
            set_quant: Quant that is currently set.
            set_value: Value of the quant that is currently set.

        Returns:
            Value for the target quant
        """
        return set_value if set_quant.name == quant_name else self.getValue(quant_name)

    def _get_array(
        self, quant_name: str, set_quant: Quantity, set_value: t.Any
    ) -> t.Any:
        """Get array for quant

        If the quant it not the current one it will be fetched.

        Args:
            quant_name: Name of the target quant.
            set_quant: Quant that is currently set.
            set_value: Value of the quant that is currently set.

        Returns:
            array for the target quant
        """
        labber_value = self._get_value(quant_name, set_quant, set_value)
        return labber_value["y"] if labber_value["y"].size > 0 else None
