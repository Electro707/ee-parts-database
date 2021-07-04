E7EPD Database Specification 
================================================
**Rev 0.2**

Specification Notes
---------------------------------
Components 
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

All components, when specified, will be based of the `GenericPart` table spec that contains common columns.
Note that the `GenericPart` table doesn't exist by itself but is used in this document as columns that every 
other table should have

Different Tables Per Components
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
To allow for the parameterization of parts, and due to SQL's column nature where it's usually unchanged, each
specific component type (like resistors, IC, etc) will have its own SQL table.

Table Spec
---------------------------------
GenericPart Table
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
============= ================================= =======================================================
Name          SQL Type                          Description
============= ================================= =======================================================
id            INTEGER PRIMARY KEY AUTOINCREMENT Each row in the database will contain an unique SQL ID
stock         INT NOT NULL                      The number of parts in stock
mfr_part_numb VARCHAR NOT NULL                  The manufacturer part number, used to distinguish each part from another
manufacturer  VARCHAR                           The manufacturer of the component
package       VARCHAR NOT NULL                  The part's physical package
part_comments MEDIUMTEXT                        Comments about the part
user_comments MEDIUMTEXT                        Any other user comments
============= ================================= =======================================================

Resistor Table
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Append the *GenericPart* Table to this table.

============= =================== =======================================================
Name          SQL Type            Description
============= =================== =======================================================
resistance    FLOAT NOT NULL      The resistor's resistance
tolerance     FLOAT               The resistor's tolerance as a float (so a 5% resistor will be stored as 5)
power         FLOAT               The resistor's power rating in W
============= =================== =======================================================

Capacitor Table
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Append the *GenericPart* Table to this table.

============= =================== =======================================================
Name          SQL Type            Description
============= =================== =======================================================
capacitance   FLOAT NOT NULL      The capacitor's capacitance
tolerance     FLOAT               The capacitor's tolerance as a float (so a 5% capacitor will be stored as 5)
power         FLOAT               The capacitor's power rating in W
voltage       FLOAT               The capacitor's maximum voltage rating
temp_coeff    VARCHAR             The capacitor's temperature coefficient
cap_type      VARCHAR             The capacitor types, which should only be 'electrolytic', 'ceramic', 'tantalum', 'film'. If a type is not listed, you can enter a custom type, just make sure that it's consistent for different parts (also create an Issue on the Github page so we can all have it :)
============= =================== =======================================================

Inductor Table
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Append the *GenericPart* Table to this table.

============= =================== =======================================================
Name          SQL Type            Description
============= =================== =======================================================
inductance    FLOAT NOT NULL      The inductance of the inductor
tolerance     FLOAT               The inductor's tolerance as a float (so a 5% inductor will be stored as 5)
max_current   FLOAT               The inductor's maximum current
============= =================== =======================================================

Diode Table
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Append the *GenericPart* Table to this table.

=================== =================== =======================================================
Name                SQL Type            Description
=================== =================== =======================================================
diode_type          VARCHAR NOT NULL    Diode Type (Regular, Zener, Schottky, etc)
max_current         FLOAT               Max/Peak Current
average_current     FLOAT               Average Current Rating
max_rv              FLOAT               Max reverse voltage
=================== =================== =======================================================

IC Table
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Append the *GenericPart* Table to this table.

============= =================== =======================================================
Name          SQL Type            Description
============= =================== =======================================================
ic_type       VARCHAR NOT NULL    The IC type, for example microcontroller, ADC, comparator, etc.
============= =================== =======================================================

PCBs Table
---------------------------------
============= ===================================== =======================================================
Name          SQL Type                              Description
============= ===================================== =======================================================
id            INTEGER PRIMARY KEY AUTOINCREMENT     Each row in the database will contain an unique SQL ID
stock         INT NOT NULL                          The number of parts in stock
rev           VARCHAR NOT NULL                      The project's revision
sub_rev       VARCHAR                               The project's sub-revision
project_name  VARCHAR NOT NULL                      The project name related to this part. The project should match that of the Projects database (upcoming in Rev 0.2)
user_comments MEDIUMTEXT                            Any other user comments
============= ===================================== =======================================================

Projects
---------------------------------
TODO, in Rev 2.0

