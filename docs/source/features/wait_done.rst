Wait Done Quantities
=====================

The Labber driver expose all node available for the device. In theory these Nodes
is everything one needs to operate the device. Sometimes it is however handy to
have additional functionality. Some of them are already described already in the
previous sections. This section explains the usage and purpose of the
``* - Wait_Done`` quantities.

Labber is not able to detect easily if a measurement, e.g. a scope shot, that
is running on the device is finished or not. Although Labber provides these
a way of for most scenarios not all use cases are covered. The zhinst-labber
drivers therefor expose the wait done quantities. They are of a boolean type
and if enabled block the execution of a measurement until the corresponding
measurement is finished.

Especially in the measurement editor this can be used to ensure that a
measurement is finished before the results are logged.

All of the wait done quantities have a timeout that prevents the measurement from
being blocked for to long.

At after the measurement is finish the quantity is reset automatically to 0 so
it can be called again.
