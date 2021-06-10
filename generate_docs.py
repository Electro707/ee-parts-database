"""
    Program to generate some documentation, as well as other stuff (I lied, it also generates the dataclass)
"""

import databaseSpec

generate_for = databaseSpec.eedata_microcontroller_spec
spec_name = "Microcontroller"
generate_dataclass = True
generate_database_docs = True


if generate_dataclass:
    to_print = "@dataclass\nclass NAME(GenericItem):\n"
    for spec in generate_for:
        if spec in databaseSpec.eedata_generic_spec:
            continue
        to_print += "    %s" % spec['db_name']
        if "FLOAT" in spec['db_type']:
            to_print += ": float = None"
        elif "INT" in spec['db_type']:
            to_print += ": int = None"
        else:
            to_print += ": str = None"
        to_print += "\n"
    print(to_print)

print('\n\n')

if generate_database_docs:
    to_print = "|Name|SQL Type|Description|\n|---|---|---|\n"
    for spec in generate_for:
        if spec in databaseSpec.eedata_generic_spec:
            continue
        to_print += "|%s|%s| |\n" % (spec['db_name'], spec['db_type'])
    print(to_print)
