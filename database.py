import logging
import sqlite3
import json
import os
from dataclasses import dataclass
import typing

# Outline the different parts storage specifications

eedata_generic_spec = [
    {
        'db_name': 'stock',
        'showcase_name': 'Stock',
        'db_type': "INT NOT NULL",
        'shows_as': "normal",
        'required': True,
    },
    {
        'db_name': 'manufacturer',
        'showcase_name': 'Manufacturer',
        'db_type': "VARCHAR",
        "shows_as": "normal",
        'required': False,
    }
]

eedata_resistors_spec = eedata_generic_spec + [
    {
        'db_name': 'resistance',
        "showcase_name": "Resistance",
        "db_type": "FLOAT NOT NULL",
        "shows_as_type": "engineering",
        'required': True,
    },
    {
        'db_name': 'tolerance',
        "showcase_name": "Tolerance",
        "db_type": "FLOAT",
        "shows_as_type": "percentage",
        'required': False,
    },
    {
        'db_name': 'package',
        "showcase_name": "Package",
        "db_type": "VARCHAR(20) NOT NULL",
        "shows_as_type": "normal",
        'required': True,
    },
    {
        'db_name': 'power',
        "showcase_name": "Power Rating",
        'db_type': "FLOAT",
        'show_as_type': 'normal',
        'required': False,
    }
]


@dataclass
class _GenericItem:
    stock: int = None
    manufacturer: str = None

    def __getitem__(self, key):
        return self.__dict__[key]

    def __setitem__(self, key, item):
        self.__dict__[key] = item


@dataclass
class Resistor(_GenericItem):
    resistance: float = None
    package: str = None
    power: float = None
    tolerance: float = None


class InputException(Exception):
    def __init__(self, message):
        super().__init__(message)


class EmptyInDatabase(Exception):
    def __init__(self):
        super().__init__('Empty Part')


class EEData:
    class _CustomCursor(sqlite3.Cursor):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.log = logging.getLogger('sql')

        def execute(self, sql: str, parameters: typing.Iterable[typing.Any] = []) -> sqlite3.Cursor:
            self.log.debug('Executing SQL command %s with params %s' % (sql, parameters))
            return super().execute(sql, parameters)

    class _GenericPart:
        def __init__(self, cursor: sqlite3.Cursor):
            self.cur = cursor
            self.table_name = None      # type: str
            self.table_item_spec = None     # type: list
            self.part_type = _GenericItem

        def check_if_table(self):
            self.cur.execute(" SELECT count(name) FROM sqlite_schema WHERE type='table' AND name=? ", (self.table_name, ))
            d = self.cur.fetchall()
            if d[0][0] == 0:
                # Create a table if it doesn't exist
                sql_command = "CREATE TABLE " + self.table_name + " (id INTEGER PRIMARY KEY AUTOINCREMENT, "
                for i, item in enumerate(self.table_item_spec):
                    sql_command += item['db_name'] + " " + item['db_type'] + ", "
                # Remove last comma
                sql_command = sql_command[:-2] + ");"
                # sql_command += "PRIMARY KEY('id') );"
                self.cur.execute(sql_command)

        def check_if_already_in_db(self, part_info: _GenericItem):
            if part_info.manufacturer is not None:
                self.cur.execute(" SELECT id FROM "+self.table_name+" WHERE manufacturer=? ", (part_info.manufacturer, ))
                d = self.cur.fetchall()
                print(d)
                if len(d) == 0:
                    return False
                elif len(d) == 1:
                    return d[0][0]
                # TODO: Handle if there are more than 1 entries
            return False

        def get_part_by_id(self, sql_id: int):
            self.cur.execute(" SELECT * FROM "+self.table_name+" WHERE id=? ", (sql_id, ))
            d = self.cur.fetchall()
            ret = self.part_type()
            if len(d) == 0:
                raise EmptyInDatabase()
            elif len(d) == 1:
                for i, item in enumerate(self.table_item_spec):
                    ret[item['db_name']] = d[0][i+1]
                return ret

        def update_part(self, part_info: _GenericItem):
            if part_info.manufacturer is not None:
                sql_command = "UPDATE " + self.table_name + " SET "
                sql_params = []
                for i, item in enumerate(self.table_item_spec):
                    sql_command += item['db_name'] + "=?,"
                    sql_params.append(part_info[item['db_name']])
                # Remove last comma
                sql_command = sql_command[:-1] + "WHERE manufacturer=?"
                sql_params.append(part_info.manufacturer)
                self.cur.execute(sql_command, sql_params)

        def create_part(self, part_info: _GenericItem):
            sql_command = "INSERT INTO " + self.table_name + " ("
            for i, item in enumerate(self.table_item_spec):
                sql_command += item['db_name'] + ", "
            # Remove last comma and space
            sql_command = sql_command[:-2] + ") VALUES ("
            for i, item in enumerate(self.table_item_spec):
                sql_command += "'" + str(part_info[item['db_name']]) + "', "
            sql_command = sql_command[:-2] + ");"
            self.cur.execute(sql_command)

    class Resistance(_GenericPart):
        def __init__(self, cursor: sqlite3.Cursor):
            super().__init__(cursor)
            self.table_name = 'resistance'
            self.table_item_spec = eedata_resistors_spec
            self.part_type = Resistor
            self.check_if_table()

        def add_resistor(self, resistor: Resistor):
            # Check if key already exists in table
            for item in self.table_item_spec:
                if item['required'] is True:
                    if resistor[item['db_name']] is None:
                        raise InputException("Did not assign key %s, but it's required" % item['db_name'])
            duplicate_id = self.check_if_already_in_db(resistor)
            if duplicate_id is not False:
                self.append_stock(duplicate_id, append_by=resistor.stock)
            else:
                # Otherwise create the resistor
                super().create_part(resistor)

        def check_if_already_in_db(self, resistor: Resistor):
            # Check if manufacturer is already part of DB
            stat = super().check_if_already_in_db(resistor)
            # TODO: Do resistor specific checks then
            return stat

        def append_stock(self, resistor_id: int, append_by: int):
            res = super().get_part_by_id(resistor_id)
            print(res)
            res.stock += append_by
            super().update_part(res)

    def __init__(self):
        self.log = logging.getLogger('Database')
        self.conn = sqlite3.connect('project_db.db')

        # self.resistors = self.Resistance(self.conn.cursor())
        self.resistors = self.Resistance(self.conn.cursor(factory=self._CustomCursor))

    def close(self):
        self.conn.commit()
        self.conn.close()

    def save(self):
        self.conn.commit()