#!/usr/bin/python3

import database
import logging
import rich
import rich.console
import rich.panel
from rich.prompt import Prompt
from rich.logging import RichHandler
import rich.table
from engineering_notation import EngNumber
import questionary
import pathlib
import os
import json

l = logging.getLogger()
l.setLevel(logging.WARNING)
l.addHandler(RichHandler())

console = rich.console.Console(style="blue")


class CLIConfig:
    """ Configuration wrapper for potential future use """
    def __init__(self):
        self.file_path = os.path.dirname(os.path.abspath(__file__)) + '/cli_config.json'
        self.config = {}
        if os.path.isfile(self.file_path):
            with open(self.file_path) as f:
                self.config = json.load(f)

    def save(self):
        with open(self.file_path, 'w') as f:
            json.dump(self.config, f)


class CLI:
    def __init__(self):
        self.db = database.EEData()
        self.conf = CLIConfig()

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

    def print_parts_list(self, part_db: database.EEData.GenericPart, parts_list: list[database.GenericItem], title):
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

    def print_all_parts(self, part_db: database.EEData.GenericPart):
        parts_list = part_db.get_all_parts()
        self.print_parts_list(part_db, parts_list, title="All parts in %s" % part_db.table_name)

    @staticmethod
    def ask_for_spec_input(spec: dict) -> str:
        while 1:
            inp = console.input("Enter value for %s: " % spec['showcase_name'])
            if inp == '':
                if spec['required'] is True:
                    console.print("You must enter this spec as it's required")
                    continue
                else:
                    inp = None
            break

        if spec['shows_as'] == 'engineering':
            inp = EngNumber(inp)
        elif spec['shows_as'] == 'percentage':
            if '%' in inp:
                inp = inp.replace('%', '')

        if "INT" in spec['db_type']:
            inp = int(inp)
        elif "FLOAT" in spec['db_type']:
            inp = float(inp)

        return inp

    def print_filtered_parts(self, part_db: database.EEData.GenericPart):
        choices = [questionary.Choice(title=d['showcase_name'], value=d) for d in part_db.table_item_spec]
        specs_selected = questionary.checkbox("Select what parameters do you want to search by: ", choices=choices).ask()
        # TODO: Remove TODO once this is done
        console.print("Sorry, this is a WIP feature")
        return
        for spec in specs_selected:
            inp = self.ask_for_spec_input(spec)

    def add_part(self, part_db: database.EEData.GenericPart):
        """ Function gets called when a part is to be added """
        try:
            # Ask for manufacturer part number first, and make sure there are no conflicts
            manufacturer = console.input("Enter the manufacturer part number: ")
            if part_db.check_if_already_in_db_by_manuf(manufacturer) is not None:
                console.print("[red]Part is already in the database[/]")
                return
            new_part = part_db.part_type(mfr_part_numb=manufacturer)
            for spec_db_name in part_db.table_item_display_order:
                if spec_db_name == 'mfr_part_numb':
                    continue
                spec = self.find_spec_by_db_name(part_db.table_item_spec, spec_db_name)
                new_part[spec_db_name] = self.ask_for_spec_input(spec)
            part_db.create_part(new_part)
        except KeyboardInterrupt:
            console.print("\nOk, no part is added")
            return

    def delete_part(self, part_db: database.EEData.GenericPart):
        """ This gets called when a part is to be deleted """
        try:
            manufacturer = console.input("Enter the manufacturer part number: ")
            if manufacturer == '':
                raise KeyboardInterrupt()
        except KeyboardInterrupt:
            console.print("[green]\nDeleted Nothing[/]")
            return
        try:
            part_db.delete_part_by_mfr_number(manufacturer)
        except database.EmptyInDatabase:
            console.print("[red]The manufacturer is not in the database[/]")

    def component_cli(self, part_db: database.EEData.GenericPart):
        """ The CLI handler for components """
        while 1:
            to_do = questionary.select("What do you want to do in this component database? ", choices=["Print parts in DB", "Add Part", "Delete Part", "Nothing"]).ask()
            if to_do is None:
                raise KeyboardInterrupt()
            if to_do == "Nothing":
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
                self.add_part(part_db)
            elif to_do == "Delete Part":
                self.delete_part(part_db)

    def main(self):
        console.print(rich.panel.Panel("Welcome to the E707PD", title_align='center'))
        try:
            while 1:
                component = questionary.select("Select the component you want do things with:", choices=list(self.db.components.keys())+['Exit']).ask()
                if component is None:
                    raise KeyboardInterrupt()
                elif component == 'Exit':
                    break
                part_db = self.db.components[component]

                self.component_cli(part_db)

        except KeyboardInterrupt:
            pass
        finally:
            console.print("\nGood night!")
            self.db.close()
            self.conf.save()


if __name__ == "__main__":
    c = CLI()
    c.main()
