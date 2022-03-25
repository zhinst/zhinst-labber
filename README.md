![CI](https://github.com/zhinst/zhinst-labber/workflows/CI/badge.svg?branch=main)
[![Coverage](https://codecov.io/gh/zhinst/zhinst-labber/branch/main/graph/badge.svg?token=VUDDFQE20M)](https://codecov.io/gh/zhinst/zhinst-labber)
[![PyPI version](https://badge.fury.io/py/zhinst-labber.svg)](https://badge.fury.io/py/zhinst-labber)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)
[![Twitter URL](https://img.shields.io/twitter/url/https/twitter.com/fold_left.svg?style=social&label=Follow%20%40zhinst)](https://twitter.com/zhinst)

# Zurich Instruments Labber Drivers

The Zurich Instruments Labber Drivers is a python package that is able to
automatically generate and update instrument drivers for all Zurich Instruments
devices for the scientific measurement software [Labber](http://labber.org/).

The Labber drivers are based on the
[Zurich Instruments Toolkit](https://github.com/zhinst/zhinst-toolkit)
(*zhinst-toolkit*), a high level driver of our Python API *ziPython*.

# Status

The Zurich Instruments Labber Drivers are well tested and considered stable
enough for general usage. The interfaces may have some incompatible changes
between releases. Please check the changelog if you are upgrading to the latest version.

## LabOne software
As a prerequisite, the LabOne software version 22.02 or later must be installed.
It can be downloaded for free at
[https://www.zhinst.com/labone](https://www.zhinst.com/labone). Follow the
installation instructions specific to your platform. Verify that you can
connect to your instrument(s) using the web interface of LabOne. If you are
upgrading from an older version, be sure to update the firmware of all
Zurich Instruments devices in use by using the web interface.

In principle LabOne can be installed in a remote machine, but we highly
recommend to install it on a local machine where you intend to run the experiment.

# Getting Started

Labber comes with its own Python distribution that is used by default.
If not specified otherwise (Preferences -> Advanced -> Python distribution) the
following command needs to be executed within this distribution.
(C:\\Program Files\\Labber\\python-labber\\Scripts\\pip.exe or similar).

```
pip install zhinst-labber
```

The drivers for an device can now be generated using the command line interface.

For example the following command generated the driver for the Device DEV1234
inside the Labber driver folder of the ZI user.

```
zhinst-labber setup "C:\Users\ZI\Labber\Drivers" DEV1234 localhost
```

## Documentation
For a full documentation see [here](https://docs.zhinst.com/zhinst-labber/en/latest).

## Contributing
We welcome contributions by the community, either as bug reports, fixes and new
code. Please use the GitHub issue tracker to report bugs or submit patches.
Before developing something new, please get in contact with us.

## License
This software is licensed under the terms of the MIT license.
See [LICENSE](LICENSE) for more detail.
