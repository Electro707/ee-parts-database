_.. module:: e7epd

API Reference
==========================================

Python Documentation
++++++++++++++++++++++++

.. autoclass:: E7EPD
  :members:
  :undoc-members:

.. autoexception:: InputException
  :members:

.. autoexception:: EmptyInDatabase
  :members:

.. autoexception:: NegativeStock
  :members:


Autofill Helpers
++++++++++++++++++++++++

This wrapper module also comes with some autofill helpers. All are in the dictionary ``autofill_helpers_list``.
Here are the current autofill helpers available:

* ``ic_manufacturers``: IC manufacturers like TI and Cypress
* ``ic_types``: The IC type, like Microcontroller and ADC
* ``capacitor_types``: Capacitor types like Ceramic and Electrolytic
* ``diode_type``: Diode Types
* ``passive_manufacturers``: Passives (resistors, capacitors, etc) manufacturers
* ``passive_packages``: Packages for passives
* ``ic_packages``: Packages for ICs
* ``mosfet_types``: MOSFET types (N-Channel, P-Channel)
* ``bjt_types``: BTJ Type (NPN, PNP)
* ``fuse_types``: Fuse Type (Slow Blow, PTC, etc)
* ``led_types``: LED "Type" (Red, RGB, Addressable, etc)

