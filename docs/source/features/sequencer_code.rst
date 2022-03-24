Sequencer Code
===============

The Arbitrary Waveform Generator functionality is realized using field-programmable
gate array (FPGA) technology and is available on multiple instruments types, like
the HDAWG, SHFSG or the SHFQA. Users can operate the AWG through a program called
sequencer code, it defines which waveforms are played and in which order. The
syntax of the LabOne AWG Sequencer programming language is based on C, but with
a few simplifications.

The user manuals for each device, that has a AWG available, provides detailed
explanation of all available commands and syntax.

The Labber drivers support the upload of a sequencer program from a ``*.seqc`` file.
The file path can be specified in the drivers for each AWG channel individually
(The quantity is called ``* - Sequencer_Program``).
Setting the file path will automatically trigger the compilation and upload of
the code and no further steps are required.
