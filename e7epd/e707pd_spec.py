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
    fraction = enum.auto()          # Show as a fraction
    custom = enum.auto()            # For cases where the printing is specially handled

class UnicodeCharacters(enum.Enum):
    Omega = '\u03A9'
    mu = '\u03BC'


@dataclasses.dataclass
class SpecLineItem:
    showcase_name: str      # How to showcase this line item to the user
    shows_as: ShowAsEnum    # How to display it to user
    input_type: type        # What Python type to use
    required: bool          # Is this item required?
    units: str = ""         # What to append to this (units) when displayed
    # The key for a part spec will be the db_name, thus it is not needed
    # db_name: str            # how this gets stored in the database


@dataclasses.dataclass
class UserSpec:
    """
    A dataclass stating how a user should be stored in the database
    """
    name: str
    email: str = ""
    phone: str = ""


@dataclasses.dataclass
class PartSpec:
    """
    How each part specification should be organized as
    """
    db_type_name: typing.Union[str, None]
    showcase_name: str
    table_display_order: tuple
    items: typing.Dict[str, SpecLineItem]


"""
The spec for any component. NOTE: this MUST match the parts table's keys
"""
BasePartItems = {
    'stock': SpecLineItem('Stock', ShowAsEnum.normal, int, True),
    'ipn': SpecLineItem('IPN', ShowAsEnum.normal, str, True),
    'mfg_part_numb': SpecLineItem('Mfg Part #', ShowAsEnum.normal, str, False),
    'manufacturer': SpecLineItem('Manufacturer', ShowAsEnum.normal, str, False),
    'package': SpecLineItem('Package', ShowAsEnum.normal, str, True),
    'storage': SpecLineItem('Storage Location', ShowAsEnum.normal, str, False),
    'comments': SpecLineItem('Comments', ShowAsEnum.normal, str, False),
    'datasheet': SpecLineItem('Datasheet', ShowAsEnum.normal, str, False),
    'user': SpecLineItem('User', ShowAsEnum.normal, str, False),
}


eedata_generic_items_preitems = ('stock', 'ipn', 'mfg_part_numb', 'manufacturer')
eedata_generic_items_postitems = ('package', 'storage', 'comments', 'datasheet', 'user')


Resistor = PartSpec(
    db_type_name='resistor',
    showcase_name='Resistor',
    table_display_order=eedata_generic_items_preitems+('resistance', 'tolerance', 'power')+eedata_generic_items_postitems,
    items={
        **BasePartItems,
        'resistance': SpecLineItem('Resistance', ShowAsEnum.engineering, float, True, f'{UnicodeCharacters.Omega:s}'),
        'tolerance': SpecLineItem('Tolerance', ShowAsEnum.precentage, float, False),
        'power': SpecLineItem('Power Rating', ShowAsEnum.fraction, float, False),
    }
)

Capacitor = PartSpec(
    db_type_name='capacitor',
    showcase_name='Capacitor',
    table_display_order=eedata_generic_items_preitems+('capacitance', 'tolerance', 'max_voltage', 'cap_type', 'temp_coeff')+eedata_generic_items_postitems,
    items={
        **BasePartItems,
        'capacitance': SpecLineItem('Capacitance', ShowAsEnum.engineering, float, True, f'F'),
        'tolerance': SpecLineItem('Tolerance', ShowAsEnum.precentage, float, False),
        'max_voltage': SpecLineItem('Voltage Rating', ShowAsEnum.normal, float, False, 'V'),
        'temp_coeff': SpecLineItem('Temp Coeff', ShowAsEnum.normal, str, False),
        'cap_type': SpecLineItem('Cap Type', ShowAsEnum.normal, str, False),
    }
)

IC = PartSpec(
    db_type_name='ic',
    showcase_name='IC',
    table_display_order=eedata_generic_items_preitems+('ic_type', )+eedata_generic_items_postitems,
    items={
        **BasePartItems,
        'ic_type': SpecLineItem('Type', ShowAsEnum.normal, str, True),
    }
)

Inductor = PartSpec(
    db_type_name='inductor',
    showcase_name='Inductor',
    table_display_order=eedata_generic_items_preitems+('inductance', 'tolerance', 'max_current')+eedata_generic_items_postitems,
    items={
        **BasePartItems,
        'inductance': SpecLineItem('Inductance', ShowAsEnum.engineering, float, True, f'H'),
        'tolerance': SpecLineItem('Tolerance', ShowAsEnum.precentage, float, False),
        'max_current': SpecLineItem('Current Rating', ShowAsEnum.engineering, float, False, 'A'),
    }
)

Diode = PartSpec(
    db_type_name='diode',
    showcase_name='Diode',
    table_display_order=eedata_generic_items_preitems+('diode_type', 'max_current', 'average_current', 'max_rv')+eedata_generic_items_postitems,
    items={
        **BasePartItems,
        'diode_type': SpecLineItem('Type', ShowAsEnum.normal, str, True),
        'max_current': SpecLineItem('Peak Current', ShowAsEnum.engineering, float, False, 'A'),
        'average_current': SpecLineItem('Average Current', ShowAsEnum.engineering, float, False, 'A'),
        'max_rv': SpecLineItem('Max Vrf', ShowAsEnum.engineering, float, False, 'V'),
    }
)

Crystal = PartSpec(
    db_type_name='crystal',
    showcase_name='Crystal',
    table_display_order=eedata_generic_items_preitems+('frequency', 'load_c', 'esr', 'stability')+eedata_generic_items_postitems,
    items={
        **BasePartItems,
        'frequency': SpecLineItem('Frequency', ShowAsEnum.engineering, float, True, 'Hz'),
        'load_c': SpecLineItem('Load Capacitance', ShowAsEnum.engineering, float, False, 'F'),
        'esr': SpecLineItem('ESR', ShowAsEnum.engineering, float, False, f'{UnicodeCharacters.Omega:s}'),
        'stability': SpecLineItem('Stability', ShowAsEnum.engineering, float, False, 'ppm'),
    }
)

FET = PartSpec(
    db_type_name='fet',
    showcase_name='FET',
    table_display_order=eedata_generic_items_preitems+('fet_type', 'vds', 'vgs', 'vgs_th', 'i_d', 'i_d_pulse')+eedata_generic_items_postitems,
    items={
        **BasePartItems,
        'fet_type': SpecLineItem('FET Type', ShowAsEnum.normal, str, True),
        'vds': SpecLineItem('Max Vds', ShowAsEnum.engineering, float, False, 'V'),
        'vgs': SpecLineItem('Max Vgs', ShowAsEnum.engineering, float, False, 'V'),
        'vgs_th': SpecLineItem('Vgs Threshold', ShowAsEnum.engineering, float, False, 'V'),
        'i_d': SpecLineItem('Drain Current', ShowAsEnum.engineering, float, False, 'A'),
        'i_d_pulse': SpecLineItem('Peak Drain Current', ShowAsEnum.engineering, float, False, 'A'),
    }
)

BJT = PartSpec(
    db_type_name='bjt',
    showcase_name='BJT',
    table_display_order=eedata_generic_items_preitems+('bjt_type', 'vcb', 'vce', 'veb', 'i_c', 'i_c_peak')+eedata_generic_items_postitems,
    items={
        **BasePartItems,
        'bjt_type': SpecLineItem('BJT Type', ShowAsEnum.normal, str, True),
        'vcb': SpecLineItem('Max Collector-Base Voltage', ShowAsEnum.engineering, float, False, 'V'),
        'vce': SpecLineItem('Max Collector-Emitter Voltage', ShowAsEnum.engineering, float, False, 'V'),
        'veb': SpecLineItem('Max Emitter-Base Voltage', ShowAsEnum.engineering, float, False, 'V'),
        'i_c': SpecLineItem('Collector Current', ShowAsEnum.engineering, float, False, 'A'),
        'i_c_peak': SpecLineItem('Peak Collector Current', ShowAsEnum.engineering, float, False, 'A'),
    }
)

Connector = PartSpec(
    db_type_name='conn',
    showcase_name='Connector',
    table_display_order=eedata_generic_items_preitems+('conn_type', )+eedata_generic_items_postitems,
    items={
        **BasePartItems,
        'conn_type': SpecLineItem('Type', ShowAsEnum.normal, str, True),
    }
)


LED = PartSpec(
    db_type_name='led',
    showcase_name='LED',
    table_display_order=eedata_generic_items_preitems+('led_type', 'color', 'vf', 'max_i')+eedata_generic_items_postitems,
    items={
        **BasePartItems,
        'led_type': SpecLineItem('Type', ShowAsEnum.normal, str, True),
        'color': SpecLineItem('Color', ShowAsEnum.normal, str, False),
        'vf': SpecLineItem('Forward Voltage', ShowAsEnum.engineering, float, False, 'V'),
        'max_i': SpecLineItem('Max Current', ShowAsEnum.engineering, float, False, 'A'),
    }
)

Fuse = PartSpec(
    db_type_name='fuse',
    showcase_name='Fuse',
    table_display_order=eedata_generic_items_preitems+('fuse_type', 'max_v', 'trip_i', 'hold_i', 'max_i')+eedata_generic_items_postitems,
    items={
        **BasePartItems,
        'fuse_type': SpecLineItem('Type', ShowAsEnum.normal, str, True),
        'max_v': SpecLineItem('Max Voltage', ShowAsEnum.engineering, float, False, 'V'),
        'max_i': SpecLineItem('Max Current', ShowAsEnum.engineering, float, False, 'A'),
        'trip_i': SpecLineItem('Trip Current', ShowAsEnum.engineering, float, False, 'A'),
        'hold_i': SpecLineItem('Hold Current', ShowAsEnum.engineering, float, False, 'A'),
    }
)

Buttons = PartSpec(
    db_type_name='sw_bw',
    showcase_name='Switch/Buttons',
    table_display_order=eedata_generic_items_preitems+('bt_type', 'circuit_t', 'max_v', 'max_i')+eedata_generic_items_postitems,
    items={
        **BasePartItems,
        'bt_type': SpecLineItem('Type', ShowAsEnum.normal, str, True),
        'circuit_t': SpecLineItem('Button Circuit', ShowAsEnum.normal, str, False),
        'max_v': SpecLineItem('Max Voltage', ShowAsEnum.engineering, float, False, 'V'),
        'max_i': SpecLineItem('Max Current', ShowAsEnum.engineering, float, False, 'A'),
    }
)

Others = PartSpec(
    db_type_name=None,        # Misc parts's type will be empty
    showcase_name='Other',
    table_display_order=eedata_generic_items_preitems+eedata_generic_items_postitems,
    items={
        **BasePartItems,
    }
)

PCBItems = {
    'stock': SpecLineItem('Stock', ShowAsEnum.normal, int, True),
    'id': SpecLineItem('Board ID', ShowAsEnum.normal, str, True),
    'board name': SpecLineItem('Board Name', ShowAsEnum.normal, str, False),
    'rev': SpecLineItem('Rev', ShowAsEnum.normal, str, True),
    'storage': SpecLineItem('Storage Location', ShowAsEnum.normal, str, False),
    'comments': SpecLineItem('Comments', ShowAsEnum.normal, str, False),
    'user': SpecLineItem('User', ShowAsEnum.normal, str, False),
    'parts': SpecLineItem('Parts', ShowAsEnum.custom, list, True)
}
PCBPartsItems = {
    'type': SpecLineItem('Type', ShowAsEnum.normal, str, True),
    'part': SpecLineItem('Part', ShowAsEnum.normal, str, True),
    'qty': SpecLineItem('Type', ShowAsEnum.normal, int, True),
    'designator': SpecLineItem('Designator', ShowAsEnum.normal, str, True),
    'alternatives': SpecLineItem('Alternative', ShowAsEnum.normal, int, False),
}

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
    from e7epd import E7EPD
    all_comp_type = E7EPD.comp_types
    for c in all_comp_type:
        for t in c.table_display_order:
            if t not in c.items:
                raise AssertionError(f"Spec '{t}' not in {c.showcase_name}")
    print("Done with test")
