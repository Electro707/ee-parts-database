#!/usr/bin/python3
"""
    E707PD Python CLI Application
    Rev 0.7
"""
# External Modules Import
import csv
import dataclasses
import enum
from dataclasses import dataclass
import logging
import logging.handlers
import rich
import rich.console
import rich.panel
import rich.pretty
import rich.text
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
from typing import Optional, Dict, List, Any, Tuple, Literal, Union
import json
import pymongo
import pymongo.errors
import pymongo.database
import importlib.resources
import re
import warnings
import argparse
import urllib.parse
from prompt_toolkit.formatted_text import FormattedText
# Local import
from .lang.locale import PrintTexts, Locale
# e7epd imports
import e7epd
from e7epd.e707pd_spec import ShowAsEnum
import e7epd.label_making
import e7epd.test

console = rich.console.Console(style="blue")


def CLIConfig_config_db_list_checker(func):
    """A decorator that checks if we have database available in the config"""
    def wrap(self, *args, **kwargs):
        if len(self.config.db_list) == 0:
            raise self.NoDatabaseException()
        return func(self, *args, **kwargs)
    return wrap


class CLIConfig:
    @dataclass
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

    class DatabaseDeprecatedException(Exception):
        pass

    def __init__(self, data_path: Optional[str] = None):
        self.log = logging.getLogger('CLIConfig')

        if data_path is None:
            if sys.platform == 'win32':
                data_path = os.path.join(os.environ["APPDATA"], 'e7epd')
            else:
                data_path = os.path.expanduser('~/.config/e7epd')

        if not os.path.isdir(data_path):
            os.makedirs(data_path)

        self.file_path = os.path.join(data_path, "cli_config.json")
        self.config = self._Config()
        if os.path.isfile(self.file_path):
            with open(self.file_path) as f:
                self.config.from_dict(json.load(f))

    def save(self):
        with open(self.file_path, 'w') as f:
            json.dump(dataclasses.asdict(self.config), f, indent=4)

    @CLIConfig_config_db_list_checker
    def get_database_connection(self, database_name: str) -> pymongo.database.Database:
        """
        Gets a database connection based off the database name.

        Args:
            database_name: The database name (internal name) to get a connection to
                           If None, it uses the last database connection used
        """
        if database_name not in self.config.db_list:
            raise self.NoLastDBSelectionException()

        db_conf = self.config.db_list[database_name]

        self.config.last_db = database_name

        return self.get_database_client(db_conf)

    def get_database_client(self, db_conf: dict) -> pymongo.database.Database:
        """
        This function just returns the client, without any of the config checking.

        Args:
            db_conf: The database config dictionary
        Raises:
            DatabaseConnectionException: If the connection to the database fails
        """
        if db_conf['type'] in ['local', 'mysql_server', 'postgress_server']:
            raise self.DatabaseDeprecatedException("Not supported, deprecated in 0.7.0", db_conf)
        elif db_conf['type'] == 'mongodb':
            # todo: enable socket connection
            ssl_on = db_conf['ssl']
            if db_conf['auth']:
                conn_str = f"mongodb://{urllib.parse.quote(db_conf['username'])}:{urllib.parse.quote(db_conf['password'])}@{db_conf['db_host']}:27017/?authSource={db_conf['auth_db']}"
            else:
                conn_str = f"mongodb://{db_conf['db_host']}:27017/"
            conn = pymongo.MongoClient(conn_str, serverSelectionTimeoutMS=1000*2, tls=ssl_on)
            db = conn[db_conf['auth_db']]
            try:
                # The ping command is cheap and does not require auth.
                conn.admin.command('ping')
            except pymongo.errors.ConnectionFailure:
                self.log.exception("ConnectionFailure going to database")
                raise self.DatabaseConnectionException()
            except pymongo.errors.OperationFailure:
                self.log.exception("OperationFailure going to database")
                raise self.DatabaseConnectionException()
            return db
        else:
            raise ValueError(f"DB Configuration is invalid, was {db_conf['type']}")

    @CLIConfig_config_db_list_checker
    def get_database_connection_info(self, database_name: str) -> dict:
        return self.config.db_list[database_name]

    @CLIConfig_config_db_list_checker
    def get_stored_db_names(self) -> list:
        return list(self.config.db_list.keys())

    def is_any_db_config_stored(self) -> bool:
        return len(self.config.db_list) != 0

    @CLIConfig_config_db_list_checker
    def rename_database(self, old_name: str, new_name: str):
        self.config.db_list[new_name] = self.config.db_list.pop(old_name)
        # If we were using the old database, rename to the active one
        if self.config.last_db == old_name:
            self.config.last_db = new_name
        self.save()

    def get_selected_database(self) -> str:
        return self.config.last_db

    def is_db_valid(self, dbName) -> bool:
        if dbName not in self.config.db_list:
            return False
        return True

    def set_last_db(self, database_name: str):
        self.config.last_db = database_name

    def save_database_as_sqlite(self, database_name: str, file_name: str):
        raise DeprecationWarning("Removed in 0.7.0")

    def save_database_as_mysql(self, database_name: str, username: str, password: str, db_name: str, host: str):
        raise DeprecationWarning("Removed in 0.7.0")

    def save_database_as_postgress(self, database_name: str, username: str, password: str, db_name: str, host: str):
        raise DeprecationWarning("Removed in 0.7.0")

    def save_database_as_mongo(self, database_name: str, username: str, password: str, host: str, auth_db: str, authenticated: bool = False, ssl: bool = False):
        """
        Saves a database info as a Mongo
        Args:
            database_name: The database name (internal id)
            username: The db username
            password: The db password
            host: The db host
            auth_db: The authentication database, if any
            authenticated: Whether the server needs authentication or not
            ssl: Whether the connection will have ssl/tls enabled
        """
        self._save_database_generic(database_name, username, password, host)
        self.config.db_list[database_name]['type'] = 'mongodb'
        self.config.db_list[database_name]['auth'] = authenticated
        self.config.db_list[database_name]['auth_db'] = auth_db
        self.config.db_list[database_name]['ssl'] = ssl
        self.save()

    def _save_database_generic(self, database_name: str, username: str, password: str, host: str):
        if database_name not in self.config.db_list:
            self.config.db_list[database_name] = {}
        self.config.db_list[database_name]['username'] = username
        self.config.db_list[database_name]['password'] = password
        self.config.db_list[database_name]['db_host'] = host

    def delete_database(self, database_name: str):
        self.log.debug(f"Deleting database config {database_name}")
        if database_name not in self.config.db_list:
            raise self.NoLastDBSelectionException()
        del self.config.db_list[database_name]
        self.save()


class CLI:
    cli_revision = e7epd.__version__

    class _HelperFunctionExitError(Exception):
        def __init__(self, data=None):
            self.extra_data = data
            super().__init__()

    # class _ChooseComponentDigikeyBarcode(Exception):
    #     def __init__(self, mfg_part_number: str, dk_info: dict):
    #         self.mfg_part_number = mfg_part_number
    #         self.dk_info = dk_info
    #         super().__init__()

    def __init__(self, config: CLIConfig, database_connection: pymongo.database.Database):
        self.db = e7epd.E7EPD(database_connection)
        self.conf = config

        self.lang = Locale()

        self.printer = None
        if e7epd.label_making.direct_printing_failed is None:
            self.printer = e7epd.label_making.PrinterObject()

        self.return_formatted_choice = questionary.Choice(value='return', title=prompt_toolkit.formatted_text.FormattedText([('green', 'Return')]))
        # self.formatted_digikey_scan_choice = questionary.Choice(title=prompt_toolkit.formatted_text.FormattedText([('blue', 'Scan Digikey 2D Barcode')]), value='dk_scan')

    def print_error(self, text_key: PrintTexts, *args):
        to_print = self.lang.get(text_key).format(args)
        console.print(f"[red]{to_print:s}[/]")

    def print(self, text_key: PrintTexts, *args):
        to_print = self.lang.get(text_key).format(args)
        console.print(f"{to_print:s}")

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

    def _ask_ipn(self, existing_ipn_list: List[str] | Literal[True] | None = None) -> Optional[str]:
        """
        Asks for the IPN. This function handles type hinting with a given list, checking if the ipn
        is a Digikey barcode scan, and raises an error if the entered part number is already in the database or not.

        Args:
            existing_ipn_list: A list of current manufacturer part numbers to typehint, or if True show all IPNs in database

        Returns: The entered manufacturer part number
        """
        # Replace default argument
        if existing_ipn_list is None:
            ipn_list = []
        elif existing_ipn_list is True:
            ipn_list = self._get_all_ipns()
        else:
            ipn_list = existing_ipn_list

        if len(ipn_list) != 0:
            ipn_entered = questionary.autocomplete("Enter the IPN: ", choices=ipn_list).ask()
        else:
            ipn_entered = questionary.text("Enter the IPN: ").ask()
        if ipn_entered == '' or ipn_entered is None:
            return None

        ipn_entered = ipn_entered.strip().upper()

        return ipn_entered

    def _get_all_ipns(self):
        return self.db.get_all_parts_by_keys(None, 'ipn')

    def _ask_mfg_part_number(self, current_ipn: Optional[str] = None) -> str:
        """
        Asks the user for the manufacturer part number
        This function mainly exists in order to handle having the mfg part number be a copy of the ipn if
            nothing is typed in
        """
        prompt = "Enter the manufacturer part number: "
        if current_ipn:
            prompt = "Enter the MGF part number or just Enter to copy the IPN: "
        mfr_part_numb = questionary.text(prompt).ask()
        if mfr_part_numb == '':
            if current_ipn is None:
                self.print_error('must_have_mfg')
                raise self._HelperFunctionExitError()
            else:
                self.print_error('selecting_ipn_as_mfg')
                return current_ipn

        mfr_part_numb = mfr_part_numb.strip().upper()

        return mfr_part_numb

    def _ask_for_pcb_parts(self) -> list:
        """
        Called when wanting to input parts for a PCB
        # todo: allow BOM import, would make life easier
        """
        all_parts_dict = []
        all_ipn_parts = self.db.get_all_parts_by_keys(None, ret_key=['ipn', 'type'])
        all_ipns = [i['ipn'] for i in all_ipn_parts]
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
                ipn = self._ask_ipn(all_ipns)
                if ipn is None:
                    self.print_error('ipn_not_given')
                    continue
                if ipn not in all_ipns:
                    self.print_error('ipn_no_exist')
                    continue
                new_part['part']['ipn'] = ipn
                new_part['type'] = [i['type'] for i in all_ipn_parts if i['ipn'] == ipn][0]
            elif specific_part == "Generic":
                try:
                    part_type = self.choose_component_type()
                except KeyboardInterrupt:
                    self.print_error('ask_pcb.comp_type_not_selected')
                    continue
                new_part['type'] = part_type.db_type_name
                for spec_db_name in part_type.items:
                    if spec_db_name in e7epd.spec.BasePartItems.keys():
                        continue
                    # Select an autocomplete choice, or None if there isn't any
                    autocomplete_choices = self.get_autocomplete_list(spec_db_name, part_type.db_type_name)
                    # Get the spec
                    spec = part_type.items[spec_db_name]
                    if spec is None:
                        console.print("[red]INTERNAL ERROR: Got None when finding the spec for database name %s[/]" % spec_db_name)
                        raise self._HelperFunctionExitError()
                    # Ask the user for that property
                    try:
                        val, op = self.ask_for_spec_input_with_operator(spec, autocomplete_choices)
                        new_part['part'][spec_db_name] = {'val': val, 'op': op.value}
                    except KeyboardInterrupt:
                        console.print("Did not add part")
                        raise self._HelperFunctionExitError()
            else:
                console.print("[red]Invalid Choice![/]")
                continue
            # Ask for quantity
            try:
                qtyS = questionary.text("Enter quantity of this part used on this PCB:").ask()
                new_part['qty'] = int(qtyS)
            except ValueError:
                self.print_error('qty_invalid')
                continue
            new_part['designator'] = questionary.text("Enter the designator/reference:").ask()
            all_parts_dict.append(new_part)

        if len(all_parts_dict) == 0:
            self.print_error('ask_pcb.no_part_added')
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
        """ Prints all parts in the database per given type """
        parts_list = self.db.get_parts(part_type)
        self.print_parts_list(part_type, parts_list, title="All parts in %s" % part_type.showcase_name)

    def print_filtered_parts(self, part_type: e7epd.spec.PartSpec):
        """
        Prints all parts in a component database with filtering
        Args:
            part_type: The component spec class
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
            if s == 'ipn':
                inp = self._ask_ipn(self.db.get_all_parts_by_keys(part_type, 'ipn'))
                if inp is None:
                    console.print("Canceled part lookup")
                    return
                op = e7epd.ComparisonOperators.equal
            else:
                autocomplete_choices = self.get_autocomplete_list(s, part_type.db_type_name)
                try:
                    inp, op = self.ask_for_spec_input_with_operator(part_type.items[s], autocomplete_choices)
                except KeyboardInterrupt:
                    console.print("Canceled part lookup")
                    return
            print(s, inp, op)
            search_filter.append(e7epd.SpecWithOperator(key=s, val=inp, operator=op))
        try:
            parts_list = self.db.get_parts(part_type, search_filter)
        except e7epd.EmptyInDatabase:
            console.print("[red]No filtered parts in the database[/]")
            return
        self.print_parts_list(part_type, parts_list, title="All parts in %s" % part_type.showcase_name)

    def menu_search_parts(self):
        choice = [questionary.Choice(title=i.showcase_name, value=i) for i in self.db.comp_types] + [self.return_formatted_choice]
        choice.insert(0, questionary.Choice(title=prompt_toolkit.formatted_text.FormattedText([('orange', 'Search by IPN')])))
        component = questionary.select("Select the component you want do things with:", choices=choice).ask()
        if component is None or component == 'return':
            self.print_error('no_part_chosen')
            return

        if component == 'Search by IPN':
            all_ipn_list = self._get_all_ipns()
            ipn_number = self._ask_ipn(all_ipn_list)
            if ipn_number is None:
                self.print_error('ipn_not_given')
                return
            if ipn_number not in all_ipn_list:
                self.print_error('ipn_no_exist')
                return

            part = self.db.get_part_by_ipn(ipn_number)
            part_db = self.db.get_part_spec_by_db_name(part['type'])
            self.print_parts_list(part_db, [part], title="Searched Part %s" % ipn_number)
            return
        else:
            part_type = component

        if self.db.get_number_of_parts_in_db(part_type) == 0:
            self.print_error('search_parts.no_parts_type_comp')
            return
        all_parts = questionary.confirm("Do you want to filter the parts beforehand (to print all or not)?", default=False, auto_enter=True).ask(patch_stdout=False, kbi_msg="Exited option")
        if all_parts is None:
            return
        if all_parts:
            self.print_filtered_parts(part_type)
        else:
            self.print_all_parts(part_type)

    def ask_for_spec_input_with_operator(self, spec: e7epd.spec.SpecLineItem, choices: Optional[List[str]] = None,
                                         operator_allowed: bool = True) -> Tuple[Union[str, float, int], e7epd.ComparisonOperators]:
        """
        Function that prompts the user to enter the specification (resistance, package, etc) for a part.
        This function allows nicely type inputs like 10k

        Args:
            spec: The specification that we want the user to enter
            choices: A list of choices to show allow the user to select from
            operator_allowed: Whether to allow the user to enter an operator (like >1k)

        Returns: A tuple of
                    - The input given as the spec type (so for resistance it will return as a float)
                    - The operator to compare with the input if allowed, like == or >
        """
        op = e7epd.ComparisonOperators('==')
        while 1:
            to_ask = self.lang.get('ask_for_spec.enter_value').format(spec.showcase_name)
            if choices:
                val = questionary.autocomplete(to_ask, choices=choices).ask()
            else:
                val = questionary.text(to_ask).ask()
            if val is None:
                raise KeyboardInterrupt()
            if val == '':
                if spec.required is True:
                    self.print('ask_for_spec.must_enter_spec')
                    continue
                else:
                    val = None

            if val is not None:
                # Remove leading and trailing whitespace
                val = val.strip()
                if operator_allowed:
                    if val.startswith(tuple(['<', '<=', '>', '>='])):
                        op = re.findall(r'\>=|\>|\<=|\<', val)[0]
                        op = e7epd.ComparisonOperators(op)
                        val = re.sub(r'\>=|\>|\<=|\<', "", val)
                if spec.units != '':
                    if val.lower().endswith(spec.units.lower()):       # remove the engineering unit if applicable
                        val = val[:-len(spec.units)]
                if spec.shows_as == ShowAsEnum.engineering:
                    try:
                        val = EngNumber(val)
                    except decimal.InvalidOperation:
                        self.print('ask_for_spec.invalid_eng_numb')
                        continue
                elif spec.shows_as == ShowAsEnum.precentage:
                    if '%' in val:
                        val = val.replace('%', '')
                    else:
                        self.print('ask_for_spec.val_not_percentage')
                        continue
                elif '/' in val and spec.input_type is float:       # if fractional
                    val = val.split('/')
                    try:
                        val = float(val[0]) / float(val[1])
                    except ValueError:
                        self.print('ask_for_spec.val_not_fraction')
                        continue

                try:
                    if spec.input_type is int:
                        val = int(val)
                    elif spec.input_type is float:
                        val = float(val)
                except ValueError:
                    self.print('ask_for_spec.value_not_type', spec.input_type)
                    continue
            break
        return val, op

    def ask_for_spec_input(self, spec: e7epd.spec.SpecLineItem, choices: Optional[List[str]] = None):
        inp, op = self.ask_for_spec_input_with_operator(spec, choices, operator_allowed=False)
        return inp

    @staticmethod
    def get_autocomplete_list(db_name: str, table_name: str) -> typing.Union[None, list]:
        # todo: improve this for table name to point to type directly
        autocomplete_choices = None
        autofill_helpers = e7epd.spec.autofill_helpers_list
        if db_name == 'manufacturer' and table_name == 'ic':
            autocomplete_choices = autofill_helpers['ic_manufacturers']
        if db_name == 'manufacturer' and table_name == 'resistor':
            autocomplete_choices = autofill_helpers['passive_manufacturers']
        elif db_name == 'ic_type' and table_name == 'ic':
            autocomplete_choices = autofill_helpers['ic_types']
        elif db_name == 'cap_type' and table_name == 'capacitor':
            autocomplete_choices = autofill_helpers['capacitor_types']
        elif db_name == 'diode_type' and table_name == 'diode':
            autocomplete_choices = autofill_helpers['diode_type']
        elif db_name == 'bjt_type' and table_name == 'bjt':
            autocomplete_choices = autofill_helpers['bjt_types']
        elif db_name == 'mosfet_type' and table_name == 'mosfet':
            autocomplete_choices = autofill_helpers['mosfet_types']
        elif db_name == 'led_type' and table_name == 'led':
            autocomplete_choices = autofill_helpers['led_types']
        elif db_name == 'fuse_type' and table_name == 'fuse':
            autocomplete_choices = autofill_helpers['fuse_types']
        # Package Auto-Helpers
        elif db_name == 'package' and table_name == 'ic':
            autocomplete_choices = autofill_helpers['ic_packages']
        elif db_name == 'package' and (table_name == 'resistor' or table_name == 'capacitor' or table_name == 'inductor'):
            autocomplete_choices = autofill_helpers['passive_packages']
        return autocomplete_choices

    def add_new_pcb(self):
        new_pcb = {}
        for spec_db_name in e7epd.spec.PCBItems:
            if spec_db_name == 'parts':
                new_pcb['parts'] = self._ask_for_pcb_parts()
            else:
                try:  # Ask the user for that property
                    new_pcb[spec_db_name] = self.ask_for_spec_input(e7epd.spec.PCBItems[spec_db_name])
                except KeyboardInterrupt:
                    self.print_error('no_add_pcb')
                    return
        self.db.add_new_pcb(new_pcb)

    def menu_add_new_part(self, part_type: Optional[e7epd.spec.PartSpec] = None):
        """ Function gets called when a part is to be added """
        try:
            ipnList = self._get_all_ipns()
            ipn = self._ask_ipn(ipnList)
            if ipn is None:
                self.print_error("ipn_not_given")
                return
            if ipn in ipnList:
                if questionary.confirm("Would you like to instead add the parts to your stock?", auto_enter=False, default=True).ask():
                    self.menu_add_stock_to_part(ipn)
                return

            if part_type is None:
                part_type = self.choose_component_type(True)
            part_type: e7epd.spec.PartSpec

            if part_type == e7epd.spec.PCBItems:
                console.print("Adding PCB instead")
                self.add_new_pcb()
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
                    autocomplete_choices = self.db.get_autocomplete_list(part_type, spec_db_name)
                    try:        # Ask the user for that property
                        new_part[spec_db_name] = self.ask_for_spec_input(part_type.items[spec_db_name], autocomplete_choices)
                    except KeyboardInterrupt:
                        console.print("Did not add part")
                        return
            if self.printer:
                if self.printer.get_availability():
                    if questionary.confirm("Want to print IPN barcode?", auto_enter=False, default=True).ask():
                        self.printer.open()
                        e7epd.label_making.print_barcodes(new_part['ipn'], self.printer)
                        self.printer.close()
            # todo: move this above print function. is here to test above function
            self.db.add_new_part(part_type, new_part)

        except KeyboardInterrupt:
            console.print("\nOk, no part is added")
            return

    # def delete_part(self, part_db: e7epd.spec.PartSpec):
    #     """ This gets called when a part is to be deleted """
    #     part_db, ipn = self.get_partdb_and_ipn(part_db, True)
    #     if questionary.confirm("ARE YOU SURE...AGAIN???", auto_enter=False, default=False).ask():
    #         try:
    #             self.db.delete_part(part_db, ipn)
    #         except e7epd.EmptyInDatabase:
    #             console.print("[red]The manufacturer is not in the database[/]")
    #         else:
    #             console.print(f"Deleted {ipn} from the database")
    #     else:
    #         console.print("Did not delete the part, it is safe.")

    def menu_add_stock_to_part(self, ipn: Optional[str] = None):
        try:
            allIpns = self._get_all_ipns()
            if ipn is None:        # If we did not pass a pre-selected mfg part number and part db, ask for it
                ipn = self._ask_ipn(allIpns)
                if ipn is None:
                    self.print_error('ipn_not_given')
                    return
                if ipn not in allIpns:
                    self.print_error('ipn_no_exist')
                    return
            component = self.db.get_part_by_ipn(ipn)
            if component is None:
                self.print_error('menu_add_stock.bug_no_comp')
                return
            self.print('menu_add_stock.list_comp_count', component['stock'])
            while 1:
                add_by = questionary.text(self.lang.get('menu_add_stock.ask_add')).ask()
                if add_by is None:
                    raise KeyboardInterrupt()
                try:
                    add_by = int(add_by)
                except ValueError:
                    self.print('menu_add_stock.must_be_int')
                    continue
                if add_by < 0:
                    self.print('menu_add_stock.must_be_not_zero')
                    continue
                break
            component['stock'] += add_by
            self.db.update_part_stock(ipn, component['stock'])
            console.print(f'[green]' + self.lang.get('menu_add_stock.added_part').format(component['stock']) + '[/]')
        except KeyboardInterrupt:
            self.print('menu_add_stock.no_change')
            return

    def menu_remove_loop(self):
        """A loop that continuously removes parts from the database per scan, until CTRL+C is entered"""
        console.print("Scan your parts in this loop in order to remove them from your stock")
        console.print("If you want to remove multiple, type '10x ' and scan the IPN (note the space)")
        while True:
            to_remove = questionary.text("Scan barcode to remove: ").ask()
            if to_remove is None:
                console.print("done with removing parts")
                return
            to_remove: str
            to_remove = to_remove.strip()
            qty, sep, ipn = to_remove.partition(" ")
            if sep == '':   # if we don't have a space, the ipn is the whole string
                ipn = qty
                qtyN = 1
            else:
                if not qty.endswith('x'):
                    console.print("[red]Quantity must end with x, like 10x[/]")
                    continue
                try:
                    qtyN = int(qty[:-1])
                except ValueError:
                    console.print("[red]Quanitity must be an integer[/]")
                    continue

            if not self.db.check_if_already_in_db_by_ipn(ipn):
                console.print("[red]IPN scanned/entered not valid[/]")
                continue
            try:
                self.db.remove_part_stock(ipn, qtyN)
            except e7epd.NegativeStock:
                console.print(f'[red]Unable to remove part, stock will go negative[/]')
            else:
                console.print(f'[green]Removed {qtyN:d} of {ipn:s} from stock[/]')

    def menu_remove_stock_from_part(self):
        try:
            allIpns = self._get_all_ipns()
            ipn = self._ask_ipn(allIpns)
            if ipn is None:
                console.print("[red]No IPN selected[/]")
                return
            if ipn not in allIpns:
                console.print("[red]IPN not in database[/]")
                return
            component = self.db.get_part_by_ipn(ipn)
            assert component is not None
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

    def menu_edit_part(self):
        """
        Function to update the part's properties
        """
        to_update = {}  # A separate variable for only keys that need changing
        try:
            # Ask for manufacturer part number first, and make sure there are no conflicts
            allIpns = self.db.get_all_parts_by_keys(None, 'ipn')
            ipn = self._ask_ipn(allIpns)
            if ipn is None:
                console.print("[red]No IPN selected[/]")
                return
            if ipn not in allIpns:
                console.print("[red]IPN not in database[/]")
                return
            component = self.db.get_part_by_ipn(ipn)
            assert component is not None
            part_db = self.db.get_part_spec_by_db_name(component['type'])
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
                    new_val = self.ask_for_spec_input(part_db.items[to_change], self.get_autocomplete_list(to_change, part_db.db_type_name))
                    to_update[to_change] = new_val
                    component[to_change] = new_val
                except KeyboardInterrupt:
                    console.print("Did not change spec")
                    continue
        except KeyboardInterrupt:
            console.print("Did not change part")
            return

    def menu_print_pcbs_list(self):
        all_boards = self.db.get_all_unique_pcbs()
        if len(all_boards) == 0:
            console.print("There are no PCBs in the database")
            return

        ta = rich.table.Table(title='All PCBs')
        ta.add_column("PCB Name")
        ta.add_column("PCB ID")
        ta.add_column("PCB Rev")
        for pcb in all_boards:
            ta.add_row(pcb['name'], pcb['id'], pcb['rev'])
        console.print(ta)

    def menu_print_pcb_and_component_availability(self):
        all_boards = self.db.get_all_unique_pcbs()
        if len(all_boards) == 0:
            console.print("There are no PCBs in the database")
            return
        all_boards = {f"{i['name']} Rev {i['rev']}": (i['id'], i['rev']) for i in all_boards}
        all_board_name = list(all_boards.keys())
        all_board_name.sort()
        board_name = questionary.autocomplete("Enter the PCB name: ", choices=all_board_name).ask()
        if board_name == '':
            console.print("No board is given")
            return

        board = self.db.get_pcb(all_boards[board_name][0], all_boards[board_name][1])

        all_parts_in_board = []         # type: typing.List[tuple]
        for board_part in board['parts']:
            parts = self.db.find_pcb_part(board_part)
            if parts is None or len(parts) == 0:
                all_parts_in_board.append(([str(board_part['qty']), board_part['designator'], '-', '-', '-', '-'], 'red'))
            elif len(parts) == 1:
                part = parts[0]
                all_parts_in_board.append(([str(board_part['qty']), board_part['designator'], part['type'], part['ipn'], f"{part['stock']:d}", part['storage']], None))
            else:
                for partI, part in enumerate(parts):
                    l = ['', '', '']
                    if partI == 0:
                        l = [str(board_part['qty']), board_part['designator'], part['type']]
                    l.append(part['ipn'])
                    l.append(f"{part['stock']:d}")
                    l.append(part['storage'])
                    all_parts_in_board.append((l, 'yellow'))

        console.print("You currently have {:d} PCBs available".format(board['stock']))

        ta = rich.table.Table(title='All components for {} Rev {}'.format(board['name'], board['rev']))
        ta.add_column("Stock Required")
        ta.add_column("Reference")
        ta.add_column("Component Type")
        ta.add_column("Available IPN#")
        ta.add_column("Stock Available")
        ta.add_column("Component Location")
        for parts_in_db in all_parts_in_board:
            ta.add_row(*parts_in_db[0], style=parts_in_db[1])
        console.print(ta)

        return

    # def component_cli(self, part_db: e7epd.spec.PartSpec):
    #     """ The CLI handler for components """
    #     while 1:
    #         to_do = questionary.select("What do you want to do in this component database? ", choices=["Print parts in DB", "Append Stock", "Remove Stock", "Add Part", "Delete Part", "Edit Part", self.return_formatted_choice]).ask()
    #         if to_do is None:
    #             raise KeyboardInterrupt()
    #         if to_do == "Return":
    #             break
    #         elif to_do == "Print parts in DB":
    #             self.search_parts(part_db)
    #         elif to_do == "Add Part":
    #             self.add_new_part(part_db)
    #         elif to_do == "Delete Part":
    #             self.delete_part(part_db)
    #         elif to_do == "Append Stock":
    #             self.add_stock_to_part(part_db)
    #         elif to_do == "Remove Stock":
    #             self.remove_stock_from_part(part_db)
    #         elif to_do == "Edit Part":
    #             self.edit_part(part_db)

    def choose_component_type(self, allow_pcb: bool = False) -> e7epd.spec.PartSpec:
        """
        Dialog to choose which component to use.
        Returns: The component class
        Raises KeyboardInterrupt: If a component is not chosen
        """
        choice = [questionary.Choice(title=i.showcase_name, value=i) for i in self.db.comp_types] + [self.return_formatted_choice]
        if allow_pcb:
            pcb_choice = questionary.Choice(title=prompt_toolkit.formatted_text.FormattedText([('purple', 'PCBs')]).__repr__())
            choice.insert(-1, pcb_choice)
        component = questionary.select("Select the component you want do things with:", choices=choice).ask()
        if component is None or component == 'return':
            raise KeyboardInterrupt()
        elif component == 'PCBs':
            part_db = e7epd.spec.PCBItems
        else:
            part_db = component
        return part_db

    def menu_print_export_barcode(self):
        def isfloat(num):
            try:
                float(num)
                return True
            except ValueError:
                return False

        if e7epd.label_making.available is not None:
            console.print(f"Cannot make barcodes (due to \"{e7epd.label_making.available}\")")
            return

        assert self.printer is not None

        direct_print = False
        if self.printer:
            r = questionary.select("Choose whether you want to export to directly print", choices=['Print to PTouch', 'Export to PDF']).ask()
            if r is None:
                return
            if 'Print' in r:
                direct_print = True
        else:
            console.print(f"Cannot directly print to printer, choosing export to pdf (due to \"{e7epd.label_making.direct_printing_failed}\")")

        if direct_print:
            if not self.printer.get_availability():
                console.print("Unable to connect to a PTouch printer, reverting to export mode")
                direct_print = False

        width = None
        export_path = None
        if not direct_print:
            export_path = questionary.path("Select the pdf export path and name", default=os.getcwd() + '/').ask()
            if export_path is None or export_path == "":
                return
            export_path = os.path.abspath(export_path)
            if os.path.isdir(export_path):
                console.print("Selected path is a folder")
                return

            width = questionary.text("What is the tape size in mm (printable area)", validate=isfloat).ask()
            if width is None or width == "":
                return
            width = float(width)

        allIpns = self._get_all_ipns()
        ipn = self._ask_ipn(allIpns)
        if ipn is None:
            self.print_error('ipn_not_given')
            return
        if ipn not in allIpns:
            self.print_error('ipn_no_exist')
            return

        if direct_print:
            self.printer.open()
            e7epd.label_making.print_barcodes(ipn, self.printer)
            self.printer.close()
        else:
            assert width is not None            # assert checks for typechecking
            assert export_path is not None      # assert checks for typechecking
            e7epd.label_making.export_barcodes(ipn, width, export_path)

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

    def menu_database_settings(self):
        class MenuDatabaseSettingsOptions(enum.StrEnum):
            ADD = "Add Database"
            RENAME = "Rename Database"
            WIPE = "Wipe Database"
            PRINT_INFO = "Print DB Info"
            SELECT_OTHER = "Select another database"
        console.print(f"Current selected database is: {self.conf.get_selected_database()}")
        while True:
            to_do = questionary.select("What do you want to? ", choices=list(MenuDatabaseSettingsOptions) + [self.return_formatted_choice]).ask()
            if to_do is None or to_do == 'return':
                break
            elif to_do == MenuDatabaseSettingsOptions.ADD:
                ret = ask_and_save_new_db_config(self.conf)
                if ret is None:
                    console.print("Did not add a new database")
                    continue
                console.print("Successfully added the new database")
            elif to_do == MenuDatabaseSettingsOptions.WIPE:
                self.wipe_database()
            elif to_do == MenuDatabaseSettingsOptions.SELECT_OTHER:
                db_name = questionary.select("Select the new database to connect to:", choices=self.conf.get_stored_db_names() + [self.return_formatted_choice]).ask()
                if db_name is None or db_name == 'return':
                    console.print("Nothing new was selected")
                    continue
                self.conf.set_last_db(db_name)
                console.print("Selected the database %s" % db_name)
                console.print("[red]Please restart software for it to take into effect[/]")
                raise KeyboardInterrupt()
            elif to_do == MenuDatabaseSettingsOptions.PRINT_INFO:
                db_name = questionary.select("Select the new database to connect to:", choices=self.conf.get_stored_db_names()).ask()
                if db_name is None:
                    console.print("Nothing new was selected")
                    continue
                t = self.conf.get_database_connection_info(db_name)
                if t['type'] == 'mongodb':
                    console.print("This is a Mongo server, where")
                    console.print(f"\tDatabase Host: {t['db_host']}")
                    console.print(f"\tMongo Auth DB: {t['auth_db']}")
                    if t['auth']:
                        console.print("\tAuthentication Enabled")
                        console.print(f"\tUsername: {t['username']}")
                    else:
                        console.print("\tAuthentication Disabled")
            elif to_do == MenuDatabaseSettingsOptions.RENAME:
                db_name = questionary.select("Select the new database to connect to:", choices=self.conf.get_stored_db_names()).ask()
                if db_name is None:
                    console.print("Nothing new was selected")
                    continue
                new_name = questionary.text("Type the new database name", default=db_name).ask()
                if new_name is None:
                    console.print("Nothing new was selected")
                    continue
                if db_name == new_name:
                    console.print("Entered same name for database, not renaming")
                    continue
                do_rename = questionary.confirm(f"Confirm to rename '{db_name}' to '{new_name}'", auto_enter=False, default=False).ask()
                if do_rename:
                    self.conf.rename_database(db_name, new_name)
                else:
                    console.print("Operation cancelled")

    def menu_pcb(self):
        class MenuPcbOptions(enum.StrEnum):
            LIST = "List all PCBAs"
            CHECK_COMP = "Check components for PCBA"
            ADD = "Add PCB"

        while True:
            to_do = questionary.select("What do you want to? ", choices=list(MenuPcbOptions) + [self.return_formatted_choice]).ask()
            if to_do is None or to_do == 'return':
                break
            elif to_do == MenuPcbOptions.CHECK_COMP:
                self.menu_print_pcb_and_component_availability()
            elif to_do == MenuPcbOptions.LIST:
                self.menu_print_pcbs_list()
            elif to_do == MenuPcbOptions.ADD:
                self.add_new_pcb()


    def main(self):
        class MenuCliOptions(enum.StrEnum):
            SEARCH = "Search Part"
            ADD_PART = "Add new part"
            ADD_STOCK = "Add new stock"
            REMOVE_STOCK = "Remove stock"
            EDIT = "Edit Part"
            DB = "Database Settings"
            PCB = "PCB Submenu"
            REMOVE_STOCK_LOOP = "Enter removal mode"
        # Check DB version before doing anything
        if not self.db.is_latest_database():
            do_update = questionary.confirm("Database {:} is not at the latest version. Upgrade?".format(self.conf.get_selected_database()), auto_enter=False, default=False).ask()
            if do_update:
                self.db.update_database()
            else:
                console.print("[red]You chose to not update the database. Need to select or create another one[/]")
                try:
                    self.menu_database_settings()
                except KeyboardInterrupt:
                    pass
                self.db.close()
                self.conf.save()
                return
        console.print(rich.panel.Panel("[bold]Welcome to the E707PD[/bold]\n"
                                       "Database Spec Revision {}, Backend Revision {}, CLI Revision {}\n"
                                       "Selected database {}".format(self.db.config.get_db_version(), e7epd.__version__, self.cli_revision, self.conf.get_selected_database()), title_align='center'))
        try:
            while 1:
                choices = list(MenuCliOptions)
                choices += [questionary.Choice(title='Print/Export Barcode', disabled=e7epd.label_making.available)]
                choices += ['Exit']
                to_do = questionary.select("Select what to do:", choices=choices, use_shortcuts=True).ask()
                if to_do is None:
                    raise KeyboardInterrupt()
                elif to_do == 'Exit':
                    break
                elif to_do == MenuCliOptions.PCB:
                    self.menu_pcb()
                elif to_do == MenuCliOptions.SEARCH:
                    self.menu_search_parts()
                elif to_do == MenuCliOptions.ADD_PART:
                    try:
                        self.menu_add_new_part()
                    except KeyboardInterrupt:
                        continue
                elif to_do == MenuCliOptions.ADD_STOCK:
                    try:
                        self.menu_add_stock_to_part()
                    except KeyboardInterrupt:
                        continue
                elif to_do == MenuCliOptions.REMOVE_STOCK:
                    try:
                        self.menu_remove_stock_from_part()
                    except KeyboardInterrupt:
                        continue
                elif to_do == MenuCliOptions.EDIT:
                    try:
                        self.menu_edit_part()
                    except KeyboardInterrupt:
                        continue
                elif to_do == 'Print/Export Barcode':
                    try:
                        self.menu_print_export_barcode()
                    except KeyboardInterrupt:
                        continue
                elif to_do == MenuCliOptions.DB:
                    self.menu_database_settings()
                elif to_do == MenuCliOptions.REMOVE_STOCK_LOOP:
                    self.menu_remove_loop()
                # elif to_do == 'Digikey API Settings':     # todo: this
                #     self.digikey_api_settings_menu()

        except KeyboardInterrupt:
            pass
        finally:
            console.print("\nGood night!")
            self.db.close()
            self.conf.save()


def ask_and_save_new_db_config(config: CLIConfig) -> Optional[Tuple[str, pymongo.database.Database]]:
    """
    Asks the user for a database info. Returns None if nothing is given, or if the internal operation fails
    """
    if (db_id_name := questionary.text("What do you want to call this database").ask()) is None:
        return None
    # todo: re-implement when we have more than just MongoDB
    # if (is_server := questionary.select("Do you want the database to be a local file or is there a server running?", choices=['mongoDb']).ask()) is None:
    #     return None
    # if is_server == 'mongoDb':
    if (host := questionary.text("What is the database host?").ask()) is None:
        return None
    if (ssl := questionary.confirm("Will the server be connected with SSL/TSL?", auto_enter=False, default=False).ask()) is None:
        return None
    if (auth_db := questionary.text("What is the database name you want to use (and auth database of authenticating if setup?)").ask()) is None:
        return None
    if (username := questionary.text("What is the database username (Enter nothing for un-auth)?").ask()) is None:
        return None
    if username == '':
        password = ''
        is_auth = False
    else:
        if (password := questionary.password("What is the database password?").ask()) is None:
            return None
        is_auth = True
    config.save_database_as_mongo(database_name=db_id_name, username=username, password=password, host=host, authenticated=is_auth, ssl=ssl, auth_db=auth_db)
    # try and get the database
    try:
        db_conn = config.get_database_connection(db_id_name)
    except config.DatabaseConnectionException:
        console.print("Failed with new database...removing it")
        config.delete_database(db_id_name)
        return None

    return db_id_name, db_conn


# def print_barcodes(conf: CLIConfig, database_connection: pymongo.database.Database):
#     def isfloat(num):
#         try:
#             float(num)
#             return True
#         except ValueError:
#             return False
#
#     db = e7epd.E7EPD(database_connection)
#
#     export = questionary.path("Select the pdf export path and name", default=os.getcwd() + '/').ask()
#     if export is None or export == "":
#         return
#     export = os.path.abspath(export)
#     if os.path.isdir(export):
#         console.print("Selected path is a folder")
#         return
#
#     width = questionary.text("What is the tape size in mm", validate=isfloat).ask()
#     if width is None or width == "":
#         return
#     width = float(width)
#
#     choice = [questionary.Choice(title=FormattedText([('blue', 'All')]))] + \
#              [questionary.Choice(title=i.showcase_name, value=i) for i in db.comp_types] + \
#              [questionary.Choice(title=FormattedText([('green', 'Return')]))]
#     component = questionary.select("Select the component you want do things with:", choices=choice).ask()
#     if component is None or component == 'Return':
#         return
#     elif component == 'All':
#         part_db = None
#     else:
#         part_db = component
#     ipn_list = db.get_all_parts_by_keys(part_db, 'ipn')
#     e7epd.label_making.export_barcodes(ipn_list, width, export)


def import_order_csv(cli: CLI):
    """Imports an order CSV and/or prints labels for them"""
    TESTING_DEFAULT_CSV = ''        # for testing
    # TESTING_DEFAULT_CSV = '/home/electro/Downloads/DK_PRODUCTS_101423034.csv'

    allow_print = True
    if e7epd.label_making.available:
        res = questionary.confirm(f"Printing order is not possible due to python ({e7epd.label_making.available}). Continue?", False).ask()
        if res is not True:
            return
        allow_print = False
    if e7epd.label_making.direct_printing_failed:
        res = questionary.confirm(f"Will be unable to print to barcode label ({e7epd.label_making.direct_printing_failed}). Continue?", False).ask()
        if res is not True:
            return
        allow_print = False

    printer = None
    if allow_print:
        printer = e7epd.label_making.PrinterObject()
        if not printer.open():
            console.print("[red]Unable to open printer, exiting[/]")
            return
        w = printer.get_tape_width_px()
        if w == 0:
            console.print("[orange]No tape installed in printer[/]")
            return

    # digikey specific, for now
    # todo: allow user to select columns
    column_names = {
        'mfg_part_numb': 'Manufacturer Part Number',
        'ipn': 'Manufacturer Part Number',
        'comments': 'Description',
        'manufacturer': 'Manufacturer',
        'stock': 'Quantity',
    }
    column_index = {}

    try:
        allParts = []

        path = questionary.path("Enter the path for Digikey csv file", TESTING_DEFAULT_CSV).ask()
        if path is None:
            return
        path = path.strip()
        path = os.path.expanduser(path)
        if not os.path.isfile(path):
            console.print(f"Path given ({path}) is not a file not exist")
            return

        with open(path, 'r', newline='') as f:
            reader = csv.reader(f)
            header = reader.__next__()      # read header
            for dbName, colN in column_names.items():
                if colN not in header:
                    console.print(f"The CSV doesn't have the required column {colN}, bailing")
                    return
                column_index[dbName] = header.index(colN)

            for row in reader:
                partInfo = {}
                # ignore any parts that don't have a part number, such as a subtotal row
                if row[column_index['ipn']] == '':
                    continue
                for dbName, idx in column_index.items():
                    partInfo[dbName] = e7epd.e707pd_spec.BasePartItems[dbName].input_type(row[idx])
                allParts.append(partInfo)

        # print(allParts)

        existingPartsInp = cli.db.get_all_parts_by_keys(None, 'ipn')

        for part in allParts:
            addPart = questionary.confirm(f"Import {part['ipn']} - {part['comments']} QTY={part['stock']}?", True, auto_enter=False).unsafe_ask()
            if addPart is not True:
                console.print(f"Skipping part {part['ipn']}")
                continue

            # check if we already imported this part, and if so prompt to add instead
            if part['ipn'] in existingPartsInp:
                console.print(f"Part already exists in database, adding to stock")
                cli.db.add_part_stock(part['ipn'], part['stock'])
            else:
                part_type = cli.choose_component_type()
                part_to_save = {}
                part_to_save.update(part)
                for spec_db_name in part_type.table_display_order:
                    # Skip over existing parameters that we imported
                    if spec_db_name in part_to_save:
                        continue
                    # Select an autocomplete choice, or None if there isn't any
                    autocomplete_choices = cli.db.get_autocomplete_list(part_type, spec_db_name)
                    try:  # Ask the user for that property
                        part_to_save[spec_db_name] = cli.ask_for_spec_input(part_type.items[spec_db_name], autocomplete_choices)
                    except KeyboardInterrupt:
                        console.print("Did not add part")
                        return
                cli.db.add_new_part(part_type, part_to_save)
            if printer:
                if questionary.confirm("Want to print IPN barcode?", auto_enter=False, default=True).ask():
                    e7epd.label_making.print_barcodes([part['ipn']], printer)
            # todo: move this above print function. is here to test above function


        # if not questionary.confirm(f"Are you sure you want to print {len(allParts)} part numbers?").ask():
        #     return
        # # todo: perhaps a selection option? Or have it cross-reference the database for existing mfgs?
        # e7epd.label_making.print_barcodes(allMfg, printer)
    except KeyboardInterrupt:
        console.print("Exiting out of import")
    finally:
        if printer:
            printer.close()

def import_pcb_bom(db_conn: pymongo.database.Database, import_file: str):
    """WIP, a function to allow importing of BOMs as PCB items"""
    log = logging.getLogger('importer_app')

    db = e7epd.E7EPD(db_conn)
    if not os.path.isfile(import_file):
        console.print("[red]The given file does not exist[/]")
        return
    _, f_ext = os.path.splitext(import_file)
    if f_ext != '.csv':
        console.print("[red]The given file is not a CSV[/]")
        return

    requiredHeader = {
        'designator': ['designator'],
        'qty': ['qty', 'quantity'],
    }
    headerIdx = {}

    with open(import_file, 'r', newline='') as f:
        reader = csv.reader(f)

        header = reader.__next__()
        for reqH in requiredHeader:
            pass


def importer_app(conf: CLIConfig, database_connection: pymongo.database.Database, import_file: str):
    """
    An importer sub-application that imports an existing "database" from a CSV file

    TODO: untested

    Args:
        conf:
        database_connection:
        import_file:

    Returns:

    """
    log = logging.getLogger('importer_app')

    if not os.path.isfile(import_file):
        console.print("[red]The given file does not exist[/]")
        return

    _, f_ext = os.path.splitext(import_file)
    if f_ext != '.csv':
        console.print("[red]The given file is not a CSV[/]")
        return

    todo = questionary.confirm(f"Do you want to import data from {import_file}", auto_enter=False, default=False).ask()
    if todo is False:
        console.print("Not importing file")
        return

    db = e7epd.E7EPD(database_connection)

    new_parts = []
    with open(import_file, 'r') as f:
        header = f.readline().strip()
        header = header.split(',')
        console.print("The following are your headers: (column, header name)")
        for i, h in enumerate(header):
            console.print(f"\t{i} --> {h}")

        # Map the columns to a key
        column_to_key = {}
        """Maps a column index to a part spec key (stock, resistance, etc)"""
        try:
            for i, h in enumerate(header):
                choices = [questionary.Choice(title=f"{v.showcase_name} (Required)" if v.required else f"{v.showcase_name}", value=i) for i, v in e7epd.spec.BasePartItems.items() if i not in column_to_key.values()]
                if 'type' not in column_to_key.values():
                    choices += [questionary.Choice(title=FormattedText([('blue', 'Part Type (Required)')]).__repr__(), value='type')]
                choices += [questionary.Choice(title=FormattedText([('orange', 'None/Other')]).__repr__(), value='None')]
                a = questionary.select(f"What database key matches the column {i} ({h})?", choices=choices).unsafe_ask()
                if a == 'None':
                    a = None
                column_to_key[i] = a
        except KeyboardInterrupt:
            console.print("[red]Exited[/]")
            return

        # Check for all required keys for the base part
        console.print(f"The following is the mapping between column and database key: {column_to_key}")
        for c in e7epd.spec.BasePartItems:
            if e7epd.spec.BasePartItems[c].required and c not in column_to_key.values():
                console.print(f"Did not select the required key [bold]'{c}'[/bold]")
                return

        console.print(f"The following is the mapping between column and database key: {column_to_key}")

        # Go through the entire file (kind of stupid, but no easy way around it) to check for all possible types
        # then ask the user what column will be used for the part parameter
        csv_type_to_internal_type = {}      # type: typing.Dict[str, e7epd.spec.PartSpec]
        part_type_choice = [questionary.Choice(i.showcase_name, value=i) for i in db.comp_types]
        type_col = [i for i in column_to_key if column_to_key[i] == 'type'][0]      # get column where the type keyword exists
        column_to_key_parts = {}
        for line_i, line in enumerate(f):
            lineS = line.strip().split(',')
            if len(header) != len(lineS):
                console.print(f"[red]Line {line_i} is not the same length as the header. Exiting[/]")
                return
            line_item = lineS[type_col]
            if line_item not in csv_type_to_internal_type:
                pt = questionary.select(f"What is the part type for string '{line_item}'?", choices=part_type_choice).unsafe_ask()
                csv_type_to_internal_type[str(line_item)] = pt
                column_to_key_parts[pt.db_type_name] = {}
                # ask the user which columns go with part-specific keys
                for i, h in enumerate(header):
                    # if we have the column in the "base part" item mapping, then don't both with the particular column for this
                    if column_to_key[i] is not None:
                        continue
                    choices = [questionary.Choice(title=f"{v.showcase_name} (Required)" if v.required else f"{v.showcase_name}", value=i) for i, v in pt.items.items() if
                               i not in column_to_key.values() and i not in e7epd.spec.BasePartItems.keys()]
                    choices += [questionary.Choice(title=prompt_toolkit.formatted_text.FormattedText([('orange', 'None')]).__repr__(), value='None')]
                    a = questionary.select(f"What database key matches the column {i} ({h})?", choices=choices).unsafe_ask()
                    if a == 'None':
                        a = None
                    column_to_key_parts[pt.db_type_name][i] = a

        console.print(f"The following is the mapping between column and database key: {column_to_key_parts}")

        # Now go back to the beginning of the file for the rest of the import, skipping the header of course!
        f.seek(0)
        f.readline()
        try:
            # Go thru, and for each line add it as a part
            for line_i, lineS in enumerate(f):
                new_part = {}
                line = lineS.strip().split(',')
                if len(header) != len(line):
                    console.print(f"[red]Line {line_i} is not the same length as the header. Exiting[/]")
                    return
                # get the type first (to check for type in other params)
                new_part['type'] = csv_type_to_internal_type[line[type_col]]
                # for each column in a particular row, add the information to new_part
                for column_i, line_item in enumerate(line):
                    if column_to_key[column_i] == 'type':   # we already have the type, don't worry about it again
                        continue

                    if column_to_key[column_i] is not None:
                        curr_column_key = column_to_key[column_i]
                        line_type = e7epd.spec.BasePartItems[curr_column_key].input_type
                    elif column_i in column_to_key_parts[new_part['type'].db_type_name]:
                        curr_column_key = column_to_key_parts[new_part['type'].db_type_name][column_i]
                        line_type = new_part['type'].items[curr_column_key].input_type
                    else:
                        continue

                    try:
                        if line_type in [float, int]:
                            # shitty attempt at removing any units by removing the last char of a string if it's not a number
                            for end_unit in ['ohm', 'F', 'H', 'Ω']:
                                if line_item.endswith(end_unit):
                                    line_item = line_item[:-(len(end_unit))]
                                    break
                            try:
                                line_item = EngNumber(line_item)
                            except decimal.InvalidOperation:
                                console.print(f"[red]Cannot convert {line_item} to Engineering Number in col {column_i} line {line_i+1}[/]")
                                continue
                        line_item = line_type(line_item)
                    except ValueError:
                        console.print(f"[red]Cannot convert {line_item} to {line_type}[/]")
                        continue

                    new_part[curr_column_key] = line_item
                new_parts.append(new_part)
        except KeyboardInterrupt:
            console.print("[red]Exited[/]")
            return

    console.print(f"The imported parts:")
    rich.pretty.pprint(new_parts)
    if questionary.confirm("Would you like to add these parts", default=False).ask() is not True:
        console.print("Understood, not adding parts")
        return

    for part in new_parts:
        # todo: add error if unable to add
        try:
            db.add_new_part(part['type'], part)
        except e7epd.InputException:
            log.exception(f"Unable to add part {part}")

def get_db(c: CLIConfig) -> Optional[pymongo.database.Database]:
    db_conn = None

    # Check if we have any database to connect to. If the connection is successful, return the DB
    if not c.is_any_db_config_stored():
        console.print("Oh no, no database is configured. Let's get that settled")
        ret = ask_and_save_new_db_config(c)
        if ret is None:
            console.print("No database given or connection failed. Exiting")
            return None
        db_name, db_conn = ret
        return db_conn

    # Check if we previously selected a database, otherwise ask the user for it
    db_name = c.get_selected_database()
    if not c.is_db_valid(db_name):
        db_name = questionary.select(
            "A database was not selected last time. Please select which database to connect to",
            choices=c.get_stored_db_names()).ask()
        if db_name is None:
            console.print("No database is selected to communicate to. Please restart and select something")
            return None

    while db_conn is None:
        try:
            db_conn = c.get_database_connection(db_name)
            break
        # If we are not able to connect to the database for any reason!
        except c.DatabaseConnectionException:
            console.print("Unable to connect to database, please select what to try again")
            db_name = questionary.select(
                "A database was not selected last time. Please select which database to connect to",
                choices=c.get_stored_db_names()).ask()
            if db_name is None:
                console.print("No database is selected to communicate to. Please restart and select something")
                return None
        # if we are still running an MySQL server, which has been deprecated!
        except c.DatabaseDeprecatedException as e:
            from e7epd import migration

            if not migration.old_sql_available:
                console.print("The migration tool cannot import sqlachemy. Run this with -v to see detailed logs")
                return None
            if questionary.confirm("Database is too old, add mongoDb server?").ask() is not True:
                console.print("Exiting")
                return None
            old_sql_name = c.config.last_db
            console.print("Enter the new MongoDB Connection")
            ret = ask_and_save_new_db_config(c)
            if ret is None:
                console.print("No database given or unable to connect to new one. Exiting")
                return None
            new_db_name, new_db_conn = ret

            if questionary.confirm("Want to migrate old data from the sql to mongo db?").ask():
                try:
                    migration.update_06_to_07(new_db_conn, e.args[1])
                except Exception as e:
                    logging.exception("Error then importing")
                    console.print("Other exception happened :(. See logs above")
                    c.delete_database(new_db_name)
                    continue
                console.print("Done with migration :)")
            c.delete_database(old_sql_name)  # delete old sql db from name
            c.config.last_db = new_db_name
            c.save()

            return new_db_conn

    return db_conn

def setup_logger(is_debug: int):
    l = logging.getLogger()
    l.setLevel(logging.DEBUG)

    rich_handler = RichHandler()
    rich_handler.setFormatter(logging.Formatter('%(name)s: %(message)s'))
    if is_debug != 0:
        rich_handler.setLevel(logging.DEBUG)
    else:
        rich_handler.setLevel(logging.INFO)

    if is_debug <= 1:
        logging.getLogger('pymongo').setLevel(logging.INFO)

    sys_log = logging.handlers.SysLogHandler()
    sys_log.setLevel(logging.DEBUG)

    l.addHandler(rich_handler)
    l.addHandler(sys_log)


def main():
    parser = argparse.ArgumentParser(description='E7EPD CLI Application')
    parser.add_argument('-v', '--verbose', action='count', help='Enable verbose mode', default=0)
    parser.add_argument('--import_csv', help='Run the importer utility with the given CSV (not fully functional)', default=None)
    parser.add_argument('--export', action='store_true', help='Exports data in a csv or json format (not functional)', default=None)
    parser.add_argument('--import_order', action='store_true', help='Utility to import a order from a csv, optionally prints it to barcodes', default=None)
    parser.add_argument('--mock_db', action='store_true', help='Setup to use a fake database for testing purposes', default=None)
    args = parser.parse_args()

    setup_logger(args.verbose)

    c = CLIConfig()

    if args.mock_db:
        console.print("Using fake database for testing")
        db_conn = e7epd.test.MockDB()
    else:
        db_conn = get_db(c)
        if db_conn is None:
            return

    # force the typechecker to be happy, as MockDB has valid signatures
    db_conn: pymongo.database.Database

    assert db_conn is not None

    if args.import_csv is not None:
        importer_app(c, db_conn, args.import_csv)
        return

    c = CLI(config=c, database_connection=db_conn)

    if args.import_order:
        import_order_csv(c)
        return

    c.main()


if __name__ == "__main__":
    main()
