# E7EPD Rev 0.1 Database Specification
## A Work-In-Progress document

## Components 
All components will be based of the `GenericPart` table spec that contains common columns. 
Note that the `GenericPart` table doesn't exist by itself but is used in this document as columns that every 
other table should have

### Different Tables Per Components
To allow for the parameterization of parts, and due to SQL's column nature where it's usually unchanged, each
specific component type (like resistors, ADC, etc) will have its own SQL table.

### Table Spec
#### GenericPart Table:
|Name|SQL Type|Description|
|---|---|---|
|id|INTEGER PRIMARY KEY AUTOINCREMENT| Each row in the database will contain an unique SQL ID|
|stock| INT NOT NULL| The number of parts in stock |
|Manufacturer|VARCHAR| The manufacturer of the component|
|package|VARCHAR NOT NULL| The part's physical package|
|comments|MEDIUMTEXT| A user comment|

#### Resistor Table:
|Name|SQL Type|Description|
|---|---|---|
|resistance|FLOAT NOT NULL| The resistor's resistance|
|tolerance|FLOAT| The resistor's tolerance as a float (so a 5% resistor will be stored as 5|
|power|FLOAT| The resistor's power rating in W|

#### Capacitor Table:
|Name|SQL Type|Description|
|---|---|---|
|capacitance|FLOAT NOT NULL| The capacitor's capacitance|
|tolerance|FLOAT| The capacitor's tolerance as a float (so a 5% resistor will be stored as 5|
|power|FLOAT| The capacitor's power rating in W|
|voltage|FLOAT| The capacitor's maximum voltage rating|
|temp_coeff|VARCHAR(20)| The capacitor's temperature coefficient|
|type|VARCHAR(20)| The capacitor types, which should only be 'electrolytic', 'ceramic', 'tantalum', 'film'. If a type is not listed, you can enter a custom type, just make sure that it's consistent for different parts (also create an Issue on the Github page so we can all have it :)|

#### Microcontroller Table:
|Name|SQL Type|Description|
|---|---|---|
|core_size|VARCHAR| The core size of the microcontroller (8-bit, 16-bit, 32-bit, etc)|
|architecture|VARCHAR| The architecture of the mcu's core (AVR, ARM M0, etc)|
|max_clock|INT| The maximum clock speed|
|max_voltage|FLOAT| The maximum voltage allowed on the mcu|
|min_voltage|FLOAT| The minimum voltage needed for the mcu to work|
|flash_size|INT| The flash size|
|ram_size|INT| The RAM size|
|eeprom_size|INT| The EEPROM size if applicable|

## Projects:
TODO
