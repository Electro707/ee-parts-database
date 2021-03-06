E7EPD Database Specification
================================================
**Rev 0.5**

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
============= ========================= =========== =======================================================
Name          SQL Type                  Required?   Description
============= ========================= =========== =======================================================
id            INTEGER PRIMARY KEY       YES         Each row in the database will contain an unique SQL ID
stock         INT                       YES         The number of parts in stock
mfr_part_numb VARCHAR                   YES         The manufacturer part number, used to distinguish each part from another
manufacturer  VARCHAR                               The manufacturer of the component
package       VARCHAR                   YES         The part's physical package
storage       VARCHAR                               The part's storage location
comments      TEXT                                  Comments about the part
datasheet     TEXT                                  The datasheet of the part
============= ========================= =========== =======================================================

Resistor Table
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Append the *GenericPart* Table to this table.
Table Name: ``resistance``

============= ========================= =========== =======================================================
Name          SQL Type                  Required?   Description
============= ========================= =========== =======================================================
resistance    FLOAT                     YES         The resistor's resistance
tolerance     FLOAT                                 The resistor's tolerance as a float (so a 5% resistor will be stored as 5)
power         FLOAT                                 The resistor's power rating in W
============= ========================= =========== =======================================================

Capacitor Table
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Append the *GenericPart* Table to this table.
Table Name: ``capacitor``

============= ========================= =========== =======================================================
Name          SQL Type                  Required?   Description
============= ========================= =========== =======================================================
capacitance   FLOAT                     YES         The capacitor's capacitance
tolerance     FLOAT                                 The capacitor's tolerance as a float (so a 5% capacitor will be stored as 5)
voltage       FLOAT                                 The capacitor's maximum voltage rating
temp_coeff    VARCHAR                               The capacitor's temperature coefficient
cap_type      VARCHAR                               The capacitor types, which should only be 'electrolytic', 'ceramic', 'tantalum', 'film'. If a type is not listed, you can enter a custom type, just make sure that it's consistent for different parts (also create an Issue on the Github page so we can all have it :)
============= ========================= =========== =======================================================

Inductor Table
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Append the *GenericPart* Table to this table.
Table Name: ``inductor``

============= ========================= =========== =======================================================
Name          SQL Type                  Required?   Description
============= ========================= =========== =======================================================
inductance    FLOAT                     YES         The inductance of the inductor
tolerance     FLOAT                                 The inductor's tolerance as a float (so a 5% inductor will be stored as 5)
max_current   FLOAT                                 The inductor's maximum current
============= ========================= =========== =======================================================

Diode Table
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Append the *GenericPart* Table to this table.
Table Name: ``diode``

================= ========================= =========== =======================================================
Name              SQL Type                  Required?   Description
================= ========================= =========== =======================================================
diode_type        VARCHAR                   YES         Diode Type (Regular, Zener, Schottky, etc)
max_current       FLOAT                                 Max/Peak Current
average_current   FLOAT                                 Average Current Rating
max_rv            FLOAT                                 Max reverse voltage
================= ========================= =========== =======================================================

IC Table
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Append the *GenericPart* Table to this table.
Table Name: ``ic``

============= ========================= =========== =======================================================
Name          SQL Type                  Required?   Description
============= ========================= =========== =======================================================
ic_type       VARCHAR                   YES         The IC type, for example microcontroller, ADC, comparator, etc.
============= ========================= =========== =======================================================

Crystal Table
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Append the *GenericPart* Table to this table.
Table Name: ``crystal``

=============== =========================== =========== =======================================================
Name            SQL Type                    Required?   Description
=============== =========================== =========== =======================================================
frequency       FLOAT                       YES         The frequency of the crystal
load_c          FLOAT                                   The load capacitance (in pF) of the crystal
esr             FLOAT                                   The ECR (in Ohms) of the crystal
stability_ppm   FLOAT                                   The stability (in ppm) of the crystal
=============== =========================== =========== =======================================================

MOSFET Table
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Append the *GenericPart* Table to this table.
Table Name: ``mosfet``

=============== =========================== =========== =======================================================
Name            SQL Type                    Required?   Description
=============== =========================== =========== =======================================================
mosfet_type     VARCHAR                     YES         The MOSFET type (N-Channel or P-Channel)
vdss            FLOAT                                   The max Drain-Source voltage of the MOSFET
vgss            FLOAT                                   The max Gate-Source voltage of the MOSFET
vgs_th          FLOAT                                   The Gate-Source threshold voltage of the MOSFET
i_d             FLOAT                                   The max continuous drain current of the MOSFET
i_d_pulse       FLOAT                                   The max pulsed/peak drain current of the MOSFET
=============== =========================== =========== =======================================================

BJT Table
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Append the *GenericPart* Table to this table.
Table Name: ``bjt``

=============== =========================== =========== =======================================================
Name            SQL Type                    Required?   Description
=============== =========================== =========== =======================================================
bjt_type        VARCHAR                     YES         The BJT type (NPN or PNP)
vcbo            FLOAT                                   The max Collector-Base voltage of the BJT
vceo            FLOAT                                   The max Collector-Emitter voltage of the BJT
vebo            FLOAT                                   The max Emitter-Base voltage of the BJT
i_c             FLOAT                                   The max continuous collector current of the BJT
i_c_peak        FLOAT                                   The max pulsed/peak collector current of the BJT
=============== =========================== =========== =======================================================

Connector Table
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Append the *GenericPart* Table to this table.
Table Name: ``connector``

============= ========================= =========== =======================================================
Name          SQL Type                  Required?   Description
============= ========================= =========== =======================================================
conn_type     VARCHAR                   YES         The connector type (Banana, Rect. Header, Test point, etc)
============= ========================= =========== =======================================================

LED Table
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Append the *GenericPart* Table to this table.
Table Name: ``led``

============= ========================= =========== =======================================================
Name          SQL Type                  Required?   Description
============= ========================= =========== =======================================================
led_type      VARCHAR                   YES         The LED's color (Red, Blue, RGB, etc)
vf            FLOAT                                 The LED's forward voltage
max_i         FLOAT                                 The LED's maximum forward current
============= ========================= =========== =======================================================

Fuse Table
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Append the *GenericPart* Table to this table.
Table Name: ``fuse``

============= ========================= =========== =======================================================
Name          SQL Type                  Required?   Description
============= ========================= =========== =======================================================
fuse_type     VARCHAR                   YES         The fuse type (Glass, PTC, etc)
max_v         FLOAT                                 The fuse's max voltage
max_i         FLOAT                                 The fuse's absolute maximum current
trip_i        FLOAT                                 The fuse's trip current
hold_i        FLOAT                                 The fuse's hold current
============= ========================= =========== =======================================================

Button/Switch Table
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Append the *GenericPart* Table to this table.
Table Name: ``button``

============= ========================= =========== =======================================================
Name          SQL Type                  Required?   Description
============= ========================= =========== =======================================================
bt_type       VARCHAR                   YES         The button/switch type (Tactile, Rocker, etc)
circuit_t     VARCHAR                               The button/switch's configuration (SPDT, SPST-NO, etc)
max_v         FLOAT                                 The button/switch's max voltage
max_i         FLOAT                                 The button/switch's absolute maximum current
============= ========================= =========== =======================================================

Misc Table
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
This table is exactly the same as the *GenericPart* Table.
Table Name: ``misc_c``

PCBs
---------------------------------
Each PCB will have parts associated with it. This should allow the user application to determine if it's possible to
build up a board given the current component's stock.

PCB Table
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Table Name: ``pcb``

============= ========================= =========== =======================================================
Name          SQL Type                  Required?   Description
============= ========================= =========== =======================================================
id            INTEGER PRIMARY KEY       YES         Each row in the database will contain an unique SQL ID
stock         INT                       YES         The number of parts in stock
board_name    VARCHAR                   YES         The board's name. Can also be thought of as the project's name
rev           VARCHAR                   YES         The pcb's revision
sub_rev       VARCHAR                               The pcb's sub-revision
comments      TEXT                                  Comments about the part
parts         JSON                      YES         A JSON list containing all of the parts used for this project
============= ========================= =========== =======================================================

Parts JSON List
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The parts JSON is a list of dictionaries containing the all parts used for a particular board.

The dictionaries in this list is formatted as follows for a component:

============= ============= =======================================================
Key           Value Type    Description
============= ============= =======================================================
comp_type     string        The component type (resistor, bjt, etc) which corresponds to the part's table name
part          dict          A dictionary describing the part
qty           int           The quantity of this part used in this board
alternatives  list          A list of alternative parts that can be used, each part being the same format as the part key above. This list can be left as an empty array.
============= ============= =======================================================

The part key above is a dictionary containing a set of filter key-value pairs that narrows down a part.
For example, for a part with the manufacturer part number of "PART123", the part dict would be
.. code-block::

    {
        mfr_part_numb: PART123
    }

As the manufacturer part number is unique to each part, this filter would only find a single part. With a resistor
for example, where a specific part does not matter, the part dict would look something like
.. code-block::

    {
        resistance: 1000
        power: >0.125
        package: 0805
    }

The `>` prefix in `power: >0.125` indicates that the power value must be greater than 1/8W, and anything above that is fine as well.
