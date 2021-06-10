import database
import logging
import rich
import rich.console
import rich.panel
from rich.prompt import Prompt
from rich.logging import RichHandler
import rich.table

l = logging.getLogger()
l.setLevel(logging.WARNING)
l.addHandler(RichHandler())

d = database.EEData()

console = rich.console.Console(style="blue")
console.print(rich.panel.Panel("Welcome to the E707PD", title_align='center'))


def print_all_parts(part_name: str):
    part_db = d.components[part_name]
    parts_list = part_db.get_all_parts()
    ta = rich.table.Table(title="All parts in %s" % part_name)
    for spec in part_db.table_item_spec:
        ta.add_column(spec['showcase_name'])
    for part in parts_list:
        row = []
        for spec in part_db.table_item_spec:
            row.append(str(part[spec['db_name']]))
        ta.add_row(*row)
    console.print(ta)


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


try:
    while 1:
        component = ask_for_option_with_numbers("Please enter a number to correspond to the following component you want to select:", d.components.keys())
        # TODO: Add more than just printing all parts
        try:
            print_all_parts(component)
        except database.EmptyInDatabase:
            console.print("[italic red]Sorry, but there are no parts for that component[/]")

except KeyboardInterrupt:
    console.print("\nGood night!")
    d.close()
