#!/usr/bin/python3
"""
    E707PD Python CLI Application
    Rev 0.7
"""
import dataclasses
# External Modules Import
import subprocess
import logging
import logging.handlers
import importlib
import rich
import rich.console
import rich.panel
import rich.pretty
from rich.prompt import Prompt
from rich.logging import RichHandler
import rich.table
import decimal
from engineering_notation import EngNumber
import questionary
import prompt_toolkit
import prompt_toolkit.formatted_text
from prompt_toolkit.formatted_text import to_formatted_text, HTML
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
import tempfile
# Local Modules Import
import e7epd
from e7epd.e707pd_spec import ShowAsEnum
import e7epd.label_making

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

    class DatabaseDeprecatedException(Exception):
        pass

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
        """
        Gets a database connection based off the database name.

        Args:
            database_name: The database name (internal name) to get a connection to
        """
        # todo: add JSON file compatibility
        if database_name is None:
            database_name = self.config.last_db
            if database_name is None:
                raise self.NoLastDBSelectionException()
        if database_name not in self.config.db_list:
            raise self.NoLastDBSelectionException()

        db_conf = self.config.db_list[database_name]

        self.config.last_db = database_name

        return self.get_database_client(db_conf)

    def get_database_client(self, db_conf: dict):
        """
        This function just returns the client, without any of the config checking.

        Args:
            db_conf: The database config dictionary
        """
        if db_conf['type'] in ['local', 'mysql_server', 'postgress_server']:
            raise self.DatabaseDeprecatedException("Not supported, deprecated in 0.7.0", db_conf)
        elif db_conf['type'] == 'mongodb':
            # todo: enable socket connection
            ssl_on = db_conf['ssl']
            if db_conf['auth']:
                conn_str = f"mongodb://{db_conf['username']}:{db_conf['password']}@{db_conf['db_host']}:27017/"
            else:
                conn_str = f"mongodb://{db_conf['db_host']}:27017/"
            conn = pymongo.MongoClient(conn_str, serverSelectionTimeoutMS=1000*2, tls=ssl_on)
            try:
                # The ping command is cheap and does not require auth.
                conn.admin.command('ping')
            except pymongo.errors.ConnectionFailure:
                self.log.exception("ConnectionFailure going to database")
                raise self.DatabaseConnectionException()
            except pymongo.errors.OperationFailure:
                self.log.exception("OperationFailure going to database")
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

    def save_database_as_mongo(self, database_name: str, username: str, password: str, host: str, authenticated: bool = False, ssl: bool = False):
        """
        Saves a database info as a Mongo
        Args:
            database_name: The database name (internal id)
            username: The db username
            password: The db password
            host: The db host
            authenticated: Whether the server needs authentication or not
            ssl: Whether the connection will have ssl/tls enabled
        """
        self._save_database_generic(database_name, username, password, host)
        self.config.db_list[database_name]['type'] = 'mongodb'
        self.config.db_list[database_name]['auth'] = authenticated
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

    class _ChooseComponentDigikeyBarcode(Exception):
        def __init__(self, mfg_part_number: str, dk_info: dict):
            self.mfg_part_number = mfg_part_number
            self.dk_info = dk_info
            super().__init__()

    def __init__(self, config: CLIConfig, database_connection: pymongo.MongoClient):
        self.db = e7epd.E7EPD(database_connection)
        self.conf = config

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
        Asks for the IPN. This function handles type hinting with a given list, checking if the ipn
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
        """ This function mainly exists in order to handle having the mfg part number be a copy of the ipn"""
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
        all_ipn_parts = self.db.get_all_parts_by_keys(None, ret_key=['ipn', 'type'])
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
                try:
                    ipn = self._ask_ipn([i['ipn'] for i in all_ipn_parts], True)
                except self._HelperFunctionExitError:
                    console.print("[red]IPN must not exist in database[/]")
                    continue
                new_part['part']['ipn'] = ipn
                new_part['type'] = [i['type'] for i in all_ipn_parts if i['ipn'] == ipn][0]
            elif specific_part == "Generic":
                try:
                    part_type = self.choose_component()
                except KeyboardInterrupt:
                    console.print("[red]IPN must not exist in database[/]")
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
                new_part['qty'] = int(questionary.text("Enter quantity of this part used on this PCB:").ask())
            except ValueError:
                console.print("[red]Invalid quantity[/]")
                continue
            new_part['designator'] = questionary.text("Enter the designator/reference:").ask()
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
        """ Prints all parts in the database per given type """
        parts_list = self.db.get_all_parts(part_type)
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
                try:
                    inp = self._ask_ipn(self.db.get_all_parts_by_keys(part_type, 'ipn'))
                except self._HelperFunctionExitError:
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
            search_filter.append(e7epd.SpecWithOperator(key=s, val=inp, operator=op))
        try:
            parts_list = self.db.get_sorted_parts(part_type, search_filter)
        except e7epd.EmptyInDatabase:
            console.print("[red]No filtered parts in the database[/]")
            return
        self.print_parts_list(part_type, parts_list, title="All parts in %s" % part_type.showcase_name)

    def print_parts(self, part_type: e7epd.spec.PartSpec = None):
        if part_type is None:
            try:
                part_type = self.choose_component()
            except KeyboardInterrupt:
                console.print("[red]No part chosen[/]")
                return
        if self.db.get_number_of_parts_in_db(part_type) == 0:
            console.print("[italic red]Sorry, but there are no parts for that component[/]")
            return
        all_parts = questionary.confirm("Do you want to filter the parts beforehand?", default=False, auto_enter=True).ask(patch_stdout=False, kbi_msg="Exited option")
        if all_parts is None:
            return
        if all_parts:
            self.print_filtered_parts(part_type)
        else:
            self.print_all_parts(part_type)

    def ask_for_spec_input_with_operator(self, spec: e7epd.spec.SpecLineItem, choices: list = None,
                                         operator_allowed: bool = True) -> (typing.Union[str, float, int], e7epd.ComparisonOperators):
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
        # todo: this
        # if spec['input_type'] == 'parts_json':  # We are handling adding a part, which is seperate from a value
        #     try:
        #         inp = self._ask_for_pcb_parts()
        #     except self._HelperFunctionExitError:
        #         raise KeyboardInterrupt()
        #     return inp
        op = e7epd.ComparisonOperators('==')
        while 1:
            # todo: do we need the following case handling below??
            # if spec_name == 'ipn':
            #     try:
            #         inp = self._ask_ipn(self.db.get_all_parts_one_keys(part_type, 'ipn'))
            #     except self._HelperFunctionExitError:
            #         raise KeyboardInterrupt()
            # else:
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
                        op = e7epd.ComparisonOperators(op)
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

    def ask_for_spec_input(self, spec: e7epd.spec.SpecLineItem, choices: list = None):
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

    def get_partdb_and_ipn(self, part_db: e7epd.spec.PartSpec = None, ipn_must_exist: bool = None):
        """
        Helper function to get the manufacturer part number and component database
        Args:
            part_db: The selected component database. If not given, this function will return one depending on the
                     manufacturer part number
            ipn_must_exist: Whether the manufacturer part number must already exist in the database

        Returns: A tuple of a selected component database and the manufacturer part number
        """
        if part_db is None:
            all_ipn_list = self.db.get_all_parts_by_keys(None, 'ipn')
        else:
            all_ipn_list = self.db.get_all_parts_by_keys(part_db, 'ipn')

        try:
            ipn_number = self._ask_ipn(all_ipn_list, must_already_exist=ipn_must_exist)
        except self._HelperFunctionExitError:
            raise self._HelperFunctionExitError()

        if part_db is None:
            t = self.db.get_part_by_ipn(ipn_number)['type']
            part_db = self.db.get_part_spec_by_db_name(t)

        return part_db, ipn_number

    def add_new_pcb(self):
        new_pcb = {}
        for spec_db_name in e7epd.spec.PCBItems:
            if spec_db_name == 'parts':
                new_pcb['parts'] = self._ask_for_pcb_parts()
            else:
                try:  # Ask the user for that property
                    new_pcb[spec_db_name] = self.ask_for_spec_input(e7epd.spec.PCBItems[spec_db_name])
                except KeyboardInterrupt:
                    console.print("Did not add part")
                    return
        self.db.add_new_pcb(new_pcb)

    def add_new_part(self, part_type: e7epd.spec.PartSpec = None):
        """ Function gets called when a part is to be added """
        try:
            if part_type is None:
                part_type = self.choose_component(True)
            if part_type == e7epd.spec.PCBItems:
                console.print("Adding PCB instead")
                self.add_new_pcb()
                return
            try:
                ipn = self._ask_ipn(self.db.get_all_parts_by_keys(part_type, 'ipn'), must_already_exist=False)
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
                    autocomplete_choices = self.db.get_autocomplete_list(part_type, spec_db_name)
                    try:        # Ask the user for that property
                        new_part[spec_db_name] = self.ask_for_spec_input(part_type.items[spec_db_name], autocomplete_choices)
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
                    new_val = self.ask_for_spec_input(part_db.items[to_change], self.get_autocomplete_list(to_change, part_db.db_type_name))
                    to_update[to_change] = new_val
                    component[to_change] = new_val
                except KeyboardInterrupt:
                    console.print("Did not change spec")
                    continue
        except KeyboardInterrupt:
            console.print("Did not change part")
            return

    def print_pcb_and_component_availability(self):
        all_boards = self.db.get_all_unique_pcbs()
        if len(all_boards) == 0:
            console.print("There are no PCBs in the database")
            return
        all_boards = {f"{i['id']} Rev {i['rev']}": (i['id'], i['rev']) for i in all_boards}
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
            if len(parts) == 0:
                all_parts_in_board.append(([str(board_part['qty']), board_part['designator'], '-', '-', '-', '-', '-'], 'red'))
            elif len(parts) == 1:
                part = parts[0]
                all_parts_in_board.append(([str(board_part['qty']), board_part['designator'], '-', part['type'], part['ipn'], f"{part['stock']:d}", part['storage']], None))
            else:
                for part in parts:
                    all_parts_in_board.append(([str(board_part['qty']), board_part['designator'], '-', part['type'], part['ipn'], f"{part['stock']:d}", part['storage']], 'orange'))

        console.print("You currently have {:d} PCBs available".format(board['stock']))

        ta = rich.table.Table(title='All components for {} Rev {}'.format(board['board name'], board['rev']))
        ta.add_column("Stock Required")
        ta.add_column("Reference")
        ta.add_column("Description")
        ta.add_column("Component Type")
        ta.add_column("Available IPN#")
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

    def choose_component(self, allow_pcb: bool = False) -> typing.Union[e7epd.spec.PartSpec, dict]:
        """
        Dialog to choose which component to use.
        Returns: The component class
        Raises KeyboardInterrupt: If a component is not chosen
        """
        choice = [questionary.Choice(title=i.showcase_name, value=i) for i in self.db.comp_types] + [self.return_formatted_choice]
        if allow_pcb:
            pcb_choice = questionary.Choice(title=prompt_toolkit.formatted_text.FormattedText([('purple', 'PCBs')]))
            choice.insert(-1, pcb_choice)
        component = questionary.select("Select the component you want do things with:", choices=choice).ask()
        if component is None or component == 'Return':
            raise KeyboardInterrupt()
        elif component == 'PCBs':
            part_db = e7epd.spec.PCBItems
        else:
            part_db = component
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
                if t['type'] == 'mongodb':
                    # todo: special print if auth is not enable or not
                    console.print("This is a Mongo server, where:\nUsername: {username}\nDatabase Host: {db_host}\nDatabase Name: {db_name}".format(**t, db_name=db_name))

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
        console.print(rich.panel.Panel("[bold]Welcome to the E707PD[/bold]\n"
                                       "Database Spec Revision {}, Backend Revision {}, CLI Revision {}\n"
                                       "Selected database {}".format(self.db.config.get_db_version(), e7epd.__version__, self.cli_revision, self.conf.get_selected_database()), title_align='center'))
        try:
            while 1:
                to_do = questionary.select("Select the component you want do things with:",
                                           choices=['Check components for PCB', 'Search Part', 'Add new part', 'Add new stock', 'Remove stock', 'Edit part',
                                                    'Database Setting', 'Digikey API Settings', 'Exit'], use_shortcuts=True).ask()
                if to_do is None:
                    raise KeyboardInterrupt()
                elif to_do == 'Exit':
                    break
                elif to_do == 'Check components for PCB':
                    self.print_pcb_and_component_availability()
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
                # todo: This was here when the parts were in physically separate tables. Might no longer make sense?
                # elif to_do == 'Individual Components View':
                #     while 1:
                #         try:
                #             part_db = self.choose_component()
                #             self.component_cli(part_db)
                #         except KeyboardInterrupt:
                #             break
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
    db_id_name = questionary.text("What do you want to call this database").unsafe_ask()
    is_server = questionary.select("Do you want the database to be a local file or is there a server running?", choices=['mongoDb']).unsafe_ask()
    if is_server == 'mongoDb':
        host = questionary.text("What is the database host?").unsafe_ask()
        ssl = questionary.confirm("Will the server be connected with SSL/TSL?", auto_enter=False, default=False).unsafe_ask()
        username = questionary.text("What is the database username (Enter nothing for un-auth)?").unsafe_ask()
        if username == '':
            password = ''
            is_auth = False
        else:
            password = questionary.password("What is the database password?").unsafe_ask()
            is_auth = True
        config.save_database_as_mongo(database_name=db_id_name, username=username, password=password, host=host, authenticated=is_auth, ssl=ssl)
        # try and get the database
        try:
            c = config.config.db_list[db_id_name]
            config.get_database_client(c)
        except config.DatabaseConnectionException:
            console.print("Failed with new database...removing it")
            config.delete_database(db_id_name)
            raise KeyboardInterrupt()       # for now, can be improved later!
    return db_id_name

def exporter_app(conf: CLIConfig, database_connection: pymongo.MongoClient):
    def isfloat(num):
        try:
            float(num)
            return True
        except ValueError:
            return False

    log = logging.getLogger('importer_app')

    to_do = questionary.select("What export function you want?",
                               choices=['Export to CSV', 'Print IPN Barcode', 'Exit'], use_shortcuts=True).ask()
    if to_do is None or to_do == 'Exit':
        console.print("Exiting!")
        return

    db = e7epd.E7EPD(database_connection)

    if to_do == 'Print IPN Barcode':
        width = questionary.text("What is the tape size in mm", validate=isfloat).ask()
        if width is None or width == "":
            return
        width = float(width)
        # todo: add default path
        export = questionary.path("Select the export path").ask()
        if export is None or export == "":
            return

        choice = [questionary.Choice(title=prompt_toolkit.formatted_text.FormattedText([('blue', 'All')]))] + \
                 [questionary.Choice(title=i.showcase_name, value=i) for i in db.comp_types] + \
                 [questionary.Choice(title=prompt_toolkit.formatted_text.FormattedText([('green', 'Return')]))]
        component = questionary.select("Select the component you want do things with:", choices=choice).ask()
        if component is None or component == 'Return':
            return
        elif component == 'All':
            part_db = None
        else:
            part_db = component
        ipn_list = db.get_all_parts_by_keys(part_db, 'ipn')
        e7epd.label_making.export_barcodes(ipn_list, width, export)
    else:
        console.print("Not implemented ")


def importer_app(conf: CLIConfig, database_connection: pymongo.MongoClient, import_file: str):
    """
    An importer sub-application that imports an existing "database" from a CSV file

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
                    choices += [questionary.Choice(title=prompt_toolkit.formatted_text.FormattedText([('blue', 'Part Type (Required)')]), value='type')]
                choices += [questionary.Choice(title=prompt_toolkit.formatted_text.FormattedText([('orange', 'None/Other')]), value='None')]
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
            line = line.strip().split(',')
            if len(header) != len(line):
                console.print(f"[red]Line {line_i} is not the same length as the header. Exiting[/]")
                return
            line_item = line[type_col]
            if line_item not in csv_type_to_internal_type:
                pt = questionary.select(f"What is the part type for string '{line_item}'?", choices=part_type_choice).unsafe_ask()
                csv_type_to_internal_type[line_item] = pt
                column_to_key_parts[pt.db_type_name] = {}
                # ask the user which columns go with part-specific keys
                for i, h in enumerate(header):
                    # if we have the column in the "base part" item mapping, then don't both with the particular column for this
                    if column_to_key[i] is not None:
                        continue
                    choices = [questionary.Choice(title=f"{v.showcase_name} (Required)" if v.required else f"{v.showcase_name}", value=i) for i, v in pt.items.items() if
                               i not in column_to_key.values() and i not in e7epd.spec.BasePartItems.keys()]
                    choices += [questionary.Choice(title=prompt_toolkit.formatted_text.FormattedText([('orange', 'None')]), value='None')]
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
            for line_i, line in enumerate(f):
                new_part = {}
                line = line.strip().split(',')
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

def setup_logger(is_debug: bool = False):
    l = logging.getLogger()
    l.setLevel(logging.DEBUG)

    rich_handler = RichHandler()
    if is_debug:
        rich_handler.setLevel(logging.DEBUG)
    else:
        rich_handler.setLevel(logging.INFO)

    sys_log = logging.handlers.SysLogHandler()
    sys_log.setLevel(logging.DEBUG)

    l.addHandler(rich_handler)
    l.addHandler(sys_log)


def main():
    parser = argparse.ArgumentParser(description='E7EPD CLI Application')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose mode', default=False)
    parser.add_argument('--import_csv', help='Run the importer utility with the given CSV', default=None)
    parser.add_argument('--export', action='store_true', help='Exports data in some what', default=None)
    args = parser.parse_args()

    setup_logger(args.verbose)

    c = CLIConfig()
    db_name = None
    db_conn = None
    while 1:
        try:
            db_conn = c.get_database_connection(db_name)
            break
        # if no database was configured
        except c.NoDatabaseException:
            try:
                console.print("Oh no, no database is configured. Let's get that settled")
                ask_for_database(c)
            except KeyboardInterrupt:
                console.print("No database given. Exiting")
                sys.exit(-1)
        # if there wasn't a default/last database selected
        except c.NoLastDBSelectionException:
            db_name = questionary.select("A database was not selected last time. Please select which database to connect to", choices=c.get_stored_db_names()).ask()
            if db_name is None:
                console.print("No database is selected to communicate to. Please restart and select something")
                sys.exit(-1)
        # if we are still running an MySQL server, which has been deprecated!
        except c.DatabaseDeprecatedException as e:
            from e7epd import migration

            if not migration.old_sql_available:
                console.print("The migration tool cannot import sqlachemy. Run this with -v to see detailed logs")
                sys.exit(-1)
            if questionary.confirm("Database is too old, migrate?").ask() is not True:
                console.print("Exiting")
                sys.exit(-1)
            old_sql_name = c.config.last_db
            console.print("Enter the new MongoDB Connection")
            try:
                new_db = ask_for_database(c)
            except KeyboardInterrupt:
                console.print("No database given. Exiting")
                sys.exit(-1)

            new_db_conn = c.get_database_connection(new_db)
            try:
                migration.update_06_to_07(new_db_conn, e.args[1])
            except Exception as e:
                logging.exception("Error then importing")
                console.print("Other exception happened :(. See logs above")
                c.delete_database(new_db)
                continue
            console.print("Done with migration :)")
            c.delete_database(old_sql_name)     # delete old sql db from name
            continue
        # If we are not able to connect to the database for any reason!
        except c.DatabaseConnectionException:
            console.print("Unable to connect to database")
            sys.exit(-1)

    if args.import_csv is not None:
        importer_app(c, db_conn, args.import_csv)
        return

    if args.export is not None:
        exporter_app(c, db_conn)
        return

    c = CLI(config=c, database_connection=db_conn)
    c.main()


if __name__ == "__main__":
    main()
