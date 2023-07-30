import dataclasses
import enum
import typing
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import Column, Integer, Float, String, Text, JSON, ForeignKey

default_string_len = 30

_AlchemyDeclarativeBase = declarative_base()

class Parts(_AlchemyDeclarativeBase):
    """
    A table for describing parts
    All parameters for this part are foreign keys in the `parts_parameters` table.
    """
    __tablename__ = 'parts'

    ipn = Column(String(default_string_len), nullable=False, primary_key=True, autoincrement=False, unique=True)
    mfr_part_numb = Column(String(default_string_len), nullable=False)
    stock = Column(Integer, nullable=False)
    manufacturer = Column(String(default_string_len))
    storage = Column(String(default_string_len))
    package = Column(String(default_string_len))
    comments = Column(Text)
    datasheet = Column(Text)
    user = Column(Integer, ForeignKey('users.id'), back_populates="parts", nullable=True)
    type = Column(Integer, ForeignKey('part_types.id'))
    part_other_params = relationship("parts_parameters", back_populates="parts", cascade="all, delete")


class ParameterTypes(_AlchemyDeclarativeBase):
    """
    This table is for part types (resistors, capacitors, etc)

    This table can be foreign keyed by the `parts` and `pcb_assembly_parts` table
    """
    __tablename__ = 'part_types'

    id = Column(Integer, primary_key=True)
    name = Column(String(default_string_len))
    part = relationship("parts")                        # Reference to the part it uses
    pcb_parts = relationship("pcb_assembly_parts")      # Reference to the part it uses


class PartsParameters(_AlchemyDeclarativeBase):
    """
    This table has the part's parameters, which each row references a specific part in the `part` table
    """
    __tablename__ = 'parts_parameters'

    id = Column(Integer, primary_key=True)
    ipn = Column(String(default_string_len), ForeignKey('parts.ipn'))
    key = Column(Float, nullable=False)
    value = Column(String(default_string_len))

class PCBAssembly(_AlchemyDeclarativeBase):
    __tablename__ = 'pcb_assembly'

    id = Column(Integer, primary_key=True)
    stock = Column(Integer, nullable=False)
    comments = Column(String(default_string_len))
    storage = Column(String(default_string_len))
    board_name = Column(String(default_string_len), nullable=False)
    rev = Column(String(default_string_len), nullable=False)
    parts = Column(Integer, ForeignKey('pcb_assembly_parts.id'))

class PCBParameters(_AlchemyDeclarativeBase):
    __tablename__ = 'pcb_assembly_parts'

    id = Column(Integer, primary_key=True)
    pcb_id = Column(Integer, ForeignKey('pcb_assembly.id'))
    quantity = Column(Integer, nullable=False)
    parts_id = Column(String(default_string_len), ForeignKey('parts.ipn'), nullable=True)   # Can be null for a non-specific part
    type = Column(Integer, ForeignKey('part_types.id'))
    text_spec = Column(String(default_string_len))

class Users(_AlchemyDeclarativeBase):
    """
    Table for storing different users
    """
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    name = Column(String(default_string_len))   # Can be null for a non-specific part
    email = Column(String(default_string_len), nullable=True)
    parts = relationship("parts")


# Outline the different parts storage specifications
# {'db_name': "", 'showcase_name': "", 'db_type': "", 'show_as_type': "normal", 'required': False, },

class ShowAsEnum(enum.Enum):
    normal = enum.auto()            # Display it as regular text/number
    engineering = enum.auto()       # Show it in engineering notation
    precentage = enum.auto()        # Show it as a percentage
    fraction = enum.auto()


@dataclasses.dataclass
class SpecLineItem:
    db_name: str            # how this gets stored in the database
    showcase_name: str      # How to showcase this line item to the user
    shows_as: ShowAsEnum    # How to display it to user
    input_type: type        # What Python type to use
    required: bool          # Is this item required?

"""
    The spec for any component. NOTE: this MUST match the parts table's keys
"""
eedata_generic_spec = [     # type: typing.List[SpecLineItem]
    SpecLineItem('stock', 'Stock', ShowAsEnum.normal, int, True),
    SpecLineItem('ipn', 'IPN', ShowAsEnum.normal, str, True),
    SpecLineItem('mfr_part_numb', 'Mfr Part #', ShowAsEnum.normal, str, False),
    SpecLineItem('manufacturer', 'Manufacturer', ShowAsEnum.normal, str, False),
    SpecLineItem('package', 'Package', ShowAsEnum.normal, str, True),
    SpecLineItem('storage', 'Storage Location', ShowAsEnum.normal, str, False),
    SpecLineItem('comments', 'Comments', ShowAsEnum.normal, str, False),
    SpecLineItem('datasheet', 'Datasheet', ShowAsEnum.normal, str, False),
    # SpecLineItem('user', 'User', ShowAsEnum.normal, str, False),      # Handled separately
]
eedata_generic_items = [i.db_name for i in eedata_generic_spec]
eedata_generic_items_preitems = ['stock', 'mfr_part_numb', 'manufacturer']
eedata_generic_items_postitems = ['package', 'storage', 'comments', 'datasheet', 'user']

eedata_resistors_params = [     # type: typing.List[SpecLineItem]
    SpecLineItem('resistance', 'Resistance', ShowAsEnum.engineering, float, True),
    SpecLineItem('tolerance', 'Tolerance', ShowAsEnum.precentage, float, False),
    SpecLineItem('power', 'Power Rating', ShowAsEnum.fraction, float, False),
]
eedata_resistor_display_order = eedata_generic_items_preitems+[i.db_name for i in eedata_resistors_params]+eedata_generic_items_postitems

eedata_capacitor_params = eedata_generic_spec + [
    {'db_name': 'capacitance', 'showcase_name': 'Capacitance', 'shows_as': 'engineering', 'input_type': 'float', 'required': True, },
    {'db_name': 'tolerance', 'showcase_name': 'Tolerance', 'shows_as': 'percentage', 'input_type': 'float', 'required': False, },
    {'db_name': 'max_voltage', 'showcase_name': 'Voltage Rating', 'shows_as': 'normal', 'input_type': 'float', 'required': False, },
    {'db_name': 'temp_coeff', 'showcase_name': 'Temperature Coefficient', 'shows_as': 'normal', 'input_type': 'str', 'required': False, },
    {'db_name': 'cap_type', 'showcase_name': 'Capacitor Type', 'shows_as': 'normal', 'input_type': 'str', 'required': False, },
]
eedata_capacitor_display_order = eedata_generic_items_preitems+['capacitance', 'tolerance', 'max_voltage', 'cap_type', 'temp_coeff']+eedata_generic_items_postitems

eedata_ic_params = eedata_generic_spec + [
    {'db_name': 'ic_type', 'showcase_name': 'IC Type', 'shows_as': 'normal', 'input_type': 'str', 'required': True},
]
eedata_ic_display_order = eedata_generic_items_preitems+['ic_type']+eedata_generic_items_postitems

eedata_inductor_params = eedata_generic_spec + [
    {'db_name': 'inductance', 'showcase_name': 'Inductance', 'shows_as': 'engineering', 'input_type': 'float', 'required': True, },
    {'db_name': 'tolerance', 'showcase_name': 'Tolerance', 'shows_as': 'percentage', 'input_type': 'float', 'required': False, },
    {'db_name': 'max_current', 'showcase_name': 'Max Current', 'shows_as': 'engineering', 'input_type': 'float', 'required': False, },
]
eedata_inductor_display_order = eedata_generic_items_preitems+['inductance', 'tolerance', 'max_current']+eedata_generic_items_postitems

eedata_diode_params = eedata_generic_spec + [
    {'db_name': 'diode_type', 'showcase_name': 'Diode Type', 'shows_as': 'normal', 'input_type': 'str', 'required': True, },
    {'db_name': 'max_current', 'showcase_name': 'Peak Current', 'shows_as': 'engineering', 'input_type': 'float', 'required': False, },
    {'db_name': 'average_current', 'showcase_name': 'Average Current', 'shows_as': 'engineering', 'input_type': 'float', 'required': False, },
    {'db_name': 'max_rv', 'showcase_name': 'Max Reverse Voltage', 'shows_as': 'engineering', 'input_type': 'float', 'required': False, },
]
eedata_diode_display_order = eedata_generic_items_preitems+['diode_type', 'max_rv', 'average_current', 'max_current']+eedata_generic_items_postitems

eedata_crystal_params = eedata_generic_spec + [
    {'db_name': 'frequency', 'showcase_name': 'Frequency', 'shows_as': 'engineering', 'input_type': 'float', 'required': True, },
    {'db_name': 'load_c', 'showcase_name': 'Load Capacitance (pF)', 'shows_as': 'engineering', 'input_type': 'float', 'required': False, },
    {'db_name': 'esr', 'showcase_name': 'ESR', 'shows_as': 'engineering', 'input_type': 'float', 'required': False, },
    {'db_name': 'stability_ppm', 'showcase_name': 'Stability (ppm)', 'shows_as': 'normal', 'input_type': 'float', 'required': False, },
]
eedata_crystal_display_order = eedata_generic_items_preitems+['frequency', 'load_c', 'esr', 'stability_ppm']+eedata_generic_items_postitems

eedata_mosfet_params = eedata_generic_spec + [
    {'db_name': 'mosfet_type', 'showcase_name': 'Type', 'shows_as': 'normal', 'input_type': 'str', 'required': True, },
    {'db_name': 'vdss', 'showcase_name': 'Max Drain-Source Voltage', 'shows_as': 'engineering', 'input_type': 'float', 'required': False, },
    {'db_name': 'vgss', 'showcase_name': 'Max Gate-Source Voltage', 'shows_as': 'engineering', 'input_type': 'float', 'required': False, },
    {'db_name': 'vgs_th', 'showcase_name': 'Gate-Source Threshold Voltage', 'shows_as': 'engineering', 'input_type': 'float', 'required': False, },
    {'db_name': 'i_d', 'showcase_name': 'Max Drain Current', 'shows_as': 'engineering', 'input_type': 'float', 'required': False, },
    {'db_name': 'i_d_pulse', 'showcase_name': 'Max Drain Peak Current', 'shows_as': 'engineering', 'input_type': 'float', 'required': False, },
]
eedata_mosfet_display_order = eedata_generic_items_preitems+['mosfet_type', 'vdss', 'vgss', 'vgs_th', 'i_d', 'i_d_pulse']+eedata_generic_items_postitems

eedata_bjt_params = eedata_generic_spec + [
    {'db_name': 'bjt_type', 'showcase_name': 'Type', 'shows_as': 'normal', 'input_type': 'str', 'required': True, },
    {'db_name': 'vcbo', 'showcase_name': 'Max Collector-Base Voltage', 'shows_as': 'engineering', 'input_type': 'float', 'required': False, },
    {'db_name': 'vceo', 'showcase_name': 'Max Collector-Emitter Voltage', 'shows_as': 'engineering', 'input_type': 'float', 'required': False, },
    {'db_name': 'vebo', 'showcase_name': 'Max Emitter-Base Voltage', 'shows_as': 'engineering', 'input_type': 'float', 'required': False, },
    {'db_name': 'i_c', 'showcase_name': 'Max Cont. Collector Current', 'shows_as': 'engineering', 'input_type': 'float', 'required': False, },
    {'db_name': 'i_c_peak', 'showcase_name': 'Max Peak Collector Current', 'shows_as': 'engineering', 'input_type': 'float', 'required': False, },
]
eedata_bjt_display_order = eedata_generic_items_preitems+['bjt_type', 'vcbo', 'vceo', 'vebo', 'i_c', 'i_c_peak']+eedata_generic_items_postitems

eedata_connector_params = eedata_generic_spec + [
    {'db_name': 'conn_type', 'showcase_name': 'Type', 'shows_as': 'normal', 'input_type': 'str', 'required': True, },
]
eedata_connector_display_order = eedata_generic_items_preitems+['conn_type']+eedata_generic_items_postitems

eedata_led_params = eedata_generic_spec + [
    {'db_name': 'led_type', 'showcase_name': 'LED Type', 'shows_as': 'normal', 'input_type': 'str', 'required': True, },
    {'db_name': 'vf', 'showcase_name': 'LED forward voltage', 'shows_as': 'engineering', 'input_type': 'float', 'required': False, },
    {'db_name': 'max_i', 'showcase_name': 'Max Current', 'shows_as': 'engineering', 'input_type': 'float', 'required': False, },
]
eedata_led_display_order = eedata_generic_items_preitems+['led_type', 'vf', 'max_i']+eedata_generic_items_postitems

eedata_fuse_params = eedata_generic_spec + [
    {'db_name': 'fuse_type', 'showcase_name': 'Fuse Type', 'shows_as': 'normal', 'input_type': 'str', 'required': True, },
    {'db_name': 'max_v', 'showcase_name': 'Fuse Max Voltage', 'shows_as': 'engineering', 'input_type': 'float', 'required': False, },
    {'db_name': 'max_i', 'showcase_name': 'Max Current', 'shows_as': 'engineering', 'input_type': 'float', 'required': False, },
    {'db_name': 'trip_i', 'showcase_name': 'Trip Current', 'shows_as': 'engineering', 'input_type': 'float', 'required': False, },
    {'db_name': 'hold_i', 'showcase_name': 'Hold Current', 'shows_as': 'engineering', 'input_type': 'float', 'required': False, },
]
eedata_fuse_display_order = eedata_generic_items_preitems+['fuse_type', 'max_v', 'trip_i', 'hold_i', 'max_i']+eedata_generic_items_postitems

eedata_button_params = eedata_generic_spec + [
    {'db_name': 'bt_type', 'showcase_name': 'Button Type', 'shows_as': 'normal', 'input_type': 'str', 'required': True},
    {'db_name': 'circuit_t', 'showcase_name': 'Button Circuit', 'shows_as': 'normal', 'input_type': 'str', 'required': False},
    {'db_name': 'max_v', 'showcase_name': 'Voltage Rating', 'shows_as': 'engineering', 'input_type': 'float', 'required': False, },
    {'db_name': 'max_i', 'showcase_name': 'Current Rating', 'shows_as': 'engineering', 'input_type': 'float', 'required': False, },
]
eedata_button_display_order = eedata_generic_items_preitems+['bt_type', 'circuit_t', 'max_v', 'max_i']+eedata_generic_items_postitems

eedata_misc_spec = eedata_generic_spec
eedata_misc_display_order = eedata_generic_items_preitems+eedata_generic_items_postitems

eedata_pcb_params = [
    {'db_name': 'stock', 'showcase_name': 'Stock', 'shows_as': 'normal', 'input_type': 'int', 'required': True, },
    {'db_name': 'rev', 'showcase_name': 'Revision', 'shows_as': 'normal', 'input_type': 'str', 'required': True, },
    {'db_name': 'comments', 'showcase_name': 'Comments', 'shows_as': 'normal', 'input_type': 'str', 'required': False, },
    {'db_name': 'storage', 'showcase_name': 'Storage Location', 'shows_as': 'normal', 'input_type': 'str', 'required': False, },
    {'db_name': 'board_name', 'showcase_name': 'Board Name', 'shows_as': 'normal', 'input_type': 'str', 'required': True},
]
eedata_pcb_display_order = ['stock', 'board_name', 'rev', 'parts', 'storage', 'comments']



"""
    While not part of the spec, but these are handly for autofills
"""
autofill_helpers_list = {
    'ic_manufacturers': ["MICROCHIP", "TI", "ANALOG DEVICES", "ON-SEMI", "STMICROELECTRONICS",
                         "CYPRESS SEMI", "INFINEON"],
    'ic_types': ["Microcontroller", "Boost Converter", "Buck Converter", "FPGA", "Battery Charger", "Battery Management",
                 "LED Driver", "Multiplexer"],
    'capacitor_types': ['Electrolytic', 'Ceramic', 'Tantalum', 'Paper', 'Film'],
    'diode_type': ['Regular', 'Zener', 'Schottky', 'TSV'],
    'passive_manufacturers': ['STACKPOLE', 'MURATA ELECTRONICS', 'SAMSUNG ELECTRO-MECHANICS', 'TAIYO YUDEN', 'TDK'],
    'passive_packages': ['0201', '0603', '0805', '1206'],
    'ic_packages': ['SOT23', 'SOT23-5', 'SOT23-6',
                    'DIP-4', 'DIP-8', 'DIP-14', 'DIP-16', 'DIP-18', 'DIP-28',
                    'SOIC-8', 'SIOC-14', 'SOIC-16', 'SOIC-18'],
    'mosfet_types': ['N-Channel', 'P-Channel'],
    'bjt_types': ['NPN', 'PNP'],
    'fuse_types': ['PTC', 'Fast Blow', 'Slow Blow'],
    'led_types': ['Red', 'Green', 'Blue', 'RGB', 'Addressable']
}

"""
    If this is ran it itself, do a test where it checks if the display order for each spec has all keys
"""
if __name__ == '__main__':
    print("Running Test")
    # spec_and_disp_arr = [['resistor', eedata_resistors_params, eedata_resistor_display_order, Resistor],
    #                      ['capacitor', eedata_capacitor_params, eedata_capacitor_display_order, Capacitor],
    #                      ['ic', eedata_ic_spec, eedata_ic_display_order, IC],
    #                      ['inductor', eedata_inductor_spec, eedata_inductor_display_order, Inductor],
    #                      ['diode', eedata_diode_spec, eedata_diode_display_order, Diode],
    #                      ['pcb', eedata_pcb_spec, eedata_pcb_display_order, PCB],
    #                      ['crystal', eedata_crystal_spec, eedata_crystal_display_order, Crystal],
    #                      ['mosfet', eedata_mosfet_spec, eedata_mosfet_display_order, MOSFET],
    #                      ['bjt', eedata_bjt_spec, eedata_bjt_display_order, BJT],
    #                      ['connectors', eedata_connector_spec, eedata_connector_display_order, Connector],
    #                      ['led', eedata_led_spec, eedata_led_display_order, LED],
    #                      ['fuse', eedata_fuse_spec, eedata_fuse_display_order, Fuse],
    #                      ['button', eedata_button_spec, eedata_button_display_order, Button],
    #                      ['misc', eedata_misc_spec, eedata_misc_display_order, MiscComp]]
    # for spec in spec_and_disp_arr:
    #     for i in spec[1]:
    #         if i['db_name'] not in spec[2]:
    #             raise AssertionError("Spec '{}' not in {}".format(i['db_name'], spec[0]))
    #
    #         if not hasattr(spec[3], i['db_name']):
    #             raise AssertionError("Extra name in spec dict for {} = {}".format(spec[0], i['db_name']))
    print("Done with test")
