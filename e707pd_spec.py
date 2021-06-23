from dataclasses import dataclass


# Outline the different parts storage specifications
# {'db_name': "", 'showcase_name': "", 'db_type': "", 'show_as_type': "normal", 'required': False, },

"""
    The spec for components
"""
eedata_generic_spec = [
    {'db_name': 'stock', 'showcase_name': 'Stock', 'db_type': "INT NOT NULL", 'shows_as': "normal", 'required': True, },
    {'db_name': 'mfr_part_numb', 'showcase_name': 'Mfr Part #', 'db_type': "VARCHAR NOT NULL", "shows_as": "normal", 'required': True, },
    {'db_name': 'manufacturer', 'showcase_name': 'Manufacturer', 'db_type': "VARCHAR", "shows_as": "normal", 'required': False, },
    {'db_name': 'package', "showcase_name": "Package", "db_type": "VARCHAR(20) NOT NULL", "shows_as": "normal", 'required': True, },
    {'db_name': 'part_comments', "showcase_name": "Part Comments", "db_type": "MEDIUMTEXT", "shows_as": "normal", 'required': False, },
    {'db_name': 'user_comments', "showcase_name": "User Comments", "db_type": "MEDIUMTEXT", "shows_as": "normal", 'required': False, },
]

eedata_resistors_spec = eedata_generic_spec + [
    {'db_name': 'resistance', "showcase_name": "Resistance", "db_type": "FLOAT NOT NULL", "shows_as": "engineering", 'required': True, },
    {'db_name': 'tolerance', "showcase_name": "Tolerance", "db_type": "FLOAT", "shows_as": "percentage", 'required': False, },
    {'db_name': 'power', "showcase_name": "Power Rating", 'db_type': "FLOAT", 'shows_as': 'normal', 'required': False, }
]
eedata_resistor_display_order = ['stock', 'mfr_part_numb', 'manufacturer', 'resistance', 'tolerance', 'power', 'package', 'user_comments']

eedata_capacitor_spec = eedata_generic_spec + [
    {'db_name': 'capacitance', 'showcase_name': "Capacitance", 'db_type': "FLOAT NOT NULL", 'shows_as': "engineering", 'required': True, },
    {'db_name': 'tolerance', "showcase_name": "Tolerance", "db_type": "FLOAT", "shows_as": "percentage", 'required': False, },
    {'db_name': 'power', "showcase_name": "Power Rating", 'db_type': "FLOAT", 'shows_as': 'normal', 'required': False, },
    {'db_name': 'max_voltage', "showcase_name": "Voltage Rating", 'db_type': "FLOAT", 'shows_as': 'normal', 'required': False, },
    {'db_name': 'temp_coeff', "showcase_name": "Temperature Coefficient", 'db_type': "VARCHAR", 'shows_as': 'normal', 'required': False, },
    {'db_name': 'cap_type', "showcase_name": "Capacitor Type", 'db_type': "VARCHAR", 'shows_as': 'normal', 'required': False, },
]
eedata_capacitor_display_order = ['stock', 'mfr_part_numb', 'manufacturer', 'capacitance', 'tolerance', 'power', 'max_voltage', 'cap_type', 'temp_coeff', 'package', 'user_comments']

eedata_ic_spec = eedata_generic_spec + [
    {'db_name': 'ic_type', 'showcase_name': "IC Type", 'db_type': "VARCHAR NOT NULL", 'shows_as': 'normal', 'required': True},
]
eedata_ic_display_order = ['stock', 'mfr_part_numb', 'manufacturer', 'ic_type', 'part_comments', 'package', 'user_comments']

eedata_pcb_spec = [
    {'db_name': 'stock', 'showcase_name': 'Stock', 'db_type': "INT NOT NULL", 'shows_as': "normal", 'required': True, },
    {'db_name': 'rev', 'showcase_name': 'Revision', 'db_type': "VARCHAR", 'shows_as': "normal", 'required': True, },
    {'db_name': 'sub_rev', 'showcase_name': 'Sub-Revision', 'db_type': "VARCHAR", 'shows_as': "normal", 'required': False, },
    {'db_name': 'user_comments', "showcase_name": "User Comments", "db_type": "MEDIUMTEXT", "shows_as": "normal", 'required': False, },
    {'db_name': 'project_name', 'showcase_name': "Project Name", 'db_type': "VARCHAR NOT NULL", 'shows_as': 'normal', 'required': True},
]


@dataclass
class GenericItem:
    stock: int = None
    manufacturer: str = None
    mfr_part_numb: str = None
    package: str = None
    part_comments: str = None
    user_comments: str = None

    def __getitem__(self, key):
        return self.__dict__[key]

    def __setitem__(self, key, item):
        self.__dict__[key] = item


@dataclass
class Resistor(GenericItem):
    resistance: float = None
    tolerance: float = None
    power: float = None


@dataclass
class Capacitor(GenericItem):
    capacitance: float = None
    tolerance: float = None
    power: float = None
    max_voltage: float = None
    temp_coeff: str = None
    cap_type: str = None


@dataclass
class IC(GenericItem):
    ic_type: str = None


@dataclass
class PCB:
    stock: int = None
    rev: str = None
    sub_rev: str = None
    user_comments: str = None
    project_name: str = None


"""
    While not part of the spec, but these are handly for autofills
"""
autofill_helpers_list = {
    'ic_manufacturers': ["Microchip", "TI", "Analog Devices", "On-Semi", "STMicroelectronics",
                         "Cypress Semiconductors", "Infineon"],
    'ic_types': ["Microcontroller", "Boost Converter", "Buck Converter", "FPGA", "Battery Charger", "Battery Management",
                 "LED Driver", "Multiplexer"],
    'capacitor_types': ['electrolytic', 'ceramic', 'tantalum', 'paper', 'film'],
}


"""
    Now comes the projects spec    
"""