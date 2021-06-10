from dataclasses import dataclass


# Outline the different parts storage specifications
# {'db_name': "", 'showcase_name': "", 'db_type': "", 'show_as_type': "normal", 'required': False, },

eedata_generic_spec = [
    {'db_name': 'stock', 'showcase_name': 'Stock', 'db_type': "INT NOT NULL", 'shows_as': "normal", 'required': True, },
    {'db_name': 'manufacturer', 'showcase_name': 'Manufacturer', 'db_type': "VARCHAR", "shows_as": "normal", 'required': False, },
    {'db_name': 'mfr_part_numb', 'showcase_name': 'Mfr Part #', 'db_type': "VARCHAR", "shows_as": "normal", 'required': False, },
    {'db_name': 'package', "showcase_name": "Package", "db_type": "VARCHAR(20) NOT NULL", "shows_as_type": "normal", 'required': True, },
    {'db_name': 'comments', "showcase_name": "Comments", "db_type": "MEDIUMTEXT", "shows_as_type": "normal", 'required': False, },
]

eedata_resistors_spec = eedata_generic_spec + [
    {'db_name': 'resistance', "showcase_name": "Resistance", "db_type": "FLOAT NOT NULL", "shows_as_type": "engineering", 'required': True, },
    {'db_name': 'tolerance', "showcase_name": "Tolerance", "db_type": "FLOAT", "shows_as_type": "percentage", 'required': False, },
    {'db_name': 'power', "showcase_name": "Power Rating", 'db_type': "FLOAT", 'show_as_type': 'normal', 'required': False, }
]

eedata_capacitor_spec = eedata_generic_spec + [
    {'db_name': 'capacitance', 'showcase_name': "Capacitance", 'db_type': "FLOAT NOT NULL", 'show_as_type': "engineering", 'required': True, },
    {'db_name': 'tolerance', "showcase_name": "Tolerance", "db_type": "FLOAT", "shows_as_type": "percentage", 'required': False, },
    {'db_name': 'power', "showcase_name": "Power Rating", 'db_type': "FLOAT", 'show_as_type': 'normal', 'required': False, },
    {'db_name': 'voltage', "showcase_name": "Voltage Rating", 'db_type': "FLOAT", 'show_as_type': 'normal', 'required': False, },
    {'db_name': 'temp_coeff', "showcase_name": "Temperature Coefficient", 'db_type': "VARCHAR(20)", 'show_as_type': 'normal', 'required': False, },
]

eedata_microcontroller_spec = eedata_generic_spec + [
    {'db_name': "core_size", 'showcase_name': "Core Size", 'db_type': "VARCHAR", 'show_as_type': "normal", 'required': False, },
    {'db_name': "architecture", 'showcase_name': "Architecture", 'db_type': "VARCHAR", 'show_as_type': "normal", 'required': False, },
    {'db_name': "max_clock", 'showcase_name': "Maximum Clock Speed", 'db_type': "INT", 'show_as_type': "engineering", 'required': False, },
    {'db_name': "max_voltage", 'showcase_name': "Maximum Voltage", 'db_type': "FLOAT", 'show_as_type': "normal", 'required': False, },
    {'db_name': "min_voltage", 'showcase_name': "Minimum Voltage", 'db_type': "FLOAT", 'show_as_type': "normal", 'required': False, },
    {'db_name': "flash_size", 'showcase_name': "Flash Size", 'db_type': "INT", 'show_as_type': "engineering", 'required': False, },
    {'db_name': "ram_size", 'showcase_name': "RAM Size", 'db_type': "INT", 'show_as_type': "engineering", 'required': False, },
    {'db_name': "eeprom_size", 'showcase_name': "EEPROM Size", 'db_type': "INT", 'show_as_type': "engineering", 'required': False, },
]


@dataclass
class GenericItem:
    stock: int = 0
    mfr_part_numb: str = None
    package: str = None
    comments: str = None
    manufacturer: str = None

    def __getitem__(self, key):
        return self.__dict__[key]

    def __setitem__(self, key, item):
        self.__dict__[key] = item


@dataclass
class Resistor(GenericItem):
    resistance: float = None
    package: str = None
    power: float = None
    tolerance: float = None


@dataclass
class Capacitor(GenericItem):
    capacitance: float = None
    power: float = None
    tolerance: float = None
    voltage: float = None
    temp_coeff: str = None


@dataclass
class Microcontroller(GenericItem):
    core_size: str = None
    architecture: str = None
    max_clock: int = None
    max_voltage: float = None
    min_voltage: float = None
    flash_size: int = None
    ram_size: int = None
    eeprom_size: int = None
