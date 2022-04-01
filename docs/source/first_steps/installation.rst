Installation
=============

Python version
--------------

Labber comes with its own Python distribution that is used by default.
If not specified otherwise (Preferences -> Advanced -> Python distribution) the
following guide needs to be executed within this distribution.
(C:\\Program Files\\Labber\\python-labber\\Scripts\\pip.exe or similar).

Dependencies
------------

These distributions will be installed automatically when installing zhinst-labber.

* `zhinst <https://pypi.org/project/zhinst/>`_ is the low level python api for Zurich
  Instruments devices.
* `zhinst-toolkit <https://pypi.org/project/zhinst-toolkit/>`_ is a high level
  driver on top of the LabOne® python api.
* `numpy <https://pypi.org/project/numpy/>`_ adds support for large, multi-dimensional
  arrays and matrices, along with a large collection of high-level mathematical
  functions to operate on these arrays.
* `click <https://click.palletsprojects.com/>`_ is a Python package for creating
  beautiful command line interfaces in a composable way with as little code as
  necessary.
* `jinja2 <https://jinja.palletsprojects.com/>`_ is a fast, expressive, extensible
  templating engine.
* `jsonschema <https://pypi.org/project/jsonschema/>`_ is an implementation of the JSON
  Schema specification for Python.
* `natsort <https://natsort.readthedocs.io>`_ is a simple yet flexible natural
  sorting in Python.

Install zhinst-labber
----------------------

Use the following command to install zhinst-labber (be sure to install it within the
correct python environment):

.. code-block:: sh

    $ pip install zhinst-labber

zhinst-labber is now installed. Check out the :doc:`Quickstart<quickstart>` or
go back to the :doc:`Documentation Overview <index>`.
