AWG Waveforms
=============

The following guide gives an overview of the waveform upload and usage within
the zhinst-labber drivers. The guide is valid for all instruments that have an
AWG core / generator.

.. _csv_upload:

CSV upload
-----------

The first way to upload a waveform through Labber is the upload via a CSV file.
A generator channel support the upload of a single complex waveform and the AWG channel
allows the upload of 2 waves and markers.

The format of CSV file is the following:

* Each row represents one waveform
* Delimiter: ``,``
* If the waveform for the given index/slot should be ignored the respective row
  can be empty.

To upload a waveform to index 0 and index 2 the CSV file could look like that

.. code-block::

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

Waveform Processor upload
--------------------------

Often the waveforms for specific applications can be generated within another
instrument in Labber (e.g. SingleQubitPulseGenerator). Since the Waveform Nodes
of the AWG format have a special format one can not directly connect the two
quantities directly. Also it is impractical to log the waveforms in their original
format since one can not directly see the separate waves.

To be able to do this zhinst-labber also provides a virtual Instrument called
``Zurich_Instruments_Waveform_Processor``. It converts between the native Zurich
Instrument waveform format and Labber Arrays. All of the exposed array quantities
can be used as input or outputs.

On the device side the following quantities exist:

* ``Interleaved - Signal``
* ``Complex - Signal``

On the Labber side the following counterparts exist:

* ``Wave 1 - Signal``
* ``Wave 2 - Signal``
* ``Marker - Signal``

The following scenarios are the most useful ones (but all combinations are possible):

1. Route two real waveforms to a single device waveform channel. The two input
   signals are routed to ``Wave 1 - Signal`` and ``Wave 2 - Signal`` and the
   ``Interleaved - Signal`` is routed to the awg waveform quantity (e.g.
   ``AWG - Waveforms - 0 - Wave``). (The marker array can also be specified if
   needed.)

2. Route two real waveforms to a complex waveform channel. The two input signals
   are routed to ``Wave 1 - Signal`` and ``Wave 2 - Signal``. The
   ``Complex - Signal`` combines these two into a complex waveform. The first
   wave is the real part and the second wave is the imaginary part.

3. Log a waveform in a way that Labber can display it. The native awg waveform
   from the device (e.g. ``AWG - Waveforms - 0 - Wave``) is routed to
   ``Interleaved - Signal``. Since one can not detect which format the waveform
   is in the following quantities may need to be adjusted:

   * ``Interleaved - Num - Channels`` (Either 1 or 2)

   * ``Interleaved - Marker - Present`` (True if a marker is present in the signal)

   ``Wave 1 - Signal``, ``Wave 2 - Signal`` and ``Marker - Signal`` can no be
   logged and contain the respective part of the original waveform.




