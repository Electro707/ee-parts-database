import logging
import json
import os
import time
import sqlalchemy
import sqlalchemy.future
import typing

from e707pd_spec import *

# Version of this backend
__version__ = '0.3'
# Version of the database spec
database_spec_rev = '0.3'


class InputException(Exception):
    """ Exception that gets raised on any input error """
    def __init__(self, message):
        super().__init__(message)


class EmptyInDatabase(Exception):
    """ Exception that gets raised when there is no parts in the database """
    def __init__(self):
        super().__init__('Empty Part')


class NegativeStock(Exception):
    """ Exception that gets raised when the removal of stock will result in a negative stock, which is physically
     impossible (you're always welcome to prove me wrong)

     Attributes:
        amount_to_make_zero (int): How many parts to make the part's stock zero.

     """
    def __init__(self, amount_to_make_zero):
        self.amount_to_make_zero = amount_to_make_zero
        super().__init__('Stock will go to negative')


class E7EPD:
    # class _CustomCursor(sqlite3.Cursor):
    #     def __init__(self, *args, **kwargs):
    #         super().__init__(*args, **kwargs)
    #         self.log = logging.getLogger('sql')
    #
    #     def execute(self, sql: str, parameters: typing.Iterable[typing.Any] = []) -> sqlite3.Cursor:
    #         self.log.debug('Executing SQL command %s with params %s' % (sql, parameters))
    #         return super().execute(sql, parameters)

    class ConfigTable:
        def __init__(self, conn: sqlalchemy.future.Connection):
            self.conn = conn
            self.table_name = 'e7epd_config'
            self.log = logging.getLogger('config')
            self.check_if_table()

        def check_if_table(self):
            if self.cur_type == DBType.sqlite3:
                self.cur.execute("SELECT count(name) FROM sqlite_schema WHERE type='table' AND name=? ", (self.table_name,))
                d = self.cur.fetchall()
                if d[0][0] == 0:
                    sql_command = "CREATE TABLE " + self.table_name + " (id INTEGER NOT NULL AUTOINCREMENT PRIMARY KEY, db_keys VARCHAR(20) NOT NULL, val VARCHAR(20) NOT NULL);"
                    self.cur.execute(sql_command)
            elif self.cur_type == DBType.mysql:
                self.cur.execute("SELECT * FROM information_schema.tables WHERE table_name=%s ", (self.table_name,))
                d = self.cur.fetchall()
                if len(d) == 0:
                    sql_command = "CREATE TABLE " + self.table_name + " (id INTEGER NOT NULL AUTO_INCREMENT PRIMARY KEY, db_keys VARCHAR(20) NOT NULL, val VARCHAR(20) NOT NULL);"
                    self.cur.execute(sql_command)

        def get_info(self, key: str) -> typing.Union[str, None]:
            self.cur.execute("SELECT db_keys, val FROM " + self.table_name + " WHERE db_keys=?", [key])
            d = self.cur.fetchall()
            if len(d) == 0:
                return None
            elif len(d) == 1:
                return d[0][1]
            else:
                raise UserWarning("There isn't supposed to be more than 1 key")

        def store_info(self, key: str, value: str):
            if self.get_info(key) is None:  # There isn't an entry for this, so create it
                self.cur.execute("INSERT INTO " + self.table_name + "(db_keys, val) VALUES (?, ?)", [key, value])
                self.log.debug('Inserted key-value pair: {}={}'.format(key, value))
            else:
                self.cur.execute("UPDATE " + self.table_name + " SET val=? WHERE db_keys=?", [value, key])
                self.log.debug('Updated key {} with value {}'.format(key, value))

        def get_db_version(self) -> typing.Union[str, None]:
            return self.get_info('db_ver')

        def store_db_version(self):
            self.store_info('db_ver', database_spec_rev)

    class GenericPart:
        """ This is a generic part constructor, which other components (like Resistors) will base off of """
        def __init__(self, cursor: sqlite3.Cursor):
            self.cur = cursor
            self.table_name = None      # type: str
            self.table_item_spec = None     # type: list
            self.table_item_display_order = None        # type: list
            self.part_type = GenericItem
            self.log = logging.getLogger(self.table_name)

        def check_if_table(self):
            """ Function that checks if the proper table is setup, and creates one if there isn't """
            if self.cur_type == DBType.sqlite3:
                self.cur.execute("SELECT count(name) FROM sqlite_schema WHERE type='table' AND name=? ", (self.table_name,))
                d = self.cur.fetchall()
                if d[0][0] == 0:
                    sql_command = "CREATE TABLE " + self.table_name + " (id INTEGER NOT NULL AUTOINCREMENT PRIMARY KEY, db_keys VARCHAR(20) NOT NULL, val VARCHAR(20) NOT NULL);"
                    self.cur.execute(sql_command)
            elif self.cur_type == DBType.mysql:
                self.cur.execute("SELECT * FROM information_schema.tables WHERE table_name=%s ", (self.table_name,))
                d = self.cur.fetchall()
                if len(d) == 0:
                    sql_command = "CREATE TABLE " + self.table_name + " (id INTEGER NOT NULL AUTO_INCREMENT PRIMARY KEY, db_keys VARCHAR(20) NOT NULL, val VARCHAR(20) NOT NULL);"
                    self.cur.execute(sql_command)

        def check_if_already_in_db(self, part_info: GenericItem):
            """ Checks if a given part is already in the database
                Currently it's done through checking for a match with the manufacturer part number

                Args:
                    part_info (GenericItem): A part item class

                TODO:
                    Add check if the manufacturer is empty
            """
            return self.check_if_already_in_db_by_manuf(part_info.mfr_part_numb)

        def check_if_already_in_db_by_manuf(self, mfr_part_numb: str) -> (None, int):
            """
                Function that checks if a part is already in the database. A generic part just goes by manufacturer
                part number, otherwise a component-specific callback needs to be added (to look up generic parts for
                example without a manufacturer part number)

                Args:
                    mfr_part_numb (str): The manufacturer part number to look for.

                Returns:
                    None if the part doesn't exist in the database, The SQL ID if it does

                Raises:
                    UserWarning: This should NEVER be triggered unless something went terribly wrong or if you manually edited the database. If the latter, please create a PR with the traceback
                    InputException: If the manufacturer part number is None, this will get raised
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

                Args:
                    sql_id (int): Part ID in the SQL table

                Returns:
                    The part's item class

                Raises:
                    EmptyInDatabase: If the SQL ID does not exist in the database
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

        def get_part_by_mfr_part_numb(self, mfr_part_numb: str) -> GenericItem:
            """
                Function that returns parts parameters by part ID

                Args:
                    mfr_part_numb (str): The part's manufacturer part number

                Returns:
                    The part's item class

                Raises:
                    EmptyInDatabase: If the SQL ID does not exist in the database
            """
            sql_command = "SELECT "
            for i, item in enumerate(self.table_item_spec):
                sql_command += item['db_name'] + ", "
            # Remove last comma
            sql_command = sql_command[:-2] + " FROM " + self.table_name + " WHERE mfr_part_numb=?"
            self.cur.execute(sql_command, (mfr_part_numb, ))
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

                Args:
                     part_info (GenericItem): The part item class you want to update
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
            """
                Function to delete a part by the manufacturer part number

                Args:
                    mfr_part_numb: The manufacturer part number of the part to delete

                Raises:
                     EmptyInDatabase: Raises this exception if there is no part in the database with that manufacturer part number
            """
            to_del_id = self.check_if_already_in_db_by_manuf(mfr_part_numb)
            if to_del_id is None:
                raise EmptyInDatabase()
            self.log.debug("Deleting part %s with ID %s" % (mfr_part_numb, to_del_id))
            sql_command = "DELETE FROM " + self.table_name + " WHERE id=?"
            self.cur.execute(sql_command, [to_del_id, ])

        def create_part(self, part_info: GenericItem):
            """
                Function to create a part for the given info

                Args:
                     part_info (GenericItem): The part item class to add to the database
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
            """ Internal function to insert a part into the database """
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
            """ Appends stock to a part by the manufacturer part number

            Args:
                mfr_part_numb (str): The manufacturer number to add the stock to
                append_by: How much stock to add

            Raises:
                EmptyInDatabase: Raises this if the manufacturer part number does not exist in the database
            """
            p_id = self.check_if_already_in_db_by_manuf(mfr_part_numb)
            if p_id is None:
                raise EmptyInDatabase()
            sql_command = "UPDATE " + self.table_name + " SET stock=stock+? WHERE id=?"
            sql_params = [append_by, p_id]
            self.cur.execute(sql_command, sql_params)

        def remove_stock_by_manufacturer_part_number(self, mfr_part_numb: str, remove_by: int):
            """ Removes stock from a part by the manufacturer part number

            Args:
                mfr_part_numb (str): The manufacturer number to add the stock to
                remove_by: How much stock to remove from the part

            Raises:
                EmptyInDatabase: Raises this if the manufacturer part number does not exist in the database
            """
            part = self.get_part_by_mfr_part_numb(mfr_part_numb)
            part.stock -= remove_by
            if part.stock < 0:
                raise NegativeStock(part.stock+remove_by)
            self.update_part(part)

        def get_all_parts(self) -> typing.List[GenericItem]:
            """ Get all parts in the database

                Returns:
                    EmptyInDatabase: Raises this if the manufacturer part number does not exist in the database
            """
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

        def get_all_mfr_part_numb_in_db(self) -> list:
            """ Get all manufaturer part numbers as a list

            Returns:
                A list of all manufacturer part numbers in the database
            """
            to_ret = []
            self.cur.execute("SELECT mfr_part_numb FROM " + self.table_name + ";")
            d = self.cur.fetchall()
            ret = []
            if len(d) == 0:
                raise EmptyInDatabase()
            for m in d:
                ret.append(m[0])
            return ret

        def get_sorted_parts(self, part_filter: GenericItem):
            sql_command = "SELECT "
            sql_params = []
            for i, item in enumerate(self.table_item_spec):
                sql_command += item['db_name'] + ", "
            # Remove last comma
            sql_command = sql_command[:-2] + " FROM " + self.table_name + " WHERE "
            for i, item in enumerate(self.table_item_spec):
                if part_filter[item['db_name']] is None:
                    continue
                sql_command += "{}=?, ".format(item['db_name'])
                sql_params.append(part_filter[item['db_name']])
            sql_command = sql_command[:-2] + ';'
            self.cur.execute(sql_command, sql_params)
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
            """ Checks if the database is empty

            Returns:
                True if the database is empty, False if not
            """
            self.cur.execute(" SELECT id FROM " + self.table_name)
            d = self.cur.fetchall()
            if len(d) == 0:
                return True
            return False

        def drop_table(self):
            """ Drops the database table and create a new one. Also known as the Nuke option """
            self.log.warning("DROPPING TABLE FOR THIS PART (%s)...DON'T REGRET THIS LATER!" % self.table_name)
            self.cur.execute("DROP TABLE " + self.table_name)

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

    class Inductors(GenericPart):
        def __init__(self, cursor: sqlite3.Cursor):
            super().__init__(cursor)
            self.table_name = 'inductor'
            self.table_item_spec = eedata_inductor_spec
            self.table_item_display_order = eedata_inductor_display_order
            self.part_type = Inductor
            self.check_if_table()

    class ICs(GenericPart):
        def __init__(self, cursor: sqlite3.Cursor):
            super().__init__(cursor)
            self.table_name = 'ic'
            self.table_item_spec = eedata_ic_spec
            self.table_item_display_order = eedata_ic_display_order
            self.part_type = IC
            self.check_if_table()

    class Diodes(GenericPart):
        def __init__(self, cursor: sqlite3.Cursor):
            super().__init__(cursor)
            self.table_name = 'diode'
            self.table_item_spec = eedata_diode_spec
            self.table_item_display_order = eedata_diode_display_order
            self.part_type = Diode
            self.check_if_table()

    def __init__(self, db_conn: sqlalchemy.future.Engine):
        self.log = logging.getLogger('Database')
        self.db_conn = db_conn
        self.conn = self.db_conn.connect()
        self.config = self.ConfigTable(self.conn.cursor(), self.conn_type)

        self.resistors = self.Resistance(self.conn.cursor())
        self.capacitors = self.Capacitors(self.conn.cursor())
        self.inductors = self.Inductors(self.conn.cursor())
        self.ics = self.ICs(self.conn.cursor())
        self.diodes = self.Diodes(self.conn.cursor())

        self.components = {
            'Resistors': self.resistors,
            'Capacitors': self.capacitors,
            'Inductors': self.inductors,
            'ICs': self.ics,
            'Diodes': self.diodes
        }

        # If the DB version is None (if the config table was just created), then populate the current version
        if self.config.get_db_version() is None:
            self.config.store_db_version()

    def close(self):
        """
            Commits to the database and closes the database connection.
            Call this when exiting your program
        """
        self.conn.close()

    def save(self):
        """
            Saves any changes done to the database
        """
        self.conn.commit()

    def wipe_database(self):
        """
            Wipes the component databases
        """
        for c in self.components:
            self.components[c].drop_table()
            # Recreate table
            self.components[c].check_if_table()

    def update_database(self):
        """
            Updates the database to the most recent revision
        """
        self.log.info("Backing up database before applying changes")
        self.backup_db()
        if self.config.get_db_version() == '0.2':   # From 0.2 -> 0.3: Add storage to all parts
            for c in self.components:
                self.components[c].cur.execute("ALTER TABLE " + self.components[c].table_name + " ADD storage VARCHAR")
        self.config.store_db_version()

    def is_latest_database(self) -> bool:
        """
            Returns whether the database is matched with the latest rev
            Returns:
                bool: True if the database is the latest, False if not
        """
        if self.config.get_db_version() != database_spec_rev:
            return False
        return True

    def backup_db(self):
        """
            Backs up the database under a new backup file
        """
        new_db_file = os.path.dirname(os.path.abspath(__file__)) + '/partdb_backup_%s' % time.strftime('%y%m%d%H%M%S')
        self.log.info("Backing database under %s" % new_db_file)
        # For now do with only SQLite3
        # TODO: Make the backup function compatible with mySQL once that's implemented
        backup_conn = sqlite3.connect(new_db_file)
        with backup_conn:
            self.conn.backup(backup_conn)
        self.log.info("Successfully backed-up database")
        backup_conn.close()
