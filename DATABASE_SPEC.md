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
|comments|MEDIUMTEXT| A user comment|

#### Resistor Table:
|Name|SQL Type|Description|
|---|---|---|
|resistance|FLOAT NOT NULL| The resistor's resistance|
|tolerance|FLOAT| The resistor's tolerance as a float (so a 5% resistor will be stored as 5|
|package|VARCHAR NOT NULL| The resistor's physical package|
|power|FLOAT| The resistor's power rating in W|


## Projects:
TODO
