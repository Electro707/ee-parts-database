Database CLI Application
==========================================

While the database can be operated by any external program, a CLI utility exist for interfacing with the database.

Requirements
++++++++++++++++++++++++

To run this CLI application, you will need ``python>3.7``. On top of that, other than the built-in packages you will
need the following packages as well:

* `rich <https://pypi.org/project/rich/>`__
* `questionary <https://pypi.org/project/questionary/>`__
* `engineering_notation <https://pypi.org/project/engineering-notation/>`__
* `SQLAlchemy <https://pypi.org/project/SQLAlchemy/>`__
* `alembic <https://pypi.org/project/alembic/>`__

Usage
++++++++++++++++++++++++
Coming Soon!


Digikey Barcode Scanning
++++++++++++++++++++++++
The CLI application allows for scanning and inputting a Digikey 2D barcode that are included in a part's bag.
To utilize this feature, my fork of `digikey-api` must be installed, which can be done with:

.. code-block:: sh

    pip install git+https://github.com/Electro707/digikey-api.git@8549f42a1853c9d371c3fb1b0b8d780d405174d8

Initially, you need to setup the DigikeyAPI with you client secret and client ID in the CLI for your Digikey Developer application which is done thru the main menu under the *'Digikey API Settings'* option.
This application must have the *'Barcode'* and *'Product Information'* APIs enabled in Digikey's API settings.
For more information on Digikey's APIs, see `https://developer.digikey.com/get_started <https://developer.digikey.com/get_started>`__.

When asked for a manufacturer part number in the CLI application, you can scan a Digikey 2D barcode instead of typing
in a manufacturer number. The input to the CLI application must be the scanned data.