AWG Waveforms
=============

The following guide gives an overview of the waveform upload and usage within
the zhinst-labber drivers. The guide is valid for all instruments that have an
AWG core / generator.

CSV upload
-----------

The first way to upload a waveform through Labber is the upload via a CSV file.
A generator channel support the upload of a single complex waveform and the awg channel
allows the upload of 2 waves and markers.

The format of CSV file is the following:

* Each row represents one waveform
* Delimiter: ``,``
* If the waveform for the given index/slot should be ignored the respecive row
  can be empty.

To upload a waveform to index 0 and index 2 the CSV file could look like that

.. code-block:: csv

    0.0,0.1,0.2,0.3,0.2,0.1,0.0

    0.0,-0.1,-0.2,-0.3,-0.2,-0.1,0.0

zhinst-labber provides an easy way to generate the CSV files within python.
The function ``export_waveforms`` can be used to export a
``zhinst.toolkit.Waveforms`` object to one or multiple CSV files. The ``Waveforms``
class is a dictionary like class. The keys represent the awg index and the value
can either be a single waveform or 2 waveforms and an optional marker. Take
a look at the respective toolkit `example <https://docs.zhinst.com/zhinst-toolkit/en/latest/examples/hdawg_awg.html#Write-the-waveforms-into-the-device-memory>`_
to see an in-depth introduction into the ``Waveforms`` class.

AWG Waveform export example:

.. code-block:: python

    from zhinst.toolkit import Waveforms
    from zhinst.labber import export_waveforms
    from pathlib import Path
    import numpy as np

    waveforms = Waveforms()
    waveforms.assign_waveform(
        slot=1,
        wave1=np.sin(np.linspace(0, 2 * np.pi, 1000)
        wave2=np.cos(np.linspace(0, 2 * np.pi, 1000))
        marker=np.ones(1000)
    )
    waveforms.assign_waveform(
        slot=3,
        wave1=-1.0 * np.blackman(1000)
    )
    export_waveforms(waveforms, Path("generated_waveforms"))

complex generator Waveform export example:

.. code-block:: python

    from zhinst.toolkit import Waveforms
    from zhinst.labber import export_waveforms
    from pathlib import Path
    import numpy as np

    complex_wave = np.zeros(1000, dtype=complex)
    complex_wave.real = np.sin(np.linspace(0, 2 * np.pi, 1000))
    complex_wave.imag = np.cos(np.linspace(0, 2 * np.pi, 1000))
    waveforms = Waveforms()
    waveforms.assign_waveform(
        slot=1,
        wave1=complex_wave
    )
    waveforms.assign_waveform(
        slot=3,
        wave1=-complex_wave
    )
    export_waveforms(waveforms, Path("generated_waveforms"))

Wavefrom Processor upload
--------------------------

Often the waveforms for specific applications can be generated within another
instrument in Labber (e.g. SingleQubitPulseGenerator). Since the Waveform Nodes
of the AWG format have a special format one can not directly connect the two
Quantities directly.

To be able to do this zhinst-labber also provides a virtual Instrument called
``Zurich_Instruments_Waveform_Processor``
