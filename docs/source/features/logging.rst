Logging and Error Handling
===========================

All logging information inside the driver are displayed in the python output
window that is created for each instrument when connected. By default the
logging level is set to ``info``, which means it is quite verbose and should
help understanding what happens in the background and if a specific information
is failing.

Exceptions from LabOne and the zhinst-labber drivers are not forwarded to Labber
it self but rather logged as an Error. This helps testing out different
configurations without loosing the device connection every time. It therefor
advised to check the logs after a measurement to ensure no problem occurred
during the measurement.

The logger level can easily be adjusted for each instrument individually through
the ``settings.json`` file that is generated for each driver in its folder.
Simply add a entry called ``logger_level`` followed by the desired level, as an
integer.

* CRITICAL => 50
* ERROR => 40
* WARNING => 30
* INFO => 20
* DEBUG => 10

One can also specify an additional file path in the ``settings.json`` where all
the log messages are stored permanently. The desired target file can be specfied
by adding an entry called ``logger_path``.
(e.g "logger_path": "C:\\\\Users\\\\test\\\\zhinst_labber.log", note the double
escaped backslash which is mandatory in the json format)
