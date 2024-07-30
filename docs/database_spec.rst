E7EPD Database Specification
================================================
**Rev 0.6-beta**

.. warning::
    THIS DOCUMENTATION MAY NOT BE UP TO DATE, AS THIS IS STILL
    IN BETA

PyMongo
---------------------------------
This specification applies to a PyMongo Database. While any JSON-like document storage mechanism will be functional
with this spec, it is currently not supported.

Database Name
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The `ee-parts-db` database will be used for this specification.

Collections
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The following collections will be created in the `ee-parts-db` database:

- parts
- pcbs
- users
- e7epd_config

Specification Notes
---------------------------------
Components
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

All components, when specified, will be based of the `BasePartItems` spec that contains common keys.
Note that the `BasePartItems` spec doesn't exist by itself but is used in this document as keys that every
other part should have

All components will have an extra key: `type`. This allows to quickly determine what part type is per document,
and what keys to be looking for.
The `type` key's value will be described below per part type.

Table Spec
---------------------------------
GenericPart Items
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
============= ========================= =========== =======================================================
Name          Variable Type             Required?   Description
============= ========================= =========== =======================================================
ipn           str                       YES         The Internal-Part-Number, used to distinguish each part from another
stock         int                       YES         The number of parts in stock
mfr_part_numb str                                   The manufacturer part number
manufacturer  str                                   The manufacturer of the component
package       str                       YES         The part's physical package
storage       str                                   The part's storage location
comments      str                                   Comments about the part
datasheet     str                                   The datasheet of the part
user          str                                   The part user's information (who added the part for example)
============= ========================= =========== =======================================================

Resistor Table
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Append the *GenericPart* items to this table.
Type: ``resistor``

============= ========================= =========== =======================================================
Name          Variable Type             Required?   Description
============= ========================= =========== =======================================================
resistance    float                     YES         The resistor's resistance
tolerance     float                                 The resistor's tolerance as a float (so a 5% resistor will be stored as 5)
power         float                                 The resistor's power rating in W
============= ========================= =========== =======================================================

Capacitor Table
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Append the *GenericPart* items to this table.
Table Name: ``capacitor``

============= ========================= =========== =======================================================
Name          SQL Type                  Required?   Description
============= ========================= =========== =======================================================
capacitance   float                     YES         The capacitor's capacitance
tolerance     float                                 The capacitor's tolerance as a float (so a 5% capacitor will be stored as 5)
voltage       float                                 The capacitor's maximum voltage rating
temp_coeff    str                                   The capacitor's temperature coefficient
cap_type      str                                   The capacitor types, which should only be 'electrolytic', 'ceramic', 'tantalum', 'film'. If a type is not listed, you can enter a custom type, just make sure that it's consistent for different parts (also create an Issue on the Github page so we can all have it :)
============= ========================= =========== =======================================================

Inductor Table
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Append the *GenericPart* items to this table.
Table Name: ``inductor``

============= ========================= =========== =======================================================
Name          SQL Type                  Required?   Description
============= ========================= =========== =======================================================
inductance    float                     YES         The inductance of the inductor
tolerance     float                                 The inductor's tolerance as a float (so a 5% inductor will be stored as 5)
max_current   float                                 The inductor's maximum current
============= ========================= =========== =======================================================

Diode Table
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Append the *GenericPart* Spec to this.
Table Name: ``diode``

================= ========================= =========== =======================================================
Name              SQL Type                  Required?   Description
================= ========================= =========== =======================================================
diode_type        str                       YES         Diode Type (Regular, Zener, Schottky, etc)
max_current       float                                 Max/Peak Current
average_current   float                                 Average Current Rating
max_rv            float                                 Max reverse voltage
================= ========================= =========== =======================================================

IC Table
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Append the *GenericPart* Spec to this.
Table Name: ``ic``

============= ========================= =========== =======================================================
Name          SQL Type                  Required?   Description
============= ========================= =========== =======================================================
ic_type       str                       YES         The IC type, for example microcontroller, ADC, comparator, etc.
============= ========================= =========== =======================================================

Crystal Table
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Append the *GenericPart* Spec to this.
Table Name: ``crystal``

=============== =========================== =========== =======================================================
Name            SQL Type                    Required?   Description
=============== =========================== =========== =======================================================
frequency       float                       YES         The frequency of the crystal
load_c          float                                   The load capacitance (in pF) of the crystal
esr             float                                   The ECR (in Ohms) of the crystal
stability_ppm   float                                   The stability (in ppm) of the crystal
=============== =========================== =========== =======================================================

FET Spec
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Append the *GenericPart* Spec to this.
Table Name: ``fet``

=============== =========================== =========== =======================================================
Name            SQL Type                    Required?   Description
=============== =========================== =========== =======================================================
fet_type        str                         YES         The MOSFET type (N-Channel or P-Channel)
vds             float                                   The max Drain-Source voltage of the FET
vgs             float                                   The max Gate-Source voltage of the FET
vgs_th          float                                   The Gate-Source threshold voltage of the FET
i_d             float                                   The max continuous drain current of the FET
i_d_pulse       float                                   The max pulsed/peak drain current of the FET
=============== =========================== =========== =======================================================

BJT Table
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Append the *GenericPart* Spec to this.
Table Name: ``bjt``

=============== =========================== =========== =======================================================
Name            SQL Type                    Required?   Description
=============== =========================== =========== =======================================================
bjt_type        str                         YES         The BJT type (NPN or PNP)
vcbo            float                                   The max Collector-Base voltage of the BJT
vceo            float                                   The max Collector-Emitter voltage of the BJT
vebo            float                                   The max Emitter-Base voltage of the BJT
i_c             float                                   The max continuous collector current of the BJT
i_c_peak        float                                   The max pulsed/peak collector current of the BJT
=============== =========================== =========== =======================================================

Connector Table
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Append the *GenericPart* Spec to this.
Table Name: ``connector``

============= ========================= =========== =======================================================
Name          SQL Type                  Required?   Description
============= ========================= =========== =======================================================
conn_type     str                       YES         The connector type (Banana, Rect. Header, Test point, etc)
============= ========================= =========== =======================================================

LED Table
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Append the *GenericPart* Spec to this.
Table Name: ``led``

============= ========================= =========== =======================================================
Name          SQL Type                  Required?   Description
============= ========================= =========== =======================================================
led_type      str                       YES         The LED's color (Red, Blue, RGB, etc)
vf            float                                 The LED's forward voltage
max_i         float                                 The LED's maximum forward current
============= ========================= =========== =======================================================

Fuse Table
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Append the *GenericPart* Spec to this.
Type: ``fuse``

============= ========================= =========== =======================================================
Name          SQL Type                  Required?   Description
============= ========================= =========== =======================================================
fuse_type     str                       YES         The fuse type (Glass, PTC, etc)
max_v         float                                 The fuse's max voltage
max_i         float                                 The fuse's absolute maximum current
trip_i        float                                 The fuse's trip current
hold_i        float                                 The fuse's hold current
============= ========================= =========== =======================================================

Button/Switch Table
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Append the *GenericPart* Spec to this.
Type: ``button``

============= ========================= =========== =======================================================
Name          SQL Type                  Required?   Description
============= ========================= =========== =======================================================
bt_type       str                       YES         The button/switch type (Tactile, Rocker, etc)
circuit_t     str                                   The button/switch's configuration (SPDT, SPST-NO, etc)
max_v         float                                 The button/switch's max voltage
max_i         float                                 The button/switch's absolute maximum current
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
============= ========================= =========== =======================================================
Name          Type                      Required?   Description
============= ========================= =========== =======================================================
stock         int                       YES         The number of parts in stock
board_name    str                       YES         The board's name. Can also be thought of as the project's name
rev           str                       YES         The pcb's revision
sub_rev       str                                   The pcb's sub-revision
comments      str                                   Comments about the part
parts         list                      YES         A list containing all of the parts used for this project
============= ========================= =========== =======================================================

Parts List
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The parts is a list of dictionaries containing the all parts used for a particular board.

The dictionaries in this list is formatted as follows for a component:

============= ============= =======================================================
Key           Value Type    Description
============= ============= =======================================================
type          string        The component type (resistor, bjt, etc) which corresponds to the part's table name
part          dict          A dictionary describing the part
qty           int           The quantity of this part used in this board
designator    str           The part designator on the PCB
alternatives  list          A list of alternative parts that can be used, each part being the same format as the part key above. This list can be left as an empty array.
============= ============= =======================================================

The part key above is a dictionary containing a set of filter key-value pairs that narrows down a part.
The part key can either be specific to a IPN, or to a generic part with key-based selection. In both cases, the
`type` key is required to determine what part to look for.

For example, for a part with the ipn of "PART123", the part dict would be
.. code-block::

    {
        ipn: 'PART123'
    }

As the ipn is unique to each part, this filter would only find a single part. With a resistor
for example, where a specific part does not matter, the part dict would look something like
.. code-block::

    {
        resistance: 1000
        power: {val: 0.125, op: '>'}
        package: 0805
    }

The `>` prefix in `power: >0.125` indicates that the power value must be greater than 1/8W, and anything above that is fine as well.
