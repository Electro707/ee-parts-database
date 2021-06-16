"""
    Program to generate some documentation, as well as other stuff (I lied, it also generates the dataclass)
"""

import e707pd_spec

generate_for_list = [e707pd_spec.eedata_resistors_spec, e707pd_spec.eedata_capacitor_spec, e707pd_spec.eedata_ic_spec, e707pd_spec.eedata_generic_spec]
spec_name = ["Resistor", "Capacitor", "IC", "GenericItem"]
generate_dataclass = True
generate_database_docs = True


if generate_dataclass:
    for i, generate_for in enumerate(generate_for_list):
        to_print = "@dataclass\nclass %s(GenericItem):\n" % spec_name[i]
        for spec in generate_for:
            if spec in e707pd_spec.eedata_generic_spec and spec_name[i] != "GenericItem":
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
        print("\n")

print('\n\n')

if generate_database_docs:
    for generate_for in generate_for_list:
        to_print = "|Name|SQL Type|Description|\n|---|---|---|\n"
        for spec in generate_for:
            if spec in e707pd_spec.eedata_generic_spec:
                continue
            to_print += "|%s|%s| |\n" % (spec['db_name'], spec['db_type'])
        print(to_print)
