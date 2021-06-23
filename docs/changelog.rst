Changelog
==========================================

E7EPD Database Specification
--------------------------------------------

* v0.05: Initial Release
* v0.1:
    * Removed the Microcontroller table
    * Added an all-encompassing IC table
    * Added a PCB Table
    * Clean up some mismatch between the wrapper and this spec

Database Python DB Wrapper
--------------------------------------------
* v0.05 Initial Release
* v0.1(In Progress):
    * Removed the Microcontroller class
    * Added an IC class
    * Changed main class name from ``EEData`` to ``E7EPD``
    * Allowing user-given ``sqlite3`` connections
    * Added some autocomplete lists for some part's info like IC manufacturers and capacitor types
    * Better documentation

CLI
-----------

* v0.1: Initial Release
* v0.2 (In Progress):
    * Added initial setup for user to set the ``sqlite3`` database file
    * Added option to enter values as a percentage (so for example 1/4 for 0.25)
    * Added autocomplete for part's values like capacitor type, if they exist in the database wrapper
    * Added autocomplete hinting when a manufacturer part number is asked
    * Added option to remove and append stock to a part