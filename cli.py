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

l = logging.getLogger()
l.setLevel(logging.WARNING)
l.addHandler(RichHandler())

d = database.EEData()

console = rich.console.Console(style="blue")
console.print(rich.panel.Panel("Welcome to the E707PD", title_align='center'))


def find_spec_by_db_name(spec_list: list, db_name: str) -> dict:
    for spec in spec_list:
        if spec['db_name'] == db_name:
            return spec


def ask_for_option_with_numbers(prompt: str, options: list):
    console.print(prompt)
    option = {str(i): d for i, d in enumerate(options)}
    for o in option:
        console.print("[bold cyan]%s[/] -> [green]%s[/]" % (o, option[o]))
    while 1:
        selected = console.input("Select a component: ")
        if selected not in option.keys():
            console.print("[bold red]%s was not a valid option. Try again [/]" % selected)
            continue
        break
    return option[selected]


def print_all_parts(db: database.EEData.GenericPart):
    parts_list = db.get_all_parts()
    ta = rich.table.Table(title="All parts in %s" % db.table_name)
    for spec_db_name in db.table_item_display_order:
        ta.add_column(find_spec_by_db_name(db.table_item_spec, spec_db_name)['showcase_name'])
    for part in parts_list:
        row = []
        for spec_db_name in db.table_item_display_order:
            to_display = part[spec_db_name]
            display_as = find_spec_by_db_name(db.table_item_spec, spec_db_name)['shows_as']
            if display_as == 'engineering':
                to_display = str(EngNumber(to_display))
            elif display_as == 'percentage':
                to_display = str(to_display * 100) + "%"
            else:
                to_display = str(to_display)
            row.append(to_display)
        ta.add_row(*row)
    console.print(ta)


def add_part(db: database.EEData.GenericPart):
    try:
        # Ask for manufacturer part number first, and make sure there are no conflicts
        manufacturer = console.input("Enter the manufacturer part number: ")
        if db.check_if_already_in_db_by_manuf(manufacturer) is not None:
            console.print("[red]Part is already in the database[/]")
            return
        new_part = db.part_type(mfr_part_numb=manufacturer)
        for spec_db_name in db.table_item_display_order:
            if spec_db_name == 'mfr_part_numb':
                continue
            spec = find_spec_by_db_name(db.table_item_spec, spec_db_name)
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

            new_part[spec_db_name] = inp
        db.create_part(new_part)
    except KeyboardInterrupt:
        console.print("\nOk, no part is added")
        return


def delete_part(db: database.EEData.GenericPart):
    manufacturer = console.input("Enter the manufacturer part number: ")
    try:
        db.delete_part_by_mfr_number(manufacturer)
    except database.EmptyInDatabase:
        console.print("[red]The manufacturer is not in the database[/]")


try:
    while 1:
        component = ask_for_option_with_numbers("Please enter a number to correspond to the following component you want to select:", d.components.keys())

        part_db = d.components[component]

        if part_db.is_database_empty():
            console.print("[italic red]Sorry, but there are no parts for that component[/]")
            continue
        to_do = ask_for_option_with_numbers("What game do you want to play:", ["Print all in DB", "Add Part", "Delete Part", "Nothing"])
        if to_do == "Nothing":
            continue
        elif to_do == "Print all in DB":
            print_all_parts(part_db)
        elif to_do == "Add Part":
            add_part(part_db)
        elif to_do == "Delete Part":
            delete_part(part_db)

except KeyboardInterrupt:
    console.print("\nGood night!")
    d.close()
