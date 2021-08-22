E7EPD Database Specification 
================================================
**Rev 0.3PRE**

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
============= ========================= =========== =======================================================

Resistor Table
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Append the *GenericPart* Table to this table.

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

============= ========================= =========== =======================================================
Name          SQL Type                  Required?   Description
============= ========================= =========== =======================================================
ic_type       VARCHAR                   YES         The IC type, for example microcontroller, ADC, comparator, etc.
============= ========================= =========== =======================================================

Crystal Table
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Append the *GenericPart* Table to this table.

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

PCBs Table
---------------------------------
============= ========================= =========== =======================================================
Name          SQL Type                  Required?   Description
============= ========================= =========== =======================================================
id            INTEGER PRIMARY KEY       YES         Each row in the database will contain an unique SQL ID
stock         INT                       YES         The number of parts in stock
rev           VARCHAR                   YES         The project's revision
sub_rev       VARCHAR                               The project's sub-revision
project_name  VARCHAR                   YES         The project name related to this part. The project should match that of the Projects database (upcoming in Rev 0.2)
comments      TEXT                                  Comments about the part
============= ========================= =========== =======================================================

Projects
---------------------------------
TODO, in a future revision

