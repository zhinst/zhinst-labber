LabOne Modules
================

Besides the device drivers, zhinst-labber also is able to generate the following
LabOne modules:

* Data Acquisition Module (DAQ Module)
* Sweeper Module
* SHFQA Sweeper

Modules are software based functionalities that eases the use of the devices
and take care of complex mechanisms. For more information take a look at the
`LabOne Programming manual <http://docs.zhinst.com/manuals/labone_programming_manual/introduction_labone_modules.html./>`_.

Modules create a independent session to the server. This enable the modules to
subscribe to nodes without affecting other modules, the GUI or user based
sessions. This and the fact that the modules are device independent is the
reason zhinst-labber doesn`t include the modules directly into the device drivers.

.. note::

    The Labber driver for the modules are automatically generated/updated when a
    device driver that support the module is generated.

Labber modules require a device to operate on but this does not limit the amount
of modules one can create. This mean one can create multiple module Instruments
in Labber for the same device or for different devices.

Start A Labber Module Instrument
---------------------------------

Similar to the device drivers module driver require that the device id /serial
of the used instrument (e.g. DEV1234) is placed in the ``Address`` field. The
``Interface`` needs to set to ``Other`` and the Name is not used by the driver
itself and can be chosen freely.

Modules have the same structure than the devices, meaning all nodes available in
the driver. The following sections explain the basic usage of the provided
modules. An in-depth introduction into the modules can be found in the
`LabOne Programming manual <http://docs.zhinst.com/manuals/labone_programming_manual/introduction_labone_modules.html./>`_.
the `LabOne API Examples <https://github.com/zhinst/labone-api-examples./>`_ provide
examples how the modules can be used (Since the node naming is the same they
can be applied to the Labber driver in the same way).

DAQ Module
-----------
The `Data Acquisition Module <http://docs.zhinst.com/manuals/labone_programming_manual/data_acquisition_module.html./>`_
corresponds to the Data Acquisition tab of the LabOne User Interface. It enables
the user to record and align time and frequency domain data from multiple
instrument signal sources at a defined data rate. The data may be recorded either
continuously or in bursts based upon trigger criteria analogous to the
functionality provided by laboratory oscilloscopes.

The Labber driver defines 16 signal channels. Each channel can be set to a
specific signal. Please see the
`user manual <http://docs.pages.zhinst.com/manuals/labone_programming_manual/data_acquisition_module.html#pm.core.modules.daq.signalsubscription/>`_
to see how the signals are constructed. Alternatively one can use the LabOne UI
to see the available signals and use the API Log feature to see what the
corresponding node/signal looks like. An example of a valid signal is
``dev1234/demods/0/sample.x`` and is equal to ``demods/0/sample.x``.

Once all signals have been specified, the module is enable and has been triggered
the result quantities contain the latest data.

.. note::

    Even though the DAQ module has a history feature the result quantities only
    contain the latest traces. It is however possible to save the results,
    including older traces, using the save feature in the history tab.

.. note::

    The results are only updated if new data is available, but can be cleared
    manually through the clear node.

Sweeper Module
---------------

The Sweeper Module allows the user to perform sweeps as in the Sweeper Tab of the
LabOne User Interface. In general, the Sweeper can be used to obtain data when
measuring a DUT's response to varying (or sweeping) one instrument setting while
other instrument settings are kept constant.

The Labber driver defines 16 signal channels. Each channel can be set to a
specific signal. A signal has two parts (``path::node_part``). The first
one (path) is the streaming node itself (e.g. /dev1234/demods/sample), the second part is the
part of the node that should be displayed (If left empty a default value will be
used, if available). Which parts each node has depends on the node type and can
be looked up in the LabOne UI. An example of a valid signal for the sweeper
module is for example ``/dev1234/demods/0/sample::x``, which will subscribe to
the node ``/dev1234/demods/0/sample`` and use the ``x`` value of it in the
result quantity.

Available node parts (not a complete list):

* demods
    * auxin0
    * auxin1
    * frequency
    * phase
    * r
    * x
    * y
* imps
    * abs
    * bias
    * drive
    * frequency
    * imagz
    * param0
    * param1


To enable a sweep the ``Enable`` quantity can be set to 1. The same node can
be used to disable the sweeper module (0) or to check if a sweep is in progress
(read the current value). The result quantities contain the specified signal
parts (can also be updated during a sweep)

SHFQA Sweeper Module
---------------------

The SHFQA sweeper is a special case and only works for the SHFQA/SHFQC. The
underlying implementation can be found in the zhinst.utils.shf_sweeper.
zhinst-toolkit wraps around this and exposes a interface similar to the native
LabOne modules. This means the Labber driver for the SHFQA sweeper exposes all
parameters. A sweep is executed every time the result vector is read.

View the `toolkit example <https://docs.zhinst.com/zhinst-toolkit/en/latest/examples/shfqa_sweeper.html./>`_.
for a real live example on how the SHFQA sweeper module can be used.
