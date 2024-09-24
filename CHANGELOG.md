# zhinst-labber Changelog

## Version 0.3.3

- Add `interface` option to cli to allow specifying the interface of the target device.
  This is mostly necessary for the hf2, mf and uhf device family since they require an
  interface to be explicitly specified, if the device it not already connected to the data
  server.

## Version 0.3.2

- Fixed issue where an empty command table was sent to the device when the node has no value defined in Labber UI,
  resulting in LabOne UI warnings
- Fixed issue where setting Nodes with enumerated values issued a warning to the Labber log

## Version 0.3.1

* Added automatic Zurich Instruments static driver generation when generating new drivers.
  Current static driver(s): Zurich Instrument Waveform Processor
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
