import logging
import sqlite3
import json
import os
from dataclasses import dataclass
import typing

from databaseSpec import *


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
            self.part_type = GenericItem

        def check_if_table(self):
            """
                Function that checks if the proper table is setup, and creates one if there isn't
                :return:
            """
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

        def check_if_already_in_db(self, part_info: GenericItem):
            # TODO: Add check if the manufacturer is empty
            return self.check_if_already_in_db_by_manuf(part_info.manufacturer)

        def check_if_already_in_db_by_manuf(self, manufacturer: str) -> (None, int):
            """
                Function that checks if a part is already in the database. A generic part just goes by manufacturer
                part number, otherwise a component-specific callback needs to be added (to look up generic parts for
                example without a manufacturer part number)
                :param manufacturer: The part info class
                :return:
            """
            if manufacturer is not None:
                self.cur.execute(" SELECT id FROM "+self.table_name+" WHERE manufacturer=? ", (manufacturer, ))
                d = self.cur.fetchall()
                print(d)
                if len(d) == 0:
                    return None
                elif len(d) == 1:
                    return d[0][0]
                else:
                    raise UserWarning("There is more than 1 entry for a manufacturer specific part")
            else:
                raise UserWarning("Empty manufacturer")

        def get_part_by_id(self, sql_id: int):
            """
                Function that returns parts parameters by part ID
                :param sql_id: Part ID in the SQL table
                :return:
            """
            self.cur.execute(" SELECT * FROM "+self.table_name+" WHERE id=? ", (sql_id, ))
            d = self.cur.fetchall()
            ret = self.part_type()
            if len(d) == 0:
                raise EmptyInDatabase()
            elif len(d) == 1:
                for i, item in enumerate(self.table_item_spec):
                    # TODO: Update so this command isn't table column position specific.
                    ret[item['db_name']] = d[0][i+1]
                return ret

        def update_part(self, part_info: GenericItem):
            """
                Update a part based on manufacturer
                :param part_info:
                :return:
            """
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

        def create_part(self, part_info: GenericItem):
            """
                Function to create a part for the given info
                :param part_info:
                :return:
            """
            # Check if key already exists in table
            for item in self.table_item_spec:
                if item['required'] is True:
                    if part_info[item['db_name']] is None:
                        raise InputException("Did not assign key %s, but it's required" % item['db_name'])
            # If a part is already in a database, then raise an exception
            duplicate_id = self.check_if_already_in_db(part_info)
            if duplicate_id is False:
                raise EmptyInDatabase()
            # Create a new part inside the database
            self._insert_part_in_db(part_info)

        def _insert_part_in_db(self, part_info: GenericItem):
            # Run an insert command into the database
            sql_command = "INSERT INTO " + self.table_name + " ("
            for i, item in enumerate(self.table_item_spec):
                sql_command += item['db_name'] + ", "
            # Remove last comma and space
            sql_command = sql_command[:-2] + ") VALUES ("
            for i, item in enumerate(self.table_item_spec):
                sql_command += "'" + str(part_info[item['db_name']]) + "', "
            sql_command = sql_command[:-2] + ");"
            self.cur.execute(sql_command)

        def append_stock_by_manufacturer(self, manufacturer: str, append_by: int):
            p_id = self.check_if_already_in_db_by_manuf(manufacturer)
            if p_id is None:
                raise EmptyInDatabase()
            sql_command = "UPDATE " + self.table_name + " SET stock=stock+? WHERE id=?"
            sql_params = [append_by, p_id]
            self.cur.execute(sql_command, sql_params)

    class Resistance(_GenericPart):
        def __init__(self, cursor: sqlite3.Cursor):
            super().__init__(cursor)
            self.table_name = 'resistance'
            self.table_item_spec = eedata_resistors_spec
            self.part_type = Resistor
            self.check_if_table()

    class Capacitors(_GenericPart):
        def __init__(self, cursor: sqlite3.Cursor):
            super().__init__(cursor)
            self.table_name = 'capacitor'
            self.table_item_spec = eedata_capacitor_spec
            self.part_type = Capacitor
            self.check_if_table()

    def __init__(self):
        self.log = logging.getLogger('Database')
        self.conn = sqlite3.connect('project_db.db')

        # self.resistors = self.Resistance(self.conn.cursor())
        self.resistors = self.Resistance(self.conn.cursor(factory=self._CustomCursor))
        self.capacitors = self.Capacitors(self.conn.cursor(factory=self._CustomCursor))

    def close(self):
        self.conn.commit()
        self.conn.close()

    def save(self):
        self.conn.commit()
