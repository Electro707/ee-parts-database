import logging
import json
import os
import time
import sqlalchemy
import sqlalchemy.future
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, Float, String
import typing

import e707pd_spec as spec

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
        _Base = declarative_base()

        class _DataBase(_Base):
            __tablename__ = 'e7epd_config'
            id = Column(Integer, primary_key=True)
            key = Column(String)
            val = Column(String)

        def __init__(self, session: sqlalchemy.orm.Session, engine: sqlalchemy.future.Engine):
            self.session = session
            self.log = logging.getLogger('config')

            self._DataBase.metadata.create_all(engine)

        def get_info(self, key: str) -> typing.Union[str, None]:
            d = self.session.query(self._DataBase).filter_by(key=key).all()
            if len(d) == 0:
                return None
            elif len(d) == 1:
                return d[0].val
            else:
                raise UserWarning("There isn't supposed to be more than 1 key")

        def store_info(self, key: str, value: str):
            d = self.session.query(self._DataBase).filter_by(key=key).all()
            if len(d) == 0:
                p = self._DataBase(key=key, val=value)
                self.session.add(p)
                self.log.debug('Inserted key-value pair: {}={}'.format(key, value))
            elif len(d) == 1:
                p = d[0].val = value
                self.log.debug('Updated key {} with value {}'.format(key, value))
            else:
                raise UserWarning("There isn't supposed to be more than 1 key")

            self.session.commit()

        def get_db_version(self) -> typing.Union[str, None]:
            return self.get_info('db_ver')

        def store_db_version(self):
            self.store_info('db_ver', database_spec_rev)

    class GenericPart:
        """ This is a generic part constructor, which other components (like Resistors) will base off of """
        def __init__(self, session: sqlalchemy.orm.Session):
            self.session = session
            self.table_item_spec: list
            self.table_item_display_order: list
            self.part_type: spec.GenericItem

            if not hasattr(self, 'table_item_spec'):
                self.table_item_spec = None
            if not hasattr(self, 'table_item_display_order'):
                self.table_item_display_order = None
            if not hasattr(self, 'part_type'):
                self.part_type = None

            self.table_name = self.part_type.__tablename__
            self.log = logging.getLogger(self.part_type.__tablename__)

        def check_if_already_in_db(self, part_info: spec.GenericItem):
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
                d = self.session.query(self.part_type).filter_by(mfr_part_numb=mfr_part_numb).all()
                if len(d) == 0:
                    return None
                elif len(d) == 1:
                    return d[0].id
                else:
                    raise UserWarning("There is more than 1 entry for a manufacturer part number")
            else:
                raise InputException("Did not give a manufacturer part number")

        def get_part_by_id(self, sql_id: int) -> spec.GenericItem:
            """
                Function that returns parts parameters by part ID

                Args:
                    sql_id (int): Part ID in the SQL table

                Returns:
                    The part's item class

                Raises:
                    EmptyInDatabase: If the SQL ID does not exist in the database
            """
            d = self.session.query(self.part_type).filter_by(id=sql_id).all()
            if len(d) == 0:
                raise EmptyInDatabase()
            elif len(d) == 1:
                return d[0]
            else:
                # TODO: Add exception, as having more than 1 of the same ID is impossible
                pass

        def get_part_by_mfr_part_numb(self, mfr_part_numb: str) -> spec.GenericItem:
            """
                Function that returns parts parameters by part ID

                Args:
                    mfr_part_numb (str): The part's manufacturer part number

                Returns:
                    The part's item class

                Raises:
                    EmptyInDatabase: If the SQL ID does not exist in the database
            """
            d = self.session.query(self.part_type).filter_by(mfr_part_numb=mfr_part_numb).all()
            if len(d) == 0:
                raise EmptyInDatabase()
            elif len(d) == 1:
                return d[0]
            else:
                # TODO: Add exception, as having more than 1 of the same ID is impossible
                pass

        def update_part(self, part_info: spec.GenericItem):
            """
                Update a part based on manufacturer part number

                Args:
                     part_info (GenericItem): The part item class you want to update
            """
            if part_info.mfr_part_numb is not None:
                q = self.session.query(self.part_type).filter_by(mfr_part_numb=part_info.mfr_part_numb)
                q.update(part_info, synchronize_session="fetch")

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
            self.session.delete(self.get_part_by_mfr_part_numb(to_del_id))

        def create_part(self, part_info: spec.GenericItem):
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

        def _insert_part_in_db(self, part_info: spec.GenericItem):
            """ Internal function to insert a part into the database """
            # Run an insert command into the database
            self.log.debug('Inserting %s into database' % part_info)
            self.session.add(part_info)
            self.session.commit()

        def append_stock_by_manufacturer_part_number(self, mfr_part_numb: str, append_by: int):
            """ Appends stock to a part by the manufacturer part number

            Args:
                mfr_part_numb (str): The manufacturer number to add the stock to
                append_by: How much stock to add

            Raises:
                EmptyInDatabase: Raises this if the manufacturer part number does not exist in the database
            """
            part = self.get_part_by_mfr_part_numb(mfr_part_numb)
            part.stock += append_by

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
            self.session.commit()

        def get_all_parts(self) -> typing.List[spec.GenericItem]:
            """ Get all parts in the database

                Returns:
                    EmptyInDatabase: Raises this if the manufacturer part number does not exist in the database
            """
            return self.session.query(self.part_type).all()

        def get_all_mfr_part_numb_in_db(self) -> list:
            """ Get all manufaturer part numbers as a list

            Returns:
                A list of all manufacturer part numbers in the database
            """
            d = self.session.query(self.part_type).all()
            if len(d) == 0:
                raise EmptyInDatabase()
            return [p.mfr_part_numb for p in d]

        def get_sorted_parts(self, part_filter: spec.GenericItem):
            q = self.session.query(self.part_type)

            if q.count() == 0:
                raise EmptyInDatabase()

            filter_const = {}
            for i, item in enumerate(self.table_item_spec):
                if item['db_name'] not in part_filter.__dict__:
                    continue
                if part_filter[item['db_name']] is None:
                    continue
                filter_const[item['db_name']] = part_filter[item['db_name']]

            d = q.filter_by(**filter_const)
            return d

        def is_database_empty(self):
            """ Checks if the database is empty

            Returns:
                True if the database is empty, False if not
            """
            d = self.session.query(self.part_type).count()
            self.log.debug('Number of parts in database for %s: %s' % (self.table_name, d))
            if d == 0:
                return True
            return False

        def drop_table(self):
            """ Drops the database table and create a new one. Also known as the Nuke option """
            self.log.warning("DROPPING TABLE FOR THIS PART (%s)...DON'T REGRET THIS LATER!" % self.part_type.__tablename__)
            self.part_type.__table__.drop()

    class Resistance(GenericPart):
        def __init__(self, session: sqlalchemy.orm.Session):
            self.table_item_spec = spec.eedata_resistors_spec
            self.table_item_display_order = spec.eedata_resistor_display_order
            self.part_type = spec.Resistor

            super().__init__(session)

    class Capacitors(GenericPart):
        def __init__(self, session: sqlalchemy.orm.Session):
            self.table_item_spec = spec.eedata_capacitor_spec
            self.table_item_display_order = spec.eedata_capacitor_display_order
            self.part_type = spec.Capacitor
            self.log = logging.getLogger(self.part_type.__tablename__)

            super().__init__(session)

    class Inductors(GenericPart):
        def __init__(self, session: sqlalchemy.orm.Session):
            self.table_item_spec = spec.eedata_inductor_spec
            self.table_item_display_order = spec.eedata_inductor_display_order
            self.part_type = spec.Inductor
            self.log = logging.getLogger(self.part_type.__tablename__)

            super().__init__(session)

    class ICs(GenericPart):
        def __init__(self, session: sqlalchemy.orm.Session):
            self.table_item_spec = spec.eedata_ic_spec
            self.table_item_display_order = spec.eedata_ic_display_order
            self.part_type = spec.IC
            self.log = logging.getLogger(self.part_type.__tablename__)

            super().__init__(session)

    class Diodes(GenericPart):
        def __init__(self, session: sqlalchemy.orm.Session):
            self.table_item_spec = spec.eedata_diode_spec
            self.table_item_display_order = spec.eedata_diode_display_order
            self.part_type = spec.Diode
            self.log = logging.getLogger(self.part_type.__tablename__)

            super().__init__(session)

    def __init__(self, db_conn: sqlalchemy.future.Engine):
        self.log = logging.getLogger('Database')
        self.db_conn = db_conn

        self.config = self.ConfigTable(sessionmaker(self.db_conn)(), self.db_conn)

        self.resistors = self.Resistance(sessionmaker(self.db_conn)())
        self.capacitors = self.Capacitors(sessionmaker(self.db_conn)())
        self.inductors = self.Inductors(sessionmaker(self.db_conn)())
        self.ics = self.ICs(sessionmaker(self.db_conn)())
        self.diodes = self.Diodes(sessionmaker(self.db_conn)())

        self.components = {
            'Resistors': self.resistors,
            'Capacitors': self.capacitors,
            'Inductors': self.inductors,
            'ICs': self.ics,
            'Diodes': self.diodes
        }

        spec.GenericItem.metadata.create_all(self.db_conn)

        # If the DB version is None (if the config table was just created), then populate the current version
        if self.config.get_db_version() is None:
            self.config.store_db_version()

    def close(self):
        """
            Commits to the database and closes the database connection.
            Call this when exiting your program
        """
        for c in self.components.values():
            c.session.commit()
            c.session.flush()
            c.session.close()

    def save(self):
        """
            Saves any changes done to the database
        """
        for c in self.components.values():
            c.session.commit()

    def wipe_database(self):
        """
            Wipes the component databases
        """
        for c in self.components:
            self.components[c].drop_table()
        # Recreate table
        spec.GenericItem.metadata.create_all(self.db_conn)

    def update_database(self):
        """
            Updates the database to the most recent revision
        """
        self.log.info("Backing up database before applying changes")
        self.backup_db()
        if self.config.get_db_version() == '0.2':   # From 0.2 -> 0.3: Add storage to all parts
            for c in self.components:
                # self.components[c].cur.execute("ALTER TABLE " + self.components[c].table_name + " ADD storage VARCHAR")
                column_name = self.components[c].part_type.storage.name
                column_type = self.components[c].part_type.storage.type.compile(self.db_conn.dialect)
                print(column_name, column_type)
                self.components[c].session.execute('ALTER TABLE %s ADD COLUMN %s %s' % (self.components[c].table_name, column_name, column_type))
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
        return
        new_db_file = os.path.dirname(os.path.abspath(__file__)) + '/partdb_backup_%s' % time.strftime('%y%m%d%H%M%S')
        self.log.info("Backing database under %s" % new_db_file)
        # For now do with only SQLite3
        # TODO: Make the backup function compatible with mySQL once that's implemented
        backup_conn = sqlite3.connect(new_db_file)
        with backup_conn:
            self.conn.backup(backup_conn)
        self.log.info("Successfully backed-up database")
        backup_conn.close()
