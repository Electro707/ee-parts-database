Changelog
==========================================
The database specification will be separately tracked from the Python DB wrapper and CLI tool

E7EPD Database Specification
--------------------------------------------

* v0.05:
    * Initial Release
* v0.1:
    * Removed the Microcontroller table
    * Added an all-encompassing IC table
    * Added a PCB Table
    * Clean up some mismatch between the wrapper and this spec
* v0.2:
    * Added Inductor table
    * Added Diode table
* v0.3:
    * Added a ``storage`` key to all parts
    * Merged ``user_comments`` and ``part_comments`` to just one ``comments`` column
    * Removed ``power`` for the capacitor table
    * Updated type of the ``comments`` column to ``TEXT``
    * Added a spec for
        * Crystals
        * MOSFETs
        * BJTs
        * Connectors
        * LEDs
        * Fuses
        * Switches/Buttons
        * Misc/Others
* v0.4:
    * Added datasheet column for all components
    * Removal of ``project_name`` from the PCB table and replaced it ``board_name``
    * Added a ``parts`` JSON list for the PCB table, allowing parts to be cross-referenced per board

Database Python DB Wrapper
--------------------------------------------
* v0.05:
    * Initial Release
* v0.2:
    * Updated spec for Database Rev 0.2
    * Changed main class name from ``EEData`` to ``E7EPD``
    * Allowing user-given ``sqlite3`` connections
    * Added some autocomplete lists for some part's info like IC manufacturers and capacitor types
    * Better documentation
    * Added ```wipe_database``` function
    * Added a way for the backend to store configurations about itself
    * Added a key to check the database specification the database is under and the ``E7EPD`` class
* v0.3:
    * Switched to sqlalchemy for handing SQL
    * As the wrapper input includes a sqlalchemy engine, any sql type that sqlalchemy supports should be supported
    * Updated spec for Database Rev 0.3
    * Added the first migration from Database Rev 0.2 to 0.3 with ``alembic``
    * Added a ``PCB`` class from database spec (didn't for 0.2)
    * Added autofill helpers for the new component types
    * Re-factored backend spec and display_as lists
* v0.4:
    * Updated spec for Database Rev 0.4
    * Added migrations from database rev 0.3 to 0.4
    * More autofill helpers
    * Removed the ``update_part`` function as the variable returned by ``get_part_by_id`` or ``get_part_by_mfr_part_numb``
      already has a database link, so modifying that with a ``commit`` command will make the changes
    * Added a ``commit`` and ``rollback`` function for when modifying a returned part linked to the database
    * Re-made the ``backup_db`` function to actually work. Dumps content as a JSON file
* v0.4.1:
    * No changes
* v0.5(WIP):
    * Added an overall `E7EPD` helper function to get all manufacturer part number
    * TODO: Add Projects


CLI
-----------

* v0.1:
    * Initial Release
* v0.2:
    * Added initial setup for user to set the ``sqlite3`` database file
    * Added option to enter values as a percentage (so for example 1/4 for 0.25)
    * Added autocomplete for part's values like capacitor type, if they exist in the database wrapper
    * Added autocomplete hinting when a manufacturer part number is asked
    * Added option to remove and append stock to a part
    * Moved around options so that there is an "initial screen" before choosing components
    * Added a check for the database revision on startup
* v0.3:
    * Updated for the new Wrapper 0.3 database argument
    * Changed options so it's easier to add a new part
    * Allowing option for a mySQL database
    * Allowing option to add multiple databases
    * Allowing option to select which database to connect to
* v0.4:
    * Added ability to scan a Digikey barcode for the manufacturer part number
    * Added ability to edit a part's properties
* v0.4.1:
    * Fixed bug with an empty database where you could not enter a manufacturer part number
    * Added more safety checks and exception handling around the user input function
    * Changed the way the Digikey API got loaded and set as to not be intrusive
    * Added docs for the Digikey barcode scanning feature
    * Fixed the `Digikey API Settings` option in the main menu to allow changing the Client ID and Client Secret
    * Added a __main__.py file to allow execution of `e7epd` as a Python module with `python -m e7epd`
* v0.5(WIP):
    * Added more docs to existing functions to make it easier to interpret
    * Made it so creating an existing part would prompt to instead add the part to the existing stock
    * Added better messages about stock when adding or removing stock
    * Added PCBs as an option to add them

* TODOs:
    * Add option to import BOM file/CSV file
    * Add ability to "interact" with the PCB table
    * Add cross-coerelation between a PCB's parts and parts in the database