Quickstart
==========

Eager to get started? This page gives a good introduction to zhinst-labber.
Follow :doc:`installation` to install zhinst-labber first.

Preparation
-----------

Before you can spin up zhinst-labber LabOne® needs to installed and running.
For a complete reference see the dedicated `user manual <http://docs.zhinst.com/>`_
page for your instrument(s).

Before you continue make sure a LabOne® data server is running in your network and
all of your devices are visible.

Generate Instrument driver
---------------------------

zhinst-labber does not ship with predefined Instrument drivers. Instead the
command line can be used to generate a custom Instrument driver for all Zurich
Instrument devices. This has the benefit that one does not pay any attention to
the correct version or options.

The command line interface (CLI) can be be accessed after ``zhinst-labber`` has
been installed.

.. code-block:: bash

    >>> zhinst-labber setup --help
    Generate Zurich Instruments Labber drivers.
    ...

To generate a device driver the following information's are needed:

* Output file path. (Instrument Server -> Edit -> Preferences -> Folders -> Local Drivers)
* Device ID (e.g. DEV1234)
* Server Host (e.g localhost)

.. code-block:: bash

    >>> zhinst-labber setup "C:\Users\ZI\Labber\Drivers" DEV1234 localhost

.. warning::

    Old drivers (< 0.3 ) for Zurich Instruments devices should be deleted before
    using the zhinst-labber CLI. Drivers already generated with the zhinst-labber
    CLI are not affected by this.

.. note::

    If the driver should be generated for an HF2 device the option ``--hf2`` must
    be used.

.. note::

    The generated driver ist not bound to the used device but simply contains
    all the Quantities/Nodes that this device had at the time of the generation.
    This means the drivers can be used for other instruments, if it is of the
    same type, options and firmware revision.


Upgrade Instrument driver
--------------------------

Although it not mandatory it is recommended to upgrade the labber driver when
the firmware of the device changes. The command is the same but the ``--upgrade``
options is required. Without this option the generator does not overwrite
existing drivers.

.. code-block:: bash

    >>> zhinst-labber setup "C:\Users\ZI\Labber\Drivers" DEV1234 localhost --upgrade


Configuring the Instrument driver
----------------------------------

Besides the ``Zurich_Instruments_*.ini`` and ``Zurich_Instruments_*.py`` files
the script generates also a ``settings.json``. It offers the customization of
the drivers. It is pre filled with the information from the device used for
generating the driver but can be customized if needed.

The ``settings.json`` has the following structure:

.. code-block:: json

    {
        "data_server": {
            "host": "localhost",
            "port": 8004,
            "hf2": false,
            "shared_session": true
        },
        "instrument": {
            "base_type": "device",
            "type": "UHFLI"
        }
        "logger_level": 20
        "logger_path": "Path/to/log/output.log"
    }

* **host**: Used host server. Per default set to the server used during generation.
* **port**: Used host port. Per default set to the server used during generation.
* **hf2**: Flag if the used data_server is an HF2 data server. (automatically added
  by the generator if needed)
* **shared_session**: If true the instrument reuses a session to a data server.
  Sharing a session is enabled by default and increases the setup speed as well
  as resource consumption.
* **logger_level**: Used logger level. If not specified the default logger level
  (Info = 20) from zhinst-labber is used.
* **logger_path**: Optional path for storing the logger output to a path. (In
  addition to the std::out)

Using the Instrument drivers
-----------------------------

Once the drivers are generated they can be used within Labber. The following
configuration should be used:

* The ``Name`` is not used by the driver itself and can be chosen freely.
* The ``Interface`` **must** be set to ``Other``, regardless of the actual interface
  used for the device. The driver will automatically detect the correct
  interface. (As a fallback The LabOne GUI can be used to connect the data
  server to device via the correct interface)
* The ``Address`` (if available) **must** be set to one of the following:

  * For Devices and Modules: device id /serial of the used instrument (e.g. DEV1234).
  * For the DataServer ``server_host:server_port`` (e.g. localhost:8004). The port
    is optional and can be ignored if the default port (8004 or 8005 for hf2) is
    used.



