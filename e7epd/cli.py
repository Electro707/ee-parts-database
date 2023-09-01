#!/usr/bin/python3
"""
    E707PD Python CLI Application
    Rev 0.5
"""
import dataclasses
# External Modules Import
import subprocess
import logging
import importlib
import rich
import rich.console
import rich.panel
from rich.prompt import Prompt
from rich.logging import RichHandler
import rich.table
import decimal
from engineering_notation import EngNumber
import questionary
import prompt_toolkit
import prompt_toolkit.formatted_text
import os
import sys
import typing
import json
import pymongo
import pymongo.errors
import pkg_resources
import re
import warnings
import argparse
# Local Modules Import
import e7epd
from e7epd.e707pd_spec import ShowAsEnum
# Import of my fork of the digikey_api package
try:
    from e707_digikey.v3.api import DigikeyAPI
except ImportError:
    digikey_api_en = False
else:
    digikey_api_en = True


console = rich.console.Console(style="blue")


def CLIConfig_config_db_list_checker(func):
    def wrap(self, *args, **kwargs):
        if len(self.config.db_list) == 0:
            raise self.NoDatabaseException()
        return func(self, *args, **kwargs)
    return wrap


class CLIConfig:
    @dataclasses.dataclass
    class _Config:
        last_db: str = ""
        db_list: dict = dataclasses.field(default_factory=dict)

        # https://stackoverflow.com/questions/61426232/update-dataclass-fields-from-a-dict-in-python
        def from_dict(self, d: dict):
            for key, value in d.items():
                if hasattr(self, key):
                    setattr(self, key, value)
                else:
                    raise UserWarning(f"This dataclass does have have attribute {key}")

    class NoDatabaseException(Exception):
        def __init__(self):
            super().__init__("No Database")

    class NoLastDBSelectionException(Exception):
        def __init__(self):
            super().__init__("There isn't a last selected database")

    class DatabaseConnectionException(Exception):
        def __init__(self):
            super().__init__("Error connection with database")

    def __init__(self):
        self.log = logging.getLogger('CLIConfig')
        if not pkg_resources.resource_isdir(__name__, 'data'):
            os.mkdir(pkg_resources.resource_filename(__name__, "data"))
        self.file_path = pkg_resources.resource_filename(__name__, "data/cli_config.json")
        self.config = self._Config()
        if os.path.isfile(self.file_path):
            with open(self.file_path) as f:
                self.config.from_dict(json.load(f))

    def save(self):
        with open(self.file_path, 'w') as f:
            json.dump(dataclasses.asdict(self.config), f, indent=4)

    @CLIConfig_config_db_list_checker
    def get_database_connection(self, database_name: str = None) -> pymongo.MongoClient:
        # todo: add JSON file compatibility
        if database_name is None:
            database_name = self.config.last_db
            if database_name is None:
                raise self.NoLastDBSelectionException()
        if database_name not in self.config.db_list:
            raise self.NoLastDBSelectionException()

        db_conf = self.config.db_list[database_name]

        self.config.last_db = database_name

        if db_conf['type'] == 'local':
            raise UserWarning("Not supported, deprecated in 0.7.0")
        elif db_conf['type'] == 'mysql_server':
            raise UserWarning("Not supported, deprecated in 0.7.0")
        elif db_conf['type'] == 'postgress_server':
            raise UserWarning("Not supported, deprecated in 0.7.0")
        elif db_conf['type'] == 'mongodb':
            # todo: enable socket connection
            if db_conf['auth']:
                conn_str = f"mongodb://{db_conf['username']}:{db_conf['password']}@{db_conf['db_host']}:27017/"
            else:
                conn_str = f"mongodb://{db_conf['db_host']}:27017/"
            conn = pymongo.MongoClient(conn_str, serverSelectionTimeoutMS=1000*2)
            try:
                # The ping command is cheap and does not require auth.
                conn.admin.command('ping')
            except pymongo.errors.ConnectionFailure:
                self.log.exception("ConnectionFailure going to database")
                raise self.DatabaseConnectionException()
            return conn

    @CLIConfig_config_db_list_checker
    def get_database_connection_info(self, database_name: str = None) -> dict:
        return self.config.db_list[database_name]

    @CLIConfig_config_db_list_checker
    def get_stored_db_names(self) -> list:
        return list(self.config.db_list.keys())

    def get_selected_database(self) -> str:
        return self.config.last_db

    def set_last_db(self, database_name: str):
        self.config.last_db = database_name

    def save_database_as_sqlite(self, database_name: str, file_name: str):
        raise DeprecationWarning("Removed in 0.7.0")

    def save_database_as_mysql(self, database_name: str, username: str, password: str, db_name: str, host: str):
        raise DeprecationWarning("Removed in 0.7.0")

    def save_database_as_postgress(self, database_name: str, username: str, password: str, db_name: str, host: str):
        raise DeprecationWarning("Removed in 0.7.0")

    def save_database_as_mongo(self, database_name: str, username: str, password: str, host: str, authenticated: bool = False):
        self._save_database_as_hostsb(database_name, username, password, host)
        self.config.db_list[database_name]['type'] = 'mongodb'
        self.config.db_list[database_name]['auth'] = authenticated
        self.save()

    def _save_database_as_hostsb(self, database_name: str, username: str, password: str, host: str):
        if database_name not in self.config.db_list:
            self.config.db_list[database_name] = {}
        self.config.db_list[database_name]['username'] = username
        self.config.db_list[database_name]['password'] = password
        self.config.db_list[database_name]['db_host'] = host


class DigikeyHandler:
    class _NoDigikeyApiError(Exception):
        pass

    def __init__(self, config_handler: e7epd.E7EPDConfigTable):
        super().__init__()
        self.log = logging.getLogger('DigikeyAPIConfig')
        self.config = config_handler

        self.is_digikey_available = digikey_api_en

        if self.is_digikey_available:
            self.digikey_api = DigikeyAPI(self.config)

    def check_for_dk_api(self):
        if not self.is_digikey_available:
            console.print("[orange]API is not setup[/]")
            console.print("[orange]Please install it with 'pip install git+https://github.com/Electro707/digikey-api.git@8549f42a1853c9d371c3fb1b0b8d780d405174d8'[/]")
            raise self._NoDigikeyApiError

    def check_for_db_config(self):
        if self.digikey_api.needs_client_id() or self.digikey_api.needs_client_secret():
            raise self._NoDigikeyApiError

    def scan_digikey_barcode(self, bc_code: str = None):
        """
        Function that asks the user for a Digikey barcode scan, and finds the manufacturer part number as
        well as the part's Digikey info if requested

        TODO: The digikey info return should be parsed by this function to get useful values
        Args:
            bc_code (str): The scanned digikey barcode. In given, this function will not ask for it

        Returns:

        """
        try:
            self.check_for_dk_api()
        except self._NoDigikeyApiError:
            console.print("[red]No Digikey API is available[/]")
            raise KeyboardInterrupt()
        try:
            self.check_for_db_config()
        except self._NoDigikeyApiError:
            console.print("[red]Client Secret/Client ID are not setup. Do so from the main menu[/]")
            raise KeyboardInterrupt()

        if bc_code is None:
            bc_code = questionary.text("Enter the Digikey barcode: ").ask()
        if bc_code == '' or bc_code is None:
            console.print("[red]No barcode entered[/]")
            raise KeyboardInterrupt()
        bc_code = bc_code.strip()
        bc_code = bc_code.replace('{RS}', u"\u001E")
        bc_code = bc_code.replace('{GS}', u"\u001D")
        try:
            b = self.digikey_api.barcode_2d(bc_code)
        except:  # TODO: Add specific exception
            console.print("[red]Digikey Barcode API error[/]")
            raise KeyboardInterrupt()
        return b.manufacturer_part_number, b

    def digikey_api_config_setup(self):
        c_id = questionary.text("Enter the Digikey API client ID for the API: ").ask()
        if c_id == '' or c_id is None:
            console.print("[red]You need a client ID to use the digikey API[/]")
            return
        c_sec = questionary.password("Enter the Digikey API client secret for the API: ").ask()
        if c_sec == '' or c_sec is None:
            console.print("[red]You need a client ID to use the digikey API[/]")
            return
        self.digikey_api.set_client_info(client_id=c_id, client_secret=c_sec)


class CLI:
    cli_revision = e7epd.__version__

    class _HelperFunctionExitError(Exception):
        def __init__(self, data=None):
            self.extra_data = data
            super().__init__()

    class _ChooseComponentDigikeyBarcode(Exception):
        def __init__(self, mfg_part_number: str, dk_info: dict):
            self.mfg_part_number = mfg_part_number
            self.dk_info = dk_info
            super().__init__()

    def __init__(self, config: CLIConfig, database_connection: pymongo.MongoClient):
        self.db = e7epd.E7EPD(database_connection)
        self.conf = config
        self.dk = DigikeyHandler(self.db.config)

        self.return_formatted_choice = questionary.Choice(title=prompt_toolkit.formatted_text.FormattedText([('green', 'Return')]))
        self.formatted_digikey_scan_choice = questionary.Choice(title=prompt_toolkit.formatted_text.FormattedText([('blue', 'Scan Digikey 2D Barcode')]), value='dk_scan')

    @staticmethod
    def find_spec_by_db_name(spec_list: typing.Dict[str, e7epd.spec.SpecLineItem], db_name: str) -> e7epd.spec.SpecLineItem:
        """
            Helper function that returns a database specification by the db_name attribute
            :param spec_list: The specification list
            :param db_name: The database name
            :return: The specification that has db_name equal to the argument
        """
        warnings.warn("This function is not needed as spec_list is a dict where the key is what's stored in the database", DeprecationWarning)
        return spec_list[db_name]

    def _ask_ipn(self, existing_ipn_list: list = None, must_already_exist: bool = None) -> str:
        """
        Asks for the manufacturer part number. This function handles type hinting with a given list, checking if the mfgr
        is a Digikey barcode scan, and raises an error if the entered part number is already in the database or not.

        Args:
            existing_ipn_list: A list of current manufacturer part numbers to typehint
            must_already_exist: If a given part number must exist in the `existing_mfr_list` or must not exist

        Returns: The entered manufacturer part number
        """
        # Replace default argument
        if existing_ipn_list is None:
            existing_ipn_list = []
        if len(existing_ipn_list) != 0:
            ipn_entered = questionary.autocomplete("Enter the IPN (or scan a Digikey barcode): ", choices=existing_ipn_list).ask()
        else:
            ipn_entered = questionary.text("Enter the IPN (or scan a Digikey barcode): ").ask()
        if ipn_entered == '' or ipn_entered is None:
            console.print("[red]Must have an IPN[/]")
            raise self._HelperFunctionExitError()

        ipn_entered = ipn_entered.strip()
        ipn_entered = ipn_entered.upper()

        if ipn_entered.startswith('[)>'):
            try:
                # todo: fix this, as it currently won't work this way
                mfr_part_numb, p = self.dk.scan_digikey_barcode(ipn_entered)
            except KeyboardInterrupt:
                raise self._HelperFunctionExitError()

        if must_already_exist is True:
            if ipn_entered not in existing_ipn_list:
                console.print("[red]Part must already exist in the database[/]")
                raise self._HelperFunctionExitError(ipn_entered)
        elif must_already_exist is False:
            if ipn_entered in existing_ipn_list:
                console.print("[red]Part must not already exist in the database, which it does![/]")
                raise self._HelperFunctionExitError(ipn_entered)
        return ipn_entered

    def _ask_mfg_part_number(self, current_ipn: str = None):
        prompt = "Enter the manufacturer part number: "
        if current_ipn:
            prompt = "Enter the MGF part number or just Enter to copy the IPN: "
        mfr_part_numb = questionary.text(prompt).ask()
        if mfr_part_numb == '':
            if current_ipn is None:
                console.print("[red]Must have a manufacturer part number[/]")
                raise self._HelperFunctionExitError()
            else:
                console.print("Selecting current IPN as MGF part number")
                return current_ipn

        mfr_part_numb = mfr_part_numb.strip()
        mfr_part_numb = mfr_part_numb.upper()

        return mfr_part_numb

    def _ask_for_pcb_parts(self) -> list:
        """
        Called when wanting to input parts for a PCB
        """
        all_parts_dict = []
        while 1:
            new_part = {'part': {}}
            # Ask for the part itself, what it is and get the type
            specific_part = questionary.select("Is this a specific or generic part?",  choices=["Specific", "Generic", "Done"]).ask()
            if specific_part is None:
                raise self._HelperFunctionExitError()
            elif specific_part == "Done":
                console.print("Done adding parts")
                break
            elif specific_part == "Specific":
                mgf = self._ask_ipn(self.db.get_all_mfr_part_numb_in_db(), True)
                _, part_db = self.db.check_if_already_in_db_by_manuf(mgf)
                new_part['part']['mfr_part_numb'] = mgf
                new_part['comp_type'] = part_db.table_name
            elif specific_part == "Generic":
                generic_part_db = self.choose_component()
                new_part['comp_type'] = generic_part_db.table_name
                for spec_db_name in generic_part_db.table_item_display_order:
                    if spec_db_name in ['stock', 'mfr_part_numb', 'manufacturer', 'storage', 'comments', 'datasheet']:
                        continue
                    # Select an autocomplete choice, or None if there isn't any
                    autocomplete_choices = self.get_autocomplete_list(spec_db_name, generic_part_db.table_name)
                    # Get the spec
                    spec = self.find_spec_by_db_name(generic_part_db.table_item_spec, spec_db_name)
                    if spec is None:
                        console.print(
                            "[red]INTERNAL ERROR: Got None when finding the spec for database name %s[/]" % spec_db_name)
                        raise self._HelperFunctionExitError()
                    # Ask the user for that property
                    try:
                        val, op = self.ask_for_spec_input_with_operator(generic_part_db, spec, autocomplete_choices)
                        new_part['part'][spec_db_name] = {'val': val, 'op': op}
                    except KeyboardInterrupt:
                        console.print("Did not add part")
                        raise self._HelperFunctionExitError()
            else:
                console.print("[red]Invalid Choice![/]")
                continue
            # Ask for quantity
            try:
                new_part['quantity'] = int(questionary.text("Enter quantity of this part used on this PCB:").ask())
            except ValueError:
                console.print("[red]Invalid quantity[/]")
                continue
            new_part['quantity'] = questionary.text("Enter the designator/reference:").ask()
            all_parts_dict.append(new_part)

        if len(all_parts_dict) == 0:
            console.print("Added nothing for parts")
            raise self._HelperFunctionExitError()
        return all_parts_dict

    def print_parts_list(self, part_type: e7epd.spec.PartSpec, parts_list: list[dict], title):
        """ Function is called when the user wants to print out all parts """
        ta = rich.table.Table(title=title)
        for spec_db_name in part_type.table_display_order:
            ta.add_column(part_type.items[spec_db_name].showcase_name)
        for part in parts_list:
            row = []
            for spec_db_name in part_type.table_display_order:
                to_display = part[spec_db_name]
                display_as = part_type.items[spec_db_name].shows_as
                if to_display is not None:
                    if display_as == ShowAsEnum.engineering:
                        to_display = str(EngNumber(to_display))
                    elif display_as == ShowAsEnum.precentage:
                        to_display = str(to_display) + "%"
                    else:
                        to_display = str(to_display)
                row.append(to_display)
            ta.add_row(*row)
        console.print(ta)

    def print_all_parts(self, part_type: e7epd.spec.PartSpec):
        parts_list = self.db.get_all_parts(part_type)
        self.print_parts_list(part_type, parts_list, title="All parts in %s" % part_type.showcase_name)

    def print_filtered_parts(self, part_type: e7epd.spec.PartSpec):
        """
        Prints all parts in a component database with filtering
        Args:
            part_db: The component database to use
        """
        choices = [questionary.Choice(title=part_type.items[d].showcase_name, value=d) for d in part_type.items]
        specs_selected = questionary.checkbox("Select what parameters do you want to search by: ", choices=choices).ask()       # type: typing.List[str]
        if specs_selected is None:
            return
        if len(specs_selected) == 0:
            console.print("[red]Must choose something[/]")
            return
        search_filter = []
        for s in specs_selected:
            autocomplete_choices = self.get_autocomplete_list(s, part_type.db_type_name)
            try:
                inp, op = self.ask_for_spec_input_with_operator(part_type, s, autocomplete_choices)
            except KeyboardInterrupt:
                console.print("Canceled part lookup")
                return
            search_filter.append({'db_name': s, 'val': inp, 'op': op})
        try:
            parts_list = part_db.get_sorted_parts(search_filter)
        except e7epd.EmptyInDatabase:
            console.print("[red]No filtered parts in the database[/]")
            return
        self.print_parts_list(part_db, parts_list, title="All parts in %s" % part_db.table_name)

    def print_parts(self, part_type: e7epd.spec.PartSpec = None):
        if part_type is None:
            part_type = self.choose_component()
        if self.db.get_number_of_parts_in_db(part_type) == 0:
            console.print("[italic red]Sorry, but there are no parts for that component[/]")
            return
        all_parts = questionary.confirm("Do you want to filter the parts beforehand?", default=False, auto_enter=True).ask()
        if all_parts:
            self.print_filtered_parts(part_type)
        else:
            self.print_all_parts(part_type)

    def ask_for_spec_input_with_operator(self, part_type: e7epd.spec.PartSpec, spec_name: str, choices: list = None, operator_allowed: bool = True):
        """
        Function that prompts the user to enter the specification (resistance, package, etc) for a part.
        This function allows nicely type inputs like 10k

        Args:
            part_db: The part database to get the manufacturer part number
                       TODO: Remove this and replace with a list option for choices
            spec: The specification that we want the user to enter
            choices: A list of choices to show allow the user to select from
            operator_allowed: Whether to allow the user to enter an operator (like >1k)

        Returns: A tuple of
                    - The input given as the spec type (so for resistance it will return as a float)
                    - The operator to compare with the input if allowed, like == or >
        """
        # todo: this
        # if spec['input_type'] == 'parts_json':  # We are handling adding a part, which is seperate from a value
        #     try:
        #         inp = self._ask_for_pcb_parts()
        #     except self._HelperFunctionExitError:
        #         raise KeyboardInterrupt()
        #     return inp
        op = '=='
        spec = part_type.items[spec_name]
        while 1:
            # todo: do we need the following case handling below??
            if spec_name == 'ipn':
                try:
                    inp = self._ask_ipn(self.db.get_all_parts_one_keys(part_type, 'ipn'))
                except self._HelperFunctionExitError:
                    raise KeyboardInterrupt()
            else:
                if choices:
                    inp = questionary.autocomplete("Enter value for %s: " % spec.showcase_name, choices=choices).ask()
                else:
                    inp = questionary.text("Enter value for %s: " % spec.showcase_name).ask()
            if inp is None:
                raise KeyboardInterrupt()
            if inp == '':
                if spec.required is True:
                    console.print("You must enter this spec as it's required")
                    continue
                else:
                    inp = None

            if inp is not None:
                # Remove leading and trailing whitespace
                inp = inp.strip()
                if operator_allowed:
                    if inp.startswith(tuple(['<', '<=', '>', '>='])):
                        op = re.findall(r'\>=|\>|\<=|\<', inp)[0]
                        inp = re.sub(r'\>=|\>|\<=|\<', "", inp)
                if spec.shows_as == ShowAsEnum.engineering:
                    try:
                        inp = EngNumber(inp)
                    except decimal.InvalidOperation:
                        console.print("Invalid engineering number")
                        continue
                elif spec.shows_as == ShowAsEnum.precentage:
                    if '%' in inp:
                        inp = inp.replace('%', '')
                    else:
                        console.print("Inputted value is not a percentage")
                        continue
                elif '/' in inp and spec.input_type is float:
                    inp = inp.split('/')
                    try:
                        inp = float(inp[0]) / float(inp[1])
                    except ValueError:
                        console.print("Inputted value is not a proper fraction")
                        continue

                try:
                    if spec.input_type is int:
                        inp = int(inp)
                    elif spec.input_type is float:
                        inp = float(inp)
                except ValueError:
                    console.print("Inputted value is not a %s" % spec.input_type)
                    continue
            break
        return inp, op

    def ask_for_spec_input(self, part_type: e7epd.spec.PartSpec, spec_name: str, choices: list = None):
        inp, op = self.ask_for_spec_input_with_operator(part_type, spec_name, choices, operator_allowed=False)
        return inp

    @staticmethod
    def get_autocomplete_list(db_name: str, table_name: str) -> typing.Union[None, list]:
        # todo: improve this for table name to point to type directly
        autocomplete_choices = None
        if db_name == 'manufacturer' and table_name == 'ic':
            autocomplete_choices = e7epd.spec.autofill_helpers_list['ic_manufacturers']
        if db_name == 'manufacturer' and table_name == 'resistor':
            autocomplete_choices = e7epd.spec.autofill_helpers_list['passive_manufacturers']
        elif db_name == 'ic_type' and table_name == 'ic':
            autocomplete_choices = e7epd.spec.autofill_helpers_list['ic_types']
        elif db_name == 'cap_type' and table_name == 'capacitor':
            autocomplete_choices = e7epd.spec.autofill_helpers_list['capacitor_types']
        elif db_name == 'diode_type' and table_name == 'diode':
            autocomplete_choices = e7epd.spec.autofill_helpers_list['diode_type']
        elif db_name == 'bjt_type' and table_name == 'bjt':
            autocomplete_choices = e7epd.spec.autofill_helpers_list['bjt_types']
        elif db_name == 'mosfet_type' and table_name == 'mosfet':
            autocomplete_choices = e7epd.spec.autofill_helpers_list['mosfet_types']
        elif db_name == 'led_type' and table_name == 'led':
            autocomplete_choices = e7epd.spec.autofill_helpers_list['led_types']
        elif db_name == 'fuse_type' and table_name == 'fuse':
            autocomplete_choices = e7epd.spec.autofill_helpers_list['fuse_types']
        # Package Auto-Helpers
        elif db_name == 'package' and table_name == 'ic':
            autocomplete_choices = e7epd.spec.autofill_helpers_list['ic_packages']
        elif db_name == 'package' and (table_name == 'resistor' or table_name == 'capacitor' or table_name == 'inductor'):
            autocomplete_choices = e7epd.spec.autofill_helpers_list['passive_packages']
        return autocomplete_choices

    def get_partdb_and_ipn(self, part_db: e7epd.spec.PartSpec = None, ipn_must_exist: bool = None):
        """
        Helper function to get the manufacturer part number and component database
        Args:
            part_db: The selected component database. If not given, this function will return one depending on the
                     manufacturer part number
            ipn_must_exist: Whether the manufacturer part number must already exist in the database

        Returns: A tupple of a selected component database and the manufacturer part number
        """
        if part_db is None:
            all_ipn_list = self.db.get_all_parts_one_keys(None, 'ipn')
        else:
            all_ipn_list = self.db.get_all_parts_one_keys(part_db, 'ipn')

        try:
            ipn_number = self._ask_ipn(all_ipn_list, must_already_exist=ipn_must_exist)
        except self._HelperFunctionExitError:
            raise self._HelperFunctionExitError()

        if part_db is None:
            t = self.db.get_part_by_ipn(ipn_number)['type']
            part_db = self.db.get_part_spec_by_db_name(t)

        return part_db, ipn_number

    def add_new_part(self, part_type: e7epd.spec.PartSpec = None):
        """ Function gets called when a part is to be added """
        try:
            if part_type is None:
                try:
                    part_type = self.choose_component()
                except self._ChooseComponentDigikeyBarcode as e:
                    print(e.dk_info)
                    console.print("[red]Digikey component for adding a part isn't supported, yet[/]")
                    return
            try:
                ipn = self._ask_ipn(self.db.get_all_parts_one_keys(part_type, 'ipn'), must_already_exist=False)
            except self._HelperFunctionExitError as e:
                if e.extra_data is not None:
                    if questionary.confirm("Would you like to instead add the parts to your stock?", auto_enter=False, default=False).ask():
                        self.add_stock_to_part(part_type, e.extra_data)
                return
            new_part = {'ipn': ipn}
            for spec_db_name in part_type.table_display_order:
                # Skip over the ipn as we already have that
                if spec_db_name == 'ipn':
                    continue
                elif spec_db_name == 'mfg_part_numb':
                    try:
                        new_part['mfg_part_numb'] = self._ask_mfg_part_number(new_part['ipn'])
                    except self._HelperFunctionExitError:
                        raise KeyboardInterrupt()
                else:
                    # Select an autocomplete choice, or None if there isn't any
                    autocomplete_choices = self.get_autocomplete_list(spec_db_name, part_type.db_type_name)
                    try:        # Ask the user for that property
                        new_part[spec_db_name] = self.ask_for_spec_input(part_type, spec_db_name, autocomplete_choices)
                    except KeyboardInterrupt:
                        console.print("Did not add part")
                        return
            self.db.add_new_part(part_type, new_part)
        except KeyboardInterrupt:
            console.print("\nOk, no part is added")
            return

    def delete_part(self, part_db: e7epd.spec.PartSpec):
        """ This gets called when a part is to be deleted """
        try:
            part_db, ipn = self.get_partdb_and_ipn(part_db, True)
        except self._HelperFunctionExitError:
            return
        if questionary.confirm("ARE YOU SURE...AGAIN???", auto_enter=False, default=False).ask():
            try:
                self.db.delete_part(part_db, ipn)
            except e7epd.EmptyInDatabase:
                console.print("[red]The manufacturer is not in the database[/]")
            else:
                console.print(f"Deleted {ipn} from the database")
        else:
            console.print("Did not delete the part, it is safe.")

    def add_stock_to_part(self, part_db: e7epd.spec.PartSpec = None, ipn: str = None):
        try:
            if ipn is None or part_db is None:        # If we did not pass a pre-selected mfg part number and part db, ask for it
                try:
                    part_db, ipn = self.get_partdb_and_ipn(part_db, True)
                except self._HelperFunctionExitError:
                    return
            component = self.db.get_part_by_ipn(ipn)
            console.print('There are {:d} parts of the selected component'.format(component['stock']))
            while 1:
                add_by = questionary.text("Enter how much you want to add this part by: ").ask()
                if add_by is None:
                    raise KeyboardInterrupt()
                try:
                    add_by = int(add_by)
                except ValueError:
                    console.print("Must be an integer")
                    continue
                if add_by < 0:
                    console.print("Must be greater than 0")
                    continue
                break
            component['stock'] += add_by
            self.db.update_part_stock(ipn, component['stock'])
            console.print('[green]Add to your stock :). There is now {:d} left of it.[/]'.format(component['stock']))
        except KeyboardInterrupt:
            console.print("\nOk, no stock is changed")
            return

    def remove_stock_from_part(self, part_db: e7epd.spec.PartSpec = None):
        try:
            try:
                part_db, ipn = self.get_partdb_and_ipn(part_db, True)
            except self._HelperFunctionExitError:
                return
            component = self.db.get_part_by_ipn(ipn)
            console.print('There are {:d} parts of the selected component'.format(component['stock']))
            while 1:
                remove_by = questionary.text("Enter how many components to remove from this part?: ").ask()
                if remove_by is None:
                    raise KeyboardInterrupt()
                try:
                    remove_by = int(remove_by)
                except ValueError:
                    console.print("Must be an integer")
                    continue
                if remove_by < 0:
                    console.print("Must be greater than 0")
                    continue
                break
            if component['stock'] - remove_by < 0:
                console.print("[red]Stock will go to negative[/]")
                console.print("[red]If you want to make the stock zero, restart this operation and remove {:d} parts instead[/]".format(component['stock']))
                return
            component['stock'] -= remove_by
            self.db.update_part_stock(ipn, component['stock'])
            console.print('[green]Removed to your stock :). There is now {:d} left of it.[/]'.format(component['stock']))
        except KeyboardInterrupt:
            console.print("Ok, no stock is changed")
            return

    def edit_part(self, part_db: e7epd.spec.PartSpec = None):
        """
        Function to update the part's properties
        """
        to_update = {}  # A separate variable for only keys that need changing
        try:
            # Ask for manufacturer part number first, and make sure there are no conflicts
            try:
                part_db, ipn = self.get_partdb_and_ipn(part_db, True)
            except self._HelperFunctionExitError:
                return
            component = self.db.get_part_by_ipn(ipn)
            while 1:
                q = []
                for spec_db_name in part_db.table_display_order:
                    if spec_db_name == "ipn":
                        # todo: allow IPN to be changed. The update_part function *should* be able to handle it just fine?
                        continue
                    spec = part_db.items[spec_db_name]
                    if spec is None:
                        console.print("[red]INTERNAL ERROR: Got None when finding the spec for database name %s[/]" % spec_db_name)
                        return
                    q.append(questionary.Choice(title="{:}: {:}".format(spec.showcase_name, component[spec_db_name]), value=spec_db_name))
                q.append(questionary.Choice(title=prompt_toolkit.formatted_text.FormattedText([('green', 'Save and Exit')]), value='exit_save'))
                q.append(questionary.Choice(title=prompt_toolkit.formatted_text.FormattedText([('red', 'Exit without Saving')]), value='no_save'))
                to_change = questionary.select("Choose a field to edit:", q).ask()
                if to_change is None:
                    raise KeyboardInterrupt()
                if to_change == 'exit_save':
                    self.db.update_part(part_db, ipn, to_update)
                    break
                if to_change == 'no_save':
                    raise KeyboardInterrupt()
                try:
                    new_val = self.ask_for_spec_input(part_db, to_change, self.get_autocomplete_list(to_change, part_db.db_type_name))
                    to_update[to_change] = new_val
                    component[to_change] = new_val
                except KeyboardInterrupt:
                    console.print("Did not change spec")
                    continue
        except KeyboardInterrupt:
            console.print("Did not change part")
            return

    def print_pcb_and_component_availability(self):
        all_boards = self.db.pcbs.get_all_boardnames()
        if len(all_boards) == 0:
            console.print("There are no PCBs in the database")
            return
        board_name = questionary.autocomplete("Enter the PCB name: ", choices=all_boards).ask()
        if board_name is None:
            console.print("No board is given")
            return
        if board_name not in all_boards:
            console.print("A board not in the database was given")
            return
        rev = questionary.autocomplete("Enter the PCB revision: ", choices=self.db.pcbs.get_revision_per_boardname(board_name)).ask()

        try:
            board = self.db.pcbs.get_by_boardname_and_rev(board_name, rev)
        except sqlalchemy.exc.NoResultFound:
            console.print("[red]No board found for the given name and revision[/]")
            return

        all_parts_in_board = []
        for board_part in board.parts:
            part_db_name, part_db = self.db.get_component_by_table_name(board_part['comp_type'])
            part_description = ""
            if 'mfr_part_numb' in board_part['part']:
                part_description = board_part['part']['mfr_part_numb']
                try:
                    parts_in_db = [part_db.get_part_by_mfr_part_numb(board_part['part']['mfr_part_numb'])]
                except sqlalchemy.exc.NoResultFound:
                    parts_in_db = []
            else:
                search_query = []
                if board_part['comp_type'] == 'resistance':
                    part_description = self.db.resistors.print_formatted_from_spec(board_part['part'])
                for sc in board_part['part']:
                    if type(board_part['part'][sc]) is dict:
                        search_query.append({'db_name': sc, 'val': board_part['part'][sc]['val'], 'op': board_part['part'][sc]['op']})
                    else:
                        search_query.append({'db_name': sc, 'val': board_part['part'][sc]})
                parts_in_db = part_db.get_sorted_parts(search_query)
            if len(parts_in_db) == 0:
                all_parts_in_board.append(([str(board_part['quantity']), board_part['reference'], part_description, part_db_name, '-', '0', '-'], 's'))
            for p in parts_in_db:
                all_parts_in_board.append(([str(board_part['quantity']), board_part['reference'], part_description, part_db_name, p.mfr_part_numb, str(p.stock), p.storage], None))

        console.print("You currently have {:d} PCBs available".format(board.stock))

        ta = rich.table.Table(title='All components for {} Rev {}'.format(board_name, rev))
        ta.add_column("Stock Required")
        ta.add_column("Reference")
        ta.add_column("Description")
        ta.add_column("Component Type")
        ta.add_column("Available Mfr Part #")
        ta.add_column("Stock Available")
        ta.add_column("Component Location")
        for parts_in_db in all_parts_in_board:
            ta.add_row(*parts_in_db[0], style=parts_in_db[1])
        console.print(ta)

        return

    def component_cli(self, part_db: e7epd.spec.PartSpec):
        """ The CLI handler for components """
        while 1:
            to_do = questionary.select("What do you want to do in this component database? ", choices=["Print parts in DB", "Append Stock", "Remove Stock", "Add Part", "Delete Part", "Edit Part", self.return_formatted_choice]).ask()
            if to_do is None:
                raise KeyboardInterrupt()
            if to_do == "Return":
                break
            elif to_do == "Print parts in DB":
                self.print_parts(part_db)
            elif to_do == "Add Part":
                self.add_new_part(part_db)
            elif to_do == "Delete Part":
                self.delete_part(part_db)
            elif to_do == "Append Stock":
                self.add_stock_to_part(part_db)
            elif to_do == "Remove Stock":
                self.remove_stock_from_part(part_db)
            elif to_do == "Edit Part":
                self.edit_part(part_db)

    def choose_component(self) -> e7epd.spec.PartSpec:
        """
        Dialog to choose which component to use.
        Returns: The component class
        Raises _ChooseComponentDigikeyBarcode: If instead of a component by itself a Digikey barcode is scanned
        Raises KeyboardInterrupt: If a component is not chosen
        """
        pcb_choice = questionary.Choice(title=prompt_toolkit.formatted_text.FormattedText([('purple', 'PCBs')]))
        component = questionary.select("Select the component you want do things with:", choices=list(self.db.comp_types.keys()) + [pcb_choice, self.return_formatted_choice]).ask()
        if component is None or component == 'Return':
            raise KeyboardInterrupt()
        elif component == 'PCBs':
            # part_db = self.db.pcbs
            # todo: this
            raise KeyboardInterrupt()
            pass
        else:
            part_db = self.db.comp_types[component]
        return part_db

    def wipe_database(self):
        do_delete = questionary.confirm("ARE YOU SURE???", auto_enter=False, default=False).ask()
        if do_delete is True:
            do_delete = questionary.confirm("ARE YOU SURE...AGAIN???", auto_enter=False, default=False).ask()
            if do_delete is True:
                console.print("Don't regret this!!!")
                self.db.wipe_database()
                return
        if do_delete is not True:
            console.print("Did not delete the database")
            return

    def database_settings(self):
        console.print("Current selected database is: %s" % self.conf.get_selected_database())
        while 1:
            to_do = questionary.select("What do you want to? ", choices=["Add Database", "Wipe Database", "Print DB Info", "Select another database", self.return_formatted_choice]).ask()
            if to_do is None or to_do == "Return":
                break
            elif to_do == "Add Database":
                try:
                    ask_for_database(self.conf)
                except KeyboardInterrupt:
                    console.print("Did not add a new database")
                    continue
                console.print("Successfully added the new database")
            elif to_do == 'Wipe Database':
                self.wipe_database()
            elif to_do == "Select another database":
                db_name = questionary.select("Select the new database to connect to:", choices=self.conf.get_stored_db_names()).ask()
                if db_name is None:
                    console.print("Nothing new was selected")
                    continue
                self.conf.set_last_db(db_name)
                console.print("Selected the database %s" % db_name)
                console.print("[red]Please restart software for it to take into effect[/]")
                raise KeyboardInterrupt()
            elif to_do == "Print DB Info":
                db_name = questionary.select("Select the new database to connect to:", choices=self.conf.get_stored_db_names()).ask()
                if db_name is None:
                    console.print("Nothing new was selected")
                    continue
                t = self.conf.get_database_connection_info(db_name)
                if t['type'] == 'local':
                    console.print("This is a SQLite3 server, where the file path is {}".format(t['filename']))
                elif t['type'] == 'mysql_server':
                    console.print("This is a mySQL server, where:\nUsername: {username}\nDatabase Host: {db_host}\nDatabase Name: {db_name}".format(**t))

    # todo: this
    # def digikey_api_settings_menu(self):
    #     try:
    #         self.check_for_dk_api()
    #     except self._NoDigikeyApiError:
    #         return
    #     while 1:
    #         to_do = questionary.select("What do you want to? ", choices=["Set ClientID and ClientSecret", self.return_formatted_choice]).ask()
    #         if to_do is None or to_do == "Return":
    #             break
    #         if to_do == 'Set ClientID and ClientSecret':
    #             self.digikey_api_config_setup()

    def main(self):
        # Check DB version before doing anything
        if not self.db.is_latest_database():
            do_update = questionary.confirm("Database {:} is not at the latest version. Upgrade?".format(self.conf.get_selected_database()), auto_enter=False, default=False).ask()
            if do_update:
                self.db.update_database()
            else:
                console.print("[red]You chose to not update the database. Need to select or create another one[/]")
                try:
                    self.database_settings()
                except KeyboardInterrupt:
                    pass
                self.db.close()
                self.conf.save()
                return
        console.print(rich.panel.Panel("[bold]Welcome to the E707PD[/bold]\nDatabase Spec Revision {}, Backend Revision {}, CLI Revision {}\nSelected database {}".format(self.db.config.get_db_version(), e7epd.__version__, self.cli_revision, self.conf.get_selected_database()), title_align='center'))
        try:
            while 1:
                to_do = questionary.select("Select the component you want do things with:",
                                           choices=['Check components for PCB', 'Search Part', 'Add new part', 'Add new stock', 'Remove stock', 'Edit part', 'Individual Components View',
                                                    'Database Setting', 'Digikey API Settings', 'Exit'], use_shortcuts=True).ask()
                if to_do is None:
                    raise KeyboardInterrupt()
                elif to_do == 'Exit':
                    break
                elif to_do == 'Check components for PCB':
                    # todo: this
                    # self.print_pcb_and_component_availability()
                    continue
                elif to_do == 'Search Part':
                    self.print_parts()
                elif to_do == 'Add new part':
                    try:
                        self.add_new_part()
                    except KeyboardInterrupt:
                        continue
                elif to_do == 'Add new stock':
                    try:
                        self.add_stock_to_part()
                    except KeyboardInterrupt:
                        continue
                elif to_do == 'Remove stock':
                    try:
                        self.remove_stock_from_part()
                    except KeyboardInterrupt:
                        continue
                elif to_do == 'Edit part':
                    try:
                        self.edit_part()
                    except KeyboardInterrupt:
                        continue
                elif to_do == 'Individual Components View':
                    while 1:
                        try:
                            part_db = self.choose_component()
                            self.component_cli(part_db)
                        except KeyboardInterrupt:
                            break
                elif to_do == 'Database Setting':
                    self.database_settings()
                # elif to_do == 'Digikey API Settings':     # todo: this
                #     self.digikey_api_settings_menu()

        except KeyboardInterrupt:
            pass
        finally:
            console.print("\nGood night!")
            self.db.close()
            self.conf.save()


def ask_for_database(config: CLIConfig):
    console.print("Oh no, no database is configured. Let's get that settled")
    db_id_name = questionary.text("What do you want to call this database").unsafe_ask()
    is_server = questionary.select("Do you want the database to be a local file or is there a server running?", choices=['mongoDb']).unsafe_ask()
    if is_server == 'mongoDb':
        host = questionary.text("What is the database host?").unsafe_ask()
        username = questionary.text("What is the database username (Enter nothing for un-auth)?").unsafe_ask()
        if username == '':
            password = ''
            is_auth = False
        else:
            password = questionary.password("What is the database password?").unsafe_ask()
            is_auth = True
        config.save_database_as_mongo(database_name=db_id_name, username=username, password=password, host=host, authenticated=is_auth)


def main():
    parser = argparse.ArgumentParser(description='E7EPD CLI Application')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose mode', default=False)
    args = parser.parse_args()

    l = logging.getLogger()
    if args.verbose:
        l.setLevel(logging.DEBUG)
    else:
        l.setLevel(logging.ERROR)
    l.addHandler(RichHandler())

    c = CLIConfig()
    db_name = None
    while 1:
        try:
            db_conn = c.get_database_connection(db_name)
            break
        except c.NoDatabaseException:
            try:
                ask_for_database(c)
            except KeyboardInterrupt:
                console.print("No database given. Exiting")
                sys.exit(-1)
        except c.NoLastDBSelectionException:
            db_name = questionary.select("A database was not selected last time. Please select which database to connect to", choices=c.get_stored_db_names()).ask()
            if db_name is None:
                console.print("No database is selected to communicate to. Please restart and select something")
                sys.exit(-1)
        except c.DatabaseConnectionException:
            console.print("Unable to connect to database")
            sys.exit(-1)

    c = CLI(config=c, database_connection=db_conn)
    c.main()


if __name__ == "__main__":
    main()
