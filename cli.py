#!/usr/bin/python3

import e7epd
import logging
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
import pathlib
import os
import sys
import typing
import json
import sqlalchemy
import sqlalchemy.future

l = logging.getLogger()
l.setLevel(logging.WARNING)
l.addHandler(RichHandler())

console = rich.console.Console(style="blue")


class CLIConfig:
    class NoDatabaseException(Exception):
        def __init__(self):
            super().__init__("No Database")

    class NoLastDBSelectionException(Exception):
        def __init__(self):
            super().__init__("There isn't a last selected database")

    def __init__(self):
        self.file_path = os.path.dirname(os.path.abspath(__file__)) + '/cli_config.json'
        self.config = {}
        if os.path.isfile(self.file_path):
            with open(self.file_path) as f:
                self.config = json.load(f)

    def save(self):
        with open(self.file_path, 'w') as f:
            json.dump(self.config, f)

    def get_database_connection(self, database_name: str = None) -> sqlalchemy.future.Engine:
        if 'db_list' not in self.config:
            raise self.NoDatabaseException()
        if len(self.config['db_list']) == 0:
            raise self.NoDatabaseException()
        if database_name is None:
            if 'last_db' not in self.config:
                raise self.NoLastDBSelectionException()
            database_name = self.config['last_db']
        if database_name not in self.config['db_list']:
            raise self.NoLastDBSelectionException()

        self.config['last_db'] = database_name
        if self.config['db_list'][database_name]['type'] == 'local':
            return sqlalchemy.create_engine("sqlite:///{}".format(self.config['db_list'][database_name]['filename']))
        elif self.config['db_list'][database_name]['type'] == 'mysql_server':
            return sqlalchemy.create_engine("mysql://{}:{}@{}:{}/{}".format(self.config['db_list'][database_name]['username'],
                                                                            self.config['db_list'][database_name]['password'],
                                                                            self.config['db_list'][database_name]['db_host'], 3306,
                                                                            self.config['db_list'][database_name]['db_name']))

    def get_stored_db_names(self) -> list:
        if 'db_list' not in self.config:
            raise self.NoDatabaseException()
        if len(self.config['db_list']) == 0:
            raise self.NoDatabaseException()
        return self.config['db_list'].keys()

    def get_selected_database(self) -> str:
        return self.config['last_db']

    def set_last_db(self, database_name: str):
        self.config['last_db'] = database_name

    def save_database_as_sqlite(self, database_name: str, file_name: str):
        if '.db' not in file_name:
            raise UserWarning("No .db externsion in filename")
        if 'db_list' not in self.config:
            self.config['db_list'] = {}
        if database_name not in self.config['db_list']:
            self.config['db_list'][database_name] = {}
        self.config['db_list'][database_name]['type'] = 'local'
        self.config['db_list'][database_name]['filename'] = file_name
        self.save()

    def save_database_as_mysql(self, database_name: str, username: str, password: str, db_name: str, host: str):
        if 'db_list' not in self.config:
            self.config['db_list'] = {}
        if database_name not in self.config['db_list']:
            self.config['db_list'][database_name] = {}
        self.config['db_list'][database_name]['type'] = 'mysql_server'
        self.config['db_list'][database_name]['username'] = username
        self.config['db_list'][database_name]['password'] = password
        self.config['db_list'][database_name]['db_name'] = db_name
        self.config['db_list'][database_name]['db_host'] = host
        self.save()


class CLI:
    cli_revision = '0.3'

    class _HelperFunctionExitError(Exception):
        pass

    def __init__(self, config: CLIConfig, database_connection: sqlalchemy.future.Engine):
        self.db = e7epd.E7EPD(database_connection)
        self.conf = config

        self.return_formatted_choice = questionary.Choice(title=prompt_toolkit.formatted_text.FormattedText([('red green', 'Return')]))

    @staticmethod
    def find_spec_by_db_name(spec_list: list, db_name: str) -> dict:
        """
            Helper function that returns a database specification by the db_name attribute
            :param spec_list: The specification list
            :param db_name: The database name
            :return: The specification that has db_name equal to the argument
        """
        for spec in spec_list:
            if spec['db_name'] == db_name:
                return spec

    def _ask_manufacturer_part_number(self, part_db: e7epd.E7EPD.GenericPart, must_exit: typing.Union[None, bool] = None) -> str:
        # Get a list of manufacturer part number to use as type hinting
        if must_exit is True:
            try:
                mfr_list = part_db.get_all_mfr_part_numb_in_db()
            except e7epd.EmptyInDatabase:
                console.print("[red]No parts found in database[/]")
                raise self._HelperFunctionExitError()
            mfr_part_numb = questionary.autocomplete("Enter the manufacturer part number: ", choices=mfr_list).ask()
        else:
            mfr_part_numb = questionary.text("Enter the manufacturer part number: ").ask()
        if mfr_part_numb == '' or mfr_part_numb is None:
            console.print("[red]Must have a manufacturer part number[/]")
            raise self._HelperFunctionExitError()
        if must_exit is not None:
            exist_in_db = part_db.check_if_already_in_db_by_manuf(mfr_part_numb)
            if (must_exit and exist_in_db is None) or (not must_exit and exist_in_db is not None):
                console.print("[red]Part must already exist in the database[/]")
                raise self._HelperFunctionExitError()
        return mfr_part_numb.upper()

    def print_parts_list(self, part_db: e7epd.E7EPD.GenericPart, parts_list: list[e7epd.spec.GenericItem], title):
        """ Function is called when the user wants to print out all parts """
        ta = rich.table.Table(title=title)
        for spec_db_name in part_db.table_item_display_order:
            ta.add_column(self.find_spec_by_db_name(part_db.table_item_spec, spec_db_name)['showcase_name'])
        for part in parts_list:
            row = []
            for spec_db_name in part_db.table_item_display_order:
                to_display = part[spec_db_name]
                display_as = self.find_spec_by_db_name(part_db.table_item_spec, spec_db_name)['shows_as']
                if display_as == 'engineering':
                    to_display = str(EngNumber(to_display))
                elif display_as == 'percentage':
                    to_display = str(to_display) + "%"
                else:
                    to_display = str(to_display)
                row.append(to_display)
            ta.add_row(*row)
        console.print(ta)

    def print_all_parts(self, part_db: e7epd.E7EPD.GenericPart):
        parts_list = part_db.get_all_parts()
        self.print_parts_list(part_db, parts_list, title="All parts in %s" % part_db.table_name)

    @staticmethod
    def ask_for_spec_input(spec: dict, choices: list = None) -> str:
        while 1:
            if choices:
                inp = questionary.autocomplete("Enter value for %s: " % spec['showcase_name'], choices=choices).ask()
            else:
                inp = questionary.text("Enter value for %s: " % spec['showcase_name']).ask()
            if inp is None:
                raise KeyboardInterrupt()
            if inp == '':
                if spec['required'] is True:
                    console.print("You must enter this spec as it's required")
                    continue
                else:
                    inp = None

            if inp is not None:
                # Remove leading and trailing whitespace
                inp = inp.strip()
                if spec['shows_as'] == 'engineering':
                    try:
                        inp = EngNumber(inp)
                    except decimal.InvalidOperation:
                        console.print("Invalid engineering number")
                        continue
                elif spec['shows_as'] == 'percentage':
                    if '%' in inp:
                        inp = inp.replace('%', '')
                elif '/' in inp:
                    inp = inp.split('/')
                    inp = float(inp[0]) / float(inp[1])

                if "INT" in spec['db_type']:
                    inp = int(inp)
                elif "FLOAT" in spec['db_type']:
                    inp = float(inp)
            break
        return inp

    @staticmethod
    def get_autocomplete_list(db_name: str, table_name: str) -> typing.Union[None, list]:
        autocomplete_choices = None
        if db_name == 'manufacturer' and table_name == 'ic':
            autocomplete_choices = e7epd.spec.autofill_helpers_list['ic_manufacturers']
        elif db_name == 'ic_type' and table_name == 'ic':
            autocomplete_choices = e7epd.spec.autofill_helpers_list['ic_types']
        elif db_name == 'cap_type' and table_name == 'capacitor':
            autocomplete_choices = e7epd.spec.autofill_helpers_list['capacitor_types']
        elif db_name == 'diode_type' and table_name == 'diode':
            autocomplete_choices = e7epd.spec.autofill_helpers_list['diode_type']
        return autocomplete_choices

    def print_filtered_parts(self, part_db: e7epd.E7EPD.GenericPart):
        choices = [questionary.Choice(title=d['showcase_name'], value=d) for d in part_db.table_item_spec]
        specs_selected = questionary.checkbox("Select what parameters do you want to search by: ", choices=choices).ask()
        if specs_selected is None:
            return
        if len(specs_selected) == 0:
            console.print("[red]Must choose something[/]")
            return
        part_filter = part_db.part_type()
        for spec in specs_selected:
            autocomplete_choices = self.get_autocomplete_list(spec['db_name'], part_db.table_name)
            try:
                inp = self.ask_for_spec_input(spec, autocomplete_choices)
            except KeyboardInterrupt:
                console.print("Canceled part lookup")
                return
            part_filter[spec['db_name']] = inp
        print(part_filter)
        try:
            parts_list = part_db.get_sorted_parts(part_filter)
        except e7epd.EmptyInDatabase:
            console.print("[red]No filtered parts in the database[/]")
            return
        self.print_parts_list(part_db, parts_list, title="All parts in %s" % part_db.table_name)

    def add_new_part(self, part_db: e7epd.E7EPD.GenericPart):
        """ Function gets called when a part is to be added """
        try:
            try:
                mfr_part_numb = self._ask_manufacturer_part_number(part_db, must_exit=False)
            except self._HelperFunctionExitError:
                return
            new_part = part_db.part_type(mfr_part_numb=mfr_part_numb)
            for spec_db_name in part_db.table_item_display_order:
                # Skip over the manufacturer part number as we already have that
                if spec_db_name == 'mfr_part_numb':
                    continue
                # Select an autocomplete choice, or None if there isn't any
                autocomplete_choices = self.get_autocomplete_list(spec_db_name, part_db.table_name)
                # Get the spec
                spec = self.find_spec_by_db_name(part_db.table_item_spec, spec_db_name)
                if spec is None:
                    console.print("[red]INTERNAL ERROR: Got None when finding the spec for database name %s[/]" % spec_db_name)
                    return
                # Ask the suer for that property
                try:
                    new_part[spec_db_name] = self.ask_for_spec_input(spec, autocomplete_choices)
                except KeyboardInterrupt:
                    console.print("Did not add part")
                    return
            part_db.create_part(new_part)
            self.db.save()
        except KeyboardInterrupt:
            console.print("\nOk, no part is added")
            return

    def delete_part(self, part_db: e7epd.E7EPD.GenericPart):
        """ This gets called when a part is to be deleted """
        try:
            mfr_part_numb = self._ask_manufacturer_part_number(part_db, must_exit=True)
        except self._HelperFunctionExitError:
            return
        try:
            part_db.delete_part_by_mfr_number(mfr_part_numb)
        except e7epd.EmptyInDatabase:
            console.print("[red]The manufacturer is not in the database[/]")

    def add_stock_to_part(self, part_db: e7epd.E7EPD.GenericPart):
        try:
            # Ask for manufacturer part number first, and make sure there are no conflicts
            try:
                mfr_part_numb = self._ask_manufacturer_part_number(part_db, must_exit=True)
            except self._HelperFunctionExitError:
                return
            while 1:
                add_by = questionary.text("Enter how much you want to add this part by: ").ask()
                try:
                    add_by = int(add_by)
                except ValueError:
                    console.print("Must be an integer")
                    continue
                break
            part_db.append_stock_by_manufacturer_part_number(mfr_part_numb=mfr_part_numb, append_by=add_by)
            console.print('[green]Add to your stock :)[/]')
        except KeyboardInterrupt:
            console.print("\nOk, no stock is changed")
            return

    def remove_stock_from_part(self, part_db: e7epd.E7EPD.GenericPart):
        try:
            # Ask for manufacturer part number first, and make sure there are no conflicts
            try:
                mfr_part_numb = self._ask_manufacturer_part_number(part_db, must_exit=True)
            except self._HelperFunctionExitError:
                return
            while 1:
                remove_by = questionary.text("Enter how much you want to add this part by: ").ask()
                try:
                    remove_by = int(remove_by)
                except ValueError:
                    console.print("Must be an integer")
                    continue
                break
            try:
                part_db.remove_stock_by_manufacturer_part_number(mfr_part_numb=mfr_part_numb, remove_by=remove_by)
            except e7epd.NegativeStock as e_v:
                console.print("[red]Stock will go to negative[/]")
                console.print("[red]If you want to make the stock zero, restart this operation and remove {:d} parts instead[/]".format(e_v.amount_to_make_zero))
            else:
                console.print('[green]Removed to your stock :)[/]')
        except KeyboardInterrupt:
            console.print("\nOk, no stock is changed")
            return

    def component_cli(self, part_db: e7epd.E7EPD.GenericPart):
        """ The CLI handler for components """
        while 1:
            to_do = questionary.select("What do you want to do in this component database? ", choices=["Print parts in DB", "Append Stock", "Remove Stock", "Add Part", "Delete Part", self.return_formatted_choice]).ask()
            if to_do is None:
                raise KeyboardInterrupt()
            if to_do == "Return":
                break
            elif to_do == "Print parts in DB":
                if part_db.is_database_empty():
                    console.print("[italic red]Sorry, but there are no parts for that component[/]")
                    continue
                all_parts = questionary.confirm("Do you want to filter the parts beforehand?", default=False, auto_enter=False).ask()
                if all_parts:
                    self.print_filtered_parts(part_db)
                else:
                    self.print_all_parts(part_db)
            elif to_do == "Add Part":
                self.add_new_part(part_db)
            elif to_do == "Delete Part":
                self.delete_part(part_db)
            elif to_do == "Append Stock":
                self.add_stock_to_part(part_db)
            elif to_do == "Remove Stock":
                self.remove_stock_from_part(part_db)

    def choose_component(self):
        while 1:
            component = questionary.select("Select the component you want do things with:", choices=list(self.db.components.keys()) + [self.return_formatted_choice]).ask()
            if component is None:
                raise KeyboardInterrupt()
            elif component == 'Return':
                break

            part_db = self.db.components[component]
            self.component_cli(part_db)

    def wipe_database(self):
        do_delete = questionary.confirm("ARE YOYU SURE???", auto_enter=False).ask()
        if do_delete is True:
            do_delete = questionary.confirm("ARE YOYU SURE...AGAIN???", auto_enter=False).ask()
            if do_delete is True:
                console.print("Don't regret this!!!")
                self.db.wipe_database()
                return
        if do_delete is not True:
            console.print("Did not delete the database")
            return

    def database_settings(self):
        while 1:
            console.print("Current selected database is: %s" % self.conf.get_selected_database())
            to_do = questionary.select("What do you want to? ", choices=["Add Database", "Select another database", self.return_formatted_choice]).ask()
            if to_do is None:
                break
            if to_do == "Return":
                break
            elif to_do == "Add Database":
                try:
                    ask_for_database(self.conf)
                except KeyboardInterrupt:
                    console.print("Did not add a new database")
                    continue
                console.print("Sucessfully added the new database")
            elif to_do == "Select another database":
                db_name = questionary.select("Select the new database to connect to:", choices=self.conf.get_stored_db_names()).ask()
                if db_name is None:
                    console.print("Nothing new was selected")
                    continue
                self.conf.set_last_db(db_name)
                console.print("Selected the database %s" % db_name)
                console.print("[red]Please restart software for it to take into effect[/]")
                raise KeyboardInterrupt()

    def main(self):
        # Check DB version before doing anything
        if not self.db.is_latest_database():
            do_update = questionary.confirm("Database is not at the latest version. Updrade?", auto_enter=False).ask()
            if do_update:
                self.db.update_database()
            else:
                console.print("[red]You chose to not update the database, thus this CLI application is not usable[/]")
                return
        console.print(rich.panel.Panel("[bold]Welcome to the E707PD[/bold]\nDatabase Spec Revision {}, Backend Revision {}, CLI Revision {}\nSelected database {}".format(self.db.config.get_db_version(), e7epd.__version__, self.cli_revision, self.conf.get_selected_database()), title_align='center'))
        try:
            while 1:
                to_do = questionary.select("Select the component you want do things with:", choices=['Components', 'Wipe Database', 'Database Setting', 'Exit']).ask()
                if to_do is None:
                    raise KeyboardInterrupt()
                elif to_do == 'Exit':
                    break
                elif to_do == 'Components':
                    self.choose_component()
                elif to_do == 'Wipe Database':
                    self.wipe_database()
                elif to_do == 'Database Setting':
                    self.database_settings()

        except KeyboardInterrupt:
            pass
        finally:
            console.print("\nGood night!")
            self.db.close()
            self.conf.save()


def ask_for_database(config: CLIConfig):
    console.print("Oh no, no database is configured. Let's get that settled")
    db_id_name = questionary.text("What do you want to call this database").unsafe_ask()
    is_server = questionary.select("Do you want the database to be a local file or is there a server running?", choices=['mySQL', 'SQlite']).unsafe_ask()
    if is_server == 'mySQL':
        host = questionary.text("What is the database host?").unsafe_ask()
        db_name = questionary.text("What is the database name").unsafe_ask()
        username = questionary.text("What is the database username?").unsafe_ask()
        password = questionary.password("What is the database password?").unsafe_ask()
        config.save_database_as_mysql(database_name=db_id_name, username=username, db_name=db_name, password=password, host=host)
    elif is_server == 'SQlite':
        file_name = questionary.text("Please enter the name of the server database file you want to be created").unsafe_ask()
        config.save_database_as_sqlite(db_id_name, file_name)
        if '.db' not in file_name:
            file_name += '.db'
        config.save_database_as_sqlite(db_id_name, file_name)


if __name__ == "__main__":
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

    c = CLI(config=c, database_connection=db_conn)
    c.main()
