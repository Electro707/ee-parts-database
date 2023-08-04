import dataclasses
from dataclasses import dataclass, field, asdict
import enum
import typing


# Outline the different parts storage specifications
# {'db_name': "", 'showcase_name': "", 'db_type': "", 'show_as_type': "normal", 'required': False, },

class ShowAsEnum(enum.Enum):
    normal = enum.auto()            # Display it as regular text/number
    engineering = enum.auto()       # Show it in engineering notation
    precentage = enum.auto()        # Show it as a percentage
    fraction = enum.auto()

class UnicodeCharacters(enum.Enum):
    Omega = '\u03A9'
    mu = '\u03BC'

@dataclasses.dataclass
class SpecLineItem:
    db_name: str            # how this gets stored in the database
    showcase_name: str      # How to showcase this line item to the user
    shows_as: ShowAsEnum    # How to display it to user
    input_type: type        # What Python type to use
    required: bool          # Is this item required?
    append_str: str = ""    # What to append to this (units) when displayed


@dataclasses.dataclass
class UserSpec:
    """
    A dataclass stating how a user should be stored in the database
    """
    name: str
    email: str = ""
    phone: str = ""


"""
The spec for any component. NOTE: this MUST match the parts table's keys
"""
@dataclasses.dataclass
class _GenericPartClass:
    stock: int = field(metadata=asdict(SpecLineItem('stock', 'Stock', ShowAsEnum.normal, int, True)))
    ipn: str = field(metadata=asdict(SpecLineItem('ipn', 'IPN', ShowAsEnum.normal, str, True)))
    package: str = field(metadata=asdict(SpecLineItem('mfr_part_numb', 'Mfr Part #', ShowAsEnum.normal, str, False)))
    _: dataclasses.KW_ONLY
    mfr_part_numb: str = field(default=None, metadata=asdict(SpecLineItem('manufacturer', 'Manufacturer', ShowAsEnum.normal, str, False)))
    manufacturer: str = field(default=None, metadata=asdict(SpecLineItem('package', 'Package', ShowAsEnum.normal, str, True),))
    storage: str = field(default=None, metadata=asdict(SpecLineItem('storage', 'Storage Location', ShowAsEnum.normal, str, False),))
    comments: str = field(default=None, metadata=asdict(SpecLineItem('comments', 'Comments', ShowAsEnum.normal, str, False),))
    datasheet: str = field(default=None, metadata=asdict(SpecLineItem('datasheet', 'Datasheet', ShowAsEnum.normal, str, False),))
    user: str = field(default=None, metadata=asdict(SpecLineItem('user', 'User', ShowAsEnum.normal, str, False),))


eedata_generic_items_preitems = ('stock', 'ipn', 'mfr_part_numb', 'manufacturer')
eedata_generic_items_postitems = ('package', 'storage', 'comments', 'datasheet', 'user')


@dataclasses.dataclass
class Resistor(_GenericPartClass):
    resistance: float = field(default=None, metadata=asdict(SpecLineItem('resistance', 'Resistance', ShowAsEnum.engineering, float, True, f'{UnicodeCharacters.Omega:s}')))
    tolerance: float = field(default=None, metadata=asdict(SpecLineItem('tolerance', 'Tolerance', ShowAsEnum.precentage, float, False)), kw_only=True)
    power: float = field(default=None, metadata=asdict(SpecLineItem('power', 'Power Rating', ShowAsEnum.fraction, float, False)), kw_only=True)


eedata_resistor_display_order = eedata_generic_items_preitems+dataclasses.fields(Resistor)+eedata_generic_items_postitems


@dataclasses.dataclass
class Capacitor(_GenericPartClass):
    capacitance: float = field(default=None, metadata=asdict(SpecLineItem('capacitance', 'Capacitance', ShowAsEnum.engineering, float, True, f'F')))
    tolerance: float = field(default=None, metadata=asdict(SpecLineItem('tolerance', 'Tolerance', ShowAsEnum.precentage, float, False)))
    max_voltage: float = field(default=None, metadata=asdict(SpecLineItem('max_voltage', 'Voltage Rating', ShowAsEnum.normal, float, False, 'V')))
    temp_coeff: float = field(default=None, metadata=asdict(SpecLineItem('temp_coeff', 'Temperature Coefficient', ShowAsEnum.normal, str, False)))
    cap_type: str = field(default=None, metadata=asdict(SpecLineItem('cap_type', 'Capacitor Type', ShowAsEnum.normal, str, False)))


eedata_capacitor_display_order = eedata_generic_items_preitems+('capacitance', 'tolerance', 'max_voltage', 'cap_type', 'temp_coeff')+eedata_generic_items_postitems

@dataclasses.dataclass
class IC(_GenericPartClass):
    ic_type: str = field(default=None, metadata=asdict(SpecLineItem('ic_type', 'IC Type', ShowAsEnum.normal, str, True)))


eedata_ic_display_order = eedata_generic_items_preitems+['ic_type']+eedata_generic_items_postitems


@dataclasses.dataclass
class Inductor(_GenericPartClass):
    inductance: str = field(default=None, metadata=asdict(SpecLineItem('inductance', 'Inductance', ShowAsEnum.engineering, float, True, f'H')))
    tolerance: str = field(default=None, metadata=asdict(SpecLineItem('tolerance', 'Tolerance', ShowAsEnum.precentage, float, False)))
    max_current: str = field(default=None, metadata=asdict(SpecLineItem('max_current', 'Max Current', ShowAsEnum.engineering, float, False)))


eedata_inductor_display_order = eedata_generic_items_preitems+['inductance', 'tolerance', 'max_current']+eedata_generic_items_postitems


@dataclasses.dataclass
class Inductor(_GenericPartClass):
    diode_type: str = field(default=None, metadata=asdict(SpecLineItem('diode_type', 'Diode Type', ShowAsEnum.normal, str, True)))
    max_current: str = field(default=None, metadata=asdict(SpecLineItem('max_current', 'Peak Current', ShowAsEnum.engineering, float, False)))
    average_current: str = field(default=None, metadata=asdict(SpecLineItem('average_current', 'Average Current', ShowAsEnum.engineering, float, False)))
    max_rv: str = field(default=None, metadata=asdict(SpecLineItem('max_rv', 'Max Reverse Voltage', ShowAsEnum.engineering, float, False)))


eedata_diode_display_order = eedata_generic_items_preitems+('diode_type', 'max_rv', 'average_current', 'max_current')+eedata_generic_items_postitems

@dataclasses.dataclass
class Inductor(_GenericPartClass):
    frequency: str = field(default=None, metadata=asdict(SpecLineItem('frequency', 'Frequency', ShowAsEnum.engineering, float, True, 'Hz')))
    load_c: str = field(default=None, metadata=asdict(SpecLineItem('load_c', 'Load Capacitance', ShowAsEnum.engineering, float, False, 'F')))
    esr: str = field(default=None, metadata=asdict(SpecLineItem('esr', 'ESR', ShowAsEnum.engineering, float, False, f'{UnicodeCharacters.Omega}')))
    stability_ppm: str = field(default=None, metadata=asdict(SpecLineItem('stability_ppm', 'Stability', ShowAsEnum.normal, float, False, 'ppm')))


eedata_crystal_display_order = eedata_generic_items_preitems+('frequency', 'load_c', 'esr', 'stability_ppm')+eedata_generic_items_postitems

# todo: add
# eedata_mosfet_params = eedata_generic_spec + [
#     {'db_name': 'mosfet_type', 'showcase_name': 'Type', 'shows_as': 'normal', 'input_type': 'str', 'required': True, },
#     {'db_name': 'vdss', 'showcase_name': 'Max Drain-Source Voltage', 'shows_as': 'engineering', 'input_type': 'float', 'required': False, },
#     {'db_name': 'vgss', 'showcase_name': 'Max Gate-Source Voltage', 'shows_as': 'engineering', 'input_type': 'float', 'required': False, },
#     {'db_name': 'vgs_th', 'showcase_name': 'Gate-Source Threshold Voltage', 'shows_as': 'engineering', 'input_type': 'float', 'required': False, },
#     {'db_name': 'i_d', 'showcase_name': 'Max Drain Current', 'shows_as': 'engineering', 'input_type': 'float', 'required': False, },
#     {'db_name': 'i_d_pulse', 'showcase_name': 'Max Drain Peak Current', 'shows_as': 'engineering', 'input_type': 'float', 'required': False, },
# ]
# eedata_mosfet_display_order = eedata_generic_items_preitems+['mosfet_type', 'vdss', 'vgss', 'vgs_th', 'i_d', 'i_d_pulse']+eedata_generic_items_postitems
#
# eedata_bjt_params = eedata_generic_spec + [
#     {'db_name': 'bjt_type', 'showcase_name': 'Type', 'shows_as': 'normal', 'input_type': 'str', 'required': True, },
#     {'db_name': 'vcbo', 'showcase_name': 'Max Collector-Base Voltage', 'shows_as': 'engineering', 'input_type': 'float', 'required': False, },
#     {'db_name': 'vceo', 'showcase_name': 'Max Collector-Emitter Voltage', 'shows_as': 'engineering', 'input_type': 'float', 'required': False, },
#     {'db_name': 'vebo', 'showcase_name': 'Max Emitter-Base Voltage', 'shows_as': 'engineering', 'input_type': 'float', 'required': False, },
#     {'db_name': 'i_c', 'showcase_name': 'Max Cont. Collector Current', 'shows_as': 'engineering', 'input_type': 'float', 'required': False, },
#     {'db_name': 'i_c_peak', 'showcase_name': 'Max Peak Collector Current', 'shows_as': 'engineering', 'input_type': 'float', 'required': False, },
# ]
# eedata_bjt_display_order = eedata_generic_items_preitems+['bjt_type', 'vcbo', 'vceo', 'vebo', 'i_c', 'i_c_peak']+eedata_generic_items_postitems
#
# eedata_connector_params = eedata_generic_spec + [
#     {'db_name': 'conn_type', 'showcase_name': 'Type', 'shows_as': 'normal', 'input_type': 'str', 'required': True, },
# ]
# eedata_connector_display_order = eedata_generic_items_preitems+['conn_type']+eedata_generic_items_postitems
#
# eedata_led_params = eedata_generic_spec + [
#     {'db_name': 'led_type', 'showcase_name': 'LED Type', 'shows_as': 'normal', 'input_type': 'str', 'required': True, },
#     {'db_name': 'vf', 'showcase_name': 'LED forward voltage', 'shows_as': 'engineering', 'input_type': 'float', 'required': False, },
#     {'db_name': 'max_i', 'showcase_name': 'Max Current', 'shows_as': 'engineering', 'input_type': 'float', 'required': False, },
# ]
# eedata_led_display_order = eedata_generic_items_preitems+['led_type', 'vf', 'max_i']+eedata_generic_items_postitems
#
# eedata_fuse_params = eedata_generic_spec + [
#     {'db_name': 'fuse_type', 'showcase_name': 'Fuse Type', 'shows_as': 'normal', 'input_type': 'str', 'required': True, },
#     {'db_name': 'max_v', 'showcase_name': 'Fuse Max Voltage', 'shows_as': 'engineering', 'input_type': 'float', 'required': False, },
#     {'db_name': 'max_i', 'showcase_name': 'Max Current', 'shows_as': 'engineering', 'input_type': 'float', 'required': False, },
#     {'db_name': 'trip_i', 'showcase_name': 'Trip Current', 'shows_as': 'engineering', 'input_type': 'float', 'required': False, },
#     {'db_name': 'hold_i', 'showcase_name': 'Hold Current', 'shows_as': 'engineering', 'input_type': 'float', 'required': False, },
# ]
# eedata_fuse_display_order = eedata_generic_items_preitems+['fuse_type', 'max_v', 'trip_i', 'hold_i', 'max_i']+eedata_generic_items_postitems
#
# eedata_button_params = eedata_generic_spec + [
#     {'db_name': 'bt_type', 'showcase_name': 'Button Type', 'shows_as': 'normal', 'input_type': 'str', 'required': True},
#     {'db_name': 'circuit_t', 'showcase_name': 'Button Circuit', 'shows_as': 'normal', 'input_type': 'str', 'required': False},
#     {'db_name': 'max_v', 'showcase_name': 'Voltage Rating', 'shows_as': 'engineering', 'input_type': 'float', 'required': False, },
#     {'db_name': 'max_i', 'showcase_name': 'Current Rating', 'shows_as': 'engineering', 'input_type': 'float', 'required': False, },
# ]
# eedata_button_display_order = eedata_generic_items_preitems+['bt_type', 'circuit_t', 'max_v', 'max_i']+eedata_generic_items_postitems
#
# eedata_misc_spec = eedata_generic_spec
# eedata_misc_display_order = eedata_generic_items_preitems+eedata_generic_items_postitems
#
# eedata_pcb_params = [
#     {'db_name': 'stock', 'showcase_name': 'Stock', 'shows_as': 'normal', 'input_type': 'int', 'required': True, },
#     {'db_name': 'rev', 'showcase_name': 'Revision', 'shows_as': 'normal', 'input_type': 'str', 'required': True, },
#     {'db_name': 'comments', 'showcase_name': 'Comments', 'shows_as': 'normal', 'input_type': 'str', 'required': False, },
#     {'db_name': 'storage', 'showcase_name': 'Storage Location', 'shows_as': 'normal', 'input_type': 'str', 'required': False, },
#     {'db_name': 'board_name', 'showcase_name': 'Board Name', 'shows_as': 'normal', 'input_type': 'str', 'required': True},
# ]
# eedata_pcb_display_order = ['stock', 'board_name', 'rev', 'parts', 'storage', 'comments']



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
