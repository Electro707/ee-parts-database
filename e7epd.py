import logging
import sqlite3
import json
import os
from dataclasses import dataclass
import typing

from e707pd_spec import *

__version__ = '0.1pre'


class InputException(Exception):
    def __init__(self, message):
        super().__init__(message)


class EmptyInDatabase(Exception):
    def __init__(self):
        super().__init__('Empty Part')


class E7EPD:
    class _CustomCursor(sqlite3.Cursor):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.log = logging.getLogger('sql')

        def execute(self, sql: str, parameters: typing.Iterable[typing.Any] = []) -> sqlite3.Cursor:
            self.log.debug('Executing SQL command %s with params %s' % (sql, parameters))
            return super().execute(sql, parameters)

    class GenericPart:
        """
            This is a generic part constructor, which other components (like Resistors) will base off of
        """
        def __init__(self, cursor: sqlite3.Cursor):
            self.cur = cursor
            self.table_name = None      # type: str
            self.table_item_spec = None     # type: list
            self.table_item_display_order = None        # type: list
            self.part_type = GenericItem
            self.log = logging.getLogger(self.table_name)

        def check_if_table(self):
            """
                Function that checks if the proper table is setup, and creates one if there isn't
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
            """
                Checks if a given part is already in the database

                Currently it's done through checking for a match with the manufacturer part number

                :param part_info: A part item class

                :TODO: Add check if the manufacturer is empty
            """
            return self.check_if_already_in_db_by_manuf(part_info.mfr_part_numb)

        def check_if_already_in_db_by_manuf(self, mfr_part_numb: str) -> (None, int):
            """
                Function that checks if a part is already in the database. A generic part just goes by manufacturer
                part number, otherwise a component-specific callback needs to be added (to look up generic parts for
                example without a manufacturer part number)

                :param mfr_part_numb: The manufacturer part number to look for.

                :return: None if the part doesn't exist in the database, The SQL ID if it does

                :raises UserWarning: This should NEVER be triggered unless something went terribly wrong or if you manually edited the database. If the latter, please create a PR with the traceback

                :raises InputException: If the manufacturer part number is None, this will get raised
            """
            if mfr_part_numb is not None:
                self.cur.execute(" SELECT id FROM "+self.table_name+" WHERE mfr_part_numb=? ", (mfr_part_numb, ))
                d = self.cur.fetchall()
                if len(d) == 0:
                    return None
                elif len(d) == 1:
                    return d[0][0]
                else:
                    raise UserWarning("There is more than 1 entry for a manufacturer part number")
            else:
                raise InputException("Did not give a manufacturer part number")

        def get_part_by_id(self, sql_id: int) -> GenericItem:
            """
                Function that returns parts parameters by part ID

                :param sql_id: Part ID in the SQL table

                :return: The part's item class

                :raises EmptyInDatabase: If the SQL ID does not exist in the database
            """
            sql_command = "SELECT "
            for i, item in enumerate(self.table_item_spec):
                sql_command += item['db_name'] + ", "
            # Remove last comma
            sql_command = sql_command[:-2] + "FROM" + self.table_name + "WHERE id=?"
            self.cur.execute(sql_command, (sql_id, ))
            d = self.cur.fetchall()
            ret = self.part_type()
            if len(d) == 0:
                raise EmptyInDatabase()
            elif len(d) == 1:
                for i, item in enumerate(self.table_item_spec):
                    ret[item['db_name']] = d[0][i]
                return ret

        def update_part(self, part_info: GenericItem):
            """
                Update a part based on manufacturer part number

                :param part_info: The part item class you want to update
            """
            if part_info.mfr_part_numb is not None:
                sql_command = "UPDATE " + self.table_name + " SET "
                sql_params = []
                for i, item in enumerate(self.table_item_spec):
                    sql_command += item['db_name'] + "=?,"
                    sql_params.append(part_info[item['db_name']])
                # Remove last comma
                sql_command = sql_command[:-1] + "WHERE mfr_part_numb=?"
                sql_params.append(part_info.mfr_part_numb)
                self.cur.execute(sql_command, sql_params)

        def delete_part_by_mfr_number(self, mfr_part_numb: str):
            to_del_id = self.check_if_already_in_db_by_manuf(mfr_part_numb)
            if to_del_id is None:
                raise EmptyInDatabase()
            self.log.debug("Deleting part %s with ID %s" % (mfr_part_numb, to_del_id))
            sql_command = "DELETE FROM " + self.table_name + " WHERE id=?"
            self.cur.execute(sql_command, [to_del_id, ])

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
            sql_params = []
            sql_command = "INSERT INTO " + self.table_name + " ("
            for i, item in enumerate(self.table_item_spec):
                sql_command += item['db_name'] + ", "
            # Remove last comma and space
            sql_command = sql_command[:-2] + ") VALUES ("
            for i, item in enumerate(self.table_item_spec):
                # if part_info[item['db_name']] is None:
                #     part_info[item['db_name']] = 'NULL'
                sql_command += "?, "
                sql_params.append(part_info[item['db_name']])
            sql_command = sql_command[:-2] + ");"
            self.cur.execute(sql_command, sql_params)

        def append_stock_by_manufacturer_part_number(self, mfr_part_numb: str, append_by: int):
            p_id = self.check_if_already_in_db_by_manuf(mfr_part_numb)
            if p_id is None:
                raise EmptyInDatabase()
            sql_command = "UPDATE " + self.table_name + " SET stock=stock+? WHERE id=?"
            sql_params = [append_by, p_id]
            self.cur.execute(sql_command, sql_params)

        def get_all_parts(self) -> typing.List[GenericItem]:
            sql_command = "SELECT "
            for i, item in enumerate(self.table_item_spec):
                sql_command += item['db_name'] + ", "
            # Remove last comma
            sql_command = sql_command[:-2] + " FROM " + self.table_name
            self.cur.execute(sql_command)
            d = self.cur.fetchall()
            ret = []
            if len(d) == 0:
                raise EmptyInDatabase()
            for db_part in d:
                part = self.part_type()
                for i, item in enumerate(self.table_item_spec):
                    part[item['db_name']] = db_part[i]
                ret.append(part)
            return ret

        def is_database_empty(self):
            self.cur.execute(" SELECT id FROM " + self.table_name)
            d = self.cur.fetchall()
            if len(d) == 0:
                return True
            return False

        def drop_table(self):
            self.log.warning("DROPPING TABLE FOR THIS PART...DON'T REGRET THIS LATER!")
            self.cur.execute("DROP TABLE " + self.table_name)
            # Recreate table
            self.check_if_table()

    class Resistance(GenericPart):
        def __init__(self, cursor: sqlite3.Cursor):
            super().__init__(cursor)
            self.table_name = 'resistance'
            self.table_item_spec = eedata_resistors_spec
            self.table_item_display_order = eedata_resistor_display_order
            self.part_type = Resistor
            self.check_if_table()

    class Capacitors(GenericPart):
        def __init__(self, cursor: sqlite3.Cursor):
            super().__init__(cursor)
            self.table_name = 'capacitor'
            self.table_item_spec = eedata_capacitor_spec
            self.table_item_display_order = eedata_capacitor_display_order
            self.part_type = Capacitor
            self.check_if_table()

    class ICs(GenericPart):
        def __init__(self, cursor: sqlite3.Cursor):
            super().__init__(cursor)
            self.table_name = 'ic'
            self.table_item_spec = eedata_ic_spec
            self.table_item_display_order = eedata_ic_display_order
            self.part_type = IC
            self.check_if_table()

    def __init__(self, db_conn):
        self.log = logging.getLogger('Database')
        self.conn = db_conn

        self.resistors = self.Resistance(self.conn.cursor())
        self.capacitors = self.Capacitors(self.conn.cursor())
        self.ics = self.ICs(self.conn.cursor())

        self.components = {
            'Resistors': self.resistors,
            'Capacitors': self.capacitors,
            'ICs': self.ics
        }

    def close(self):
        """
            Commits to the database and closes the database connection

            Call this when exiting your program
        """
        self.conn.commit()
        self.conn.close()

    def save(self):
        """
            Saves any changes done to the database
        """
        self.conn.commit()
