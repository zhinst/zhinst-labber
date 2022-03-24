Command Table
==============

Command Tables are part of the AWG functionality and provide a way to optimize
the space required for the waveforms on the device.

The user manuals for each device, that has a AWG available, provides detailed
explanation of all available commands and syntax.

The Labber drivers support the upload of command_table from a ``*.json`` file.
The file path can be specified in the drivers for each AWG channel individually
(The quantity is called ``* - Commandtable - Data``).
Setting the file path will automatically trigger the validation and upload of
the command table and no further steps are required.
