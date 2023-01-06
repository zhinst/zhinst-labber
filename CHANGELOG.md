# zhinst-labber Changelog

## Version 0.3.1

* Added support for `dict` type in `values` key when `Quantity` datatype is `VECTOR`. The settings value
  `vector_quantity_value_map_array_keys` points to the correct key in the `dict`.

## Version 0.3.0
* Adapt drivers to ``zhinst-toolkit`` 0.3.x which is a major refactoring and improves
  speed, stability and feature availability.
* Introduce python package ``zhint-labber`` which is able to automatically generate
  the Labber driver for each Zurich Instruments device (including HF2).
* Easy to access CLI for zhinst-labber.
* Node naming aligned with LabOne.
* Automatic support for all nodes available on the device.
* Enhanced logging functionality.
* Waveform Processor that is able to convert native AWG Waveforms into its parts.
* Add DAQ, Sweeper and SHFQA sweeper modules

## Version 0.2.0
* Add SHFQA and SHFSG support

## Version 0.1.0
* initial release
