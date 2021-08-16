from dataclasses import dataclass
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, Float, String

_default_string_len = 30

class Base(object):
    id = Column(Integer, primary_key=True)
    stock = Column(Integer)
    manufacturer = Column(String(_default_string_len))
    storage = Column(String(_default_string_len))
    mfr_part_numb = Column(String(_default_string_len), nullable=False)
    package = Column(String(_default_string_len))
    part_comments = Column(String(_default_string_len))
    user_comments = Column(String(_default_string_len))

    def __getitem__(self, key):
        return self.__dict__[key]

    def __setitem__(self, key, item):
        self.__dict__[key] = item


GenericItem = declarative_base(cls=Base)


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
    {'db_name': 'storage', 'showcase_name': 'Storage Location', 'db_type': "VARCHAR", "shows_as": "normal", 'required': False, },
    {'db_name': 'part_comments', "showcase_name": "Part Comments", "db_type": "MEDIUMTEXT", "shows_as": "normal", 'required': False, },
    {'db_name': 'user_comments', "showcase_name": "User Comments", "db_type": "MEDIUMTEXT", "shows_as": "normal", 'required': False, },
]

eedata_resistors_spec = eedata_generic_spec + [
    {'db_name': 'resistance', "showcase_name": "Resistance", "db_type": "FLOAT NOT NULL", "shows_as": "engineering", 'required': True, },
    {'db_name': 'tolerance', "showcase_name": "Tolerance", "db_type": "FLOAT", "shows_as": "percentage", 'required': False, },
    {'db_name': 'power', "showcase_name": "Power Rating", 'db_type': "FLOAT", 'shows_as': 'normal', 'required': False, }
]
eedata_resistor_display_order = ['stock', 'mfr_part_numb', 'manufacturer', 'resistance', 'tolerance', 'power', 'package', 'part_comments', 'user_comments']

eedata_capacitor_spec = eedata_generic_spec + [
    {'db_name': 'capacitance', 'showcase_name': "Capacitance", 'db_type': "FLOAT NOT NULL", 'shows_as': "engineering", 'required': True, },
    {'db_name': 'tolerance', "showcase_name": "Tolerance", "db_type": "FLOAT", "shows_as": "percentage", 'required': False, },
    {'db_name': 'power', "showcase_name": "Power Rating", 'db_type': "FLOAT", 'shows_as': 'normal', 'required': False, },
    {'db_name': 'max_voltage', "showcase_name": "Voltage Rating", 'db_type': "FLOAT", 'shows_as': 'normal', 'required': False, },
    {'db_name': 'temp_coeff', "showcase_name": "Temperature Coefficient", 'db_type': "VARCHAR", 'shows_as': 'normal', 'required': False, },
    {'db_name': 'cap_type', "showcase_name": "Capacitor Type", 'db_type': "VARCHAR", 'shows_as': 'normal', 'required': False, },
]
eedata_capacitor_display_order = ['stock', 'mfr_part_numb', 'manufacturer', 'capacitance', 'tolerance', 'power', 'max_voltage', 'cap_type', 'temp_coeff', 'package', 'part_comments', 'user_comments']

eedata_ic_spec = eedata_generic_spec + [
    {'db_name': 'ic_type', 'showcase_name': "IC Type", 'db_type': "VARCHAR NOT NULL", 'shows_as': 'normal', 'required': True},
]
eedata_ic_display_order = ['stock', 'mfr_part_numb', 'manufacturer', 'ic_type', 'part_comments', 'package', 'user_comments']

eedata_inductor_spec = eedata_generic_spec + [
    {'db_name': 'inductance', "showcase_name": "Tolerance", "db_type": "FLOAT NOT NULL", "shows_as": "engineering", 'required': True, },
    {'db_name': 'tolerance', "showcase_name": "Tolerance", "db_type": "FLOAT", "shows_as": "percentage", 'required': False, },
    {'db_name': 'max_current', "showcase_name": "Tolerance", "db_type": "FLOAT", "shows_as": "engineering", 'required': False, },
]
eedata_inductor_display_order = ['stock', 'mfr_part_numb', 'manufacturer', 'inductance', 'tolerance', 'max_current', 'package', 'part_comments', 'user_comments']

eedata_diode_spec = eedata_generic_spec + [
    {'db_name': 'diode_type', "showcase_name": "Diode Type", "db_type": "VARCHAR NOT NULL", "shows_as": "normal", 'required': True, },
    {'db_name': 'max_current', "showcase_name": "Peak Current", "db_type": "FLOAT", "shows_as": "engineering", 'required': False, },
    {'db_name': 'average_current', "showcase_name": "Average Current", "db_type": "FLOAT", "shows_as": "engineering", 'required': False, },
    {'db_name': 'max_rv', "showcase_name": "Max Reverse Voltage", "db_type": "FLOAT", "shows_as": "engineering", 'required': False, },
]
eedata_diode_display_order = ['stock', 'mfr_part_numb', 'manufacturer', 'diode_type', 'max_rv', 'average_current', 'max_current', 'package', 'part_comments', 'user_comments']

eedata_pcb_spec = [
    {'db_name': 'stock', 'showcase_name': 'Stock', 'db_type': "INT NOT NULL", 'shows_as': "normal", 'required': True, },
    {'db_name': 'rev', 'showcase_name': 'Revision', 'db_type': "VARCHAR", 'shows_as': "normal", 'required': True, },
    {'db_name': 'sub_rev', 'showcase_name': 'Sub-Revision', 'db_type': "VARCHAR", 'shows_as': "normal", 'required': False, },
    {'db_name': 'user_comments', "showcase_name": "User Comments", "db_type": "MEDIUMTEXT", "shows_as": "normal", 'required': False, },
    {'db_name': 'project_name', 'showcase_name': "Project Name", 'db_type': "VARCHAR NOT NULL", 'shows_as': 'normal', 'required': True},
]


class Resistor(GenericItem):
    __tablename__ = 'resistance'

    resistance = Column(Float)
    tolerance = Column(Float)
    power = Column(Float)


class Capacitor(GenericItem):
    __tablename__ = 'capacitor'

    capacitance = Column(Float)
    tolerance = Column(Float)
    power = Column(Float)
    max_voltage = Column(Float)
    temp_coeff = Column(String)
    cap_type = Column(String)


class Inductor(GenericItem):
    __tablename__ = 'inductor'

    inductance = Column(Float)
    tolerance = Column(Float)
    max_current = Column(Float)


class Diode(GenericItem):
    __tablename__ = 'diode'

    diode_type = Column(String)
    max_current = Column(Float)
    average_current = Column(Float)
    max_rv = Column(Float)


class IC(GenericItem):
    __tablename__ = 'ic'

    ic_type = Column(String)


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
    'diode_type': ['Regular', 'Zener', 'Schottky', 'TSV'],
    'passive_packages': ['0201', '0603', '0805', '1206'],
    'ic_packages': ['SOT23', 'SOT23-5',
                    'DIP-4', 'DIP-8', 'DIP-14', 'DIP-16', 'DIP-18', 'DIP-28',
                    'SOIC-8, SIOC-14, SOIC-16, SOIC-18']
}


"""
    Now comes the projects spec    
"""