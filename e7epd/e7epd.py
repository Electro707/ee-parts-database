import logging
import json
import os
import time
import sqlalchemy
import sqlalchemy.future
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, Float, String, Text, JSON
from alembic.runtime.migration import MigrationContext
from alembic.operations import Operations
import typing

import e7epd.e707pd_spec as spec

# Version of the database spec
database_spec_rev = '0.4'


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
    class ConfigTable:
        _Base = declarative_base()

        class _DataBase(_Base):
            __tablename__ = 'e7epd_config'
            id = Column(Integer, primary_key=True)
            key = Column(String(spec.default_string_len))
            val = Column(String(spec.default_string_len))

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
                d[0].val = value
                self.log.debug('Updated key {} with value {}'.format(key, value))
            else:
                raise UserWarning("There isn't supposed to be more than 1 key")

            self.session.commit()

        def get_db_version(self) -> typing.Union[str, None]:
            return self.get_info('db_ver')

        def store_current_db_version(self):
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

                Raises:
                    UserWarning: This should NEVER be triggered unless something went terribly wrong or if you manually edited the database. If the former, please create an bug entry on the project's Github page with the traceback
                    InputException: If the manufacturer part number is None, this will get raised
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
                    UserWarning: This should NEVER be triggered unless something went terribly wrong or if you manually edited the database. If the former, please create an bug entry on the project's Github page with the traceback
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
                raise UserWarning()

        def delete_part_by_mfr_number(self, mfr_part_numb: str):
            """
                Function to delete a part by the manufacturer part number

                Args:
                    mfr_part_numb: The manufacturer part number of the part to delete

                Raises:
                     EmptyInDatabase: Raises this exception if there is no part in the database with that manufacturer part number
            """
            self.log.debug("Deleting part %s" % mfr_part_numb)
            self.session.delete(self.get_part_by_mfr_part_numb(mfr_part_numb))

        def create_part(self, part_info: spec.GenericItem):
            """
                Function to create a part for the given info

                Args:
                     part_info (GenericItem): The part item class to add to the database
            """
            # Check if key already exists in table
            for item in self.table_item_spec:
                if item['required'] is True:
                    # if part_info[item['db_name']] is None:
                    if getattr(part_info, item['db_name']) is None:
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

        def append_stock_by_manufacturer_part_number(self, mfr_part_numb: str, append_by: int) -> int:
            """ Appends stock to a part by the manufacturer part number

            Args:
                mfr_part_numb (str): The manufacturer number to add the stock to
                append_by: How much stock to add

            Returns:
                The new stock of the part after the appending

            Raises:
                EmptyInDatabase: Raises this if the manufacturer part number does not exist in the database
            """
            part = self.get_part_by_mfr_part_numb(mfr_part_numb)
            part.stock += append_by
            self.session.commit()
            return part.stock

        def remove_stock_by_manufacturer_part_number(self, mfr_part_numb: str, remove_by: int) -> int:
            """ Removes stock from a part by the manufacturer part number

            Args:
                mfr_part_numb (str): The manufacturer number to add the stock to
                remove_by: How much stock to remove from the part

            Returns:
                The new stock of the part after removal

            Raises:
                EmptyInDatabase: Raises this if the manufacturer part number does not exist in the database
            """
            part = self.get_part_by_mfr_part_numb(mfr_part_numb)
            if part.stock - remove_by < 0:
                raise NegativeStock(part.stock)
            part.stock -= remove_by
            self.session.commit()
            return part.stock

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
                if getattr(part_filter, item['db_name']) is None:
                    continue
                filter_const[item['db_name']] = getattr(part_filter, item['db_name'])

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

        def commit(self):
            """
                Commits any changes done to part(s)
            """
            self.session.commit()

        def rollback(self):
            """
                Roll back changes done to part(s)
            """
            self.session.rollback()

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

    class Crystals(GenericPart):
        def __init__(self, session: sqlalchemy.orm.Session):
            self.table_item_spec = spec.eedata_crystal_spec
            self.table_item_display_order = spec.eedata_crystal_display_order
            self.part_type = spec.Crystal
            self.log = logging.getLogger(self.part_type.__tablename__)

            super().__init__(session)

    class MOSFETs(GenericPart):
        def __init__(self, session: sqlalchemy.orm.Session):
            self.table_item_spec = spec.eedata_mosfet_spec
            self.table_item_display_order = spec.eedata_mosfet_display_order
            self.part_type = spec.MOSFET
            self.log = logging.getLogger(self.part_type.__tablename__)

            super().__init__(session)

    class BJTs(GenericPart):
        def __init__(self, session: sqlalchemy.orm.Session):
            self.table_item_spec = spec.eedata_bjt_spec
            self.table_item_display_order = spec.eedata_bjt_display_order
            self.part_type = spec.BJT
            self.log = logging.getLogger(self.part_type.__tablename__)

            super().__init__(session)

    class PCBs(GenericPart):
        def __init__(self, session: sqlalchemy.orm.Session):
            self.table_item_spec = spec.eedata_pcb_spec
            self.table_item_display_order = spec.eedata_pcb_display_order
            self.part_type = spec.PCB
            self.log = logging.getLogger(self.part_type.__tablename__)

            super().__init__(session)

    class Connectors(GenericPart):
        def __init__(self, session: sqlalchemy.orm.Session):
            self.table_item_spec = spec.eedata_connector_spec
            self.table_item_display_order = spec.eedata_connector_display_order
            self.part_type = spec.Connector
            self.log = logging.getLogger(self.part_type.__tablename__)

            super().__init__(session)

    class LEDs(GenericPart):
        def __init__(self, session: sqlalchemy.orm.Session):
            self.table_item_spec = spec.eedata_led_spec
            self.table_item_display_order = spec.eedata_led_display_order
            self.part_type = spec.LED
            self.log = logging.getLogger(self.part_type.__tablename__)

            super().__init__(session)

    class Fuses(GenericPart):
        def __init__(self, session: sqlalchemy.orm.Session):
            self.table_item_spec = spec.eedata_fuse_spec
            self.table_item_display_order = spec.eedata_fuse_display_order
            self.part_type = spec.Fuse
            self.log = logging.getLogger(self.part_type.__tablename__)

            super().__init__(session)

    class Buttons(GenericPart):
        def __init__(self, session: sqlalchemy.orm.Session):
            self.table_item_spec = spec.eedata_button_spec
            self.table_item_display_order = spec.eedata_button_display_order
            self.part_type = spec.Button
            self.log = logging.getLogger(self.part_type.__tablename__)

            super().__init__(session)

    class MiscComps(GenericPart):
        def __init__(self, session: sqlalchemy.orm.Session):
            self.table_item_spec = spec.eedata_misc_spec
            self.table_item_display_order = spec.eedata_misc_display_order
            self.part_type = spec.MiscComp
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
        self.crystals = self.Crystals(sessionmaker(self.db_conn)())
        self.mosfets = self.MOSFETs(sessionmaker(self.db_conn)())
        self.bjts = self.BJTs(sessionmaker(self.db_conn)())
        self.connectors = self.Connectors(sessionmaker(self.db_conn)())
        self.leds = self.LEDs(sessionmaker(self.db_conn)())
        self.fuses = self.Fuses(sessionmaker(self.db_conn)())
        self.buttons = self.Buttons(sessionmaker(self.db_conn)())
        self.misc_cs = self.MiscComps(sessionmaker(self.db_conn)())
        self.pcbs = self.PCBs(sessionmaker(self.db_conn)())

        self.components = {
            'Resistors': self.resistors,
            'Capacitors': self.capacitors,
            'Inductors': self.inductors,
            'ICs': self.ics,
            'Diodes': self.diodes,
            'Crystals': self.crystals,
            'MOSFETs': self.mosfets,
            'BJTs': self.bjts,
            'Connectors': self.connectors,
            'LEDs': self.leds,
            'Fuses': self.fuses,
            'Buttons': self.buttons,
            'Misc': self.misc_cs,
        }

        spec.GenericItem.metadata.create_all(self.db_conn)
        spec.PCB.metadata.create_all(self.db_conn)

        # If the DB version is None (if the config table was just created), then populate the current version
        if self.config.get_db_version() is None:
            self.config.store_current_db_version()

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

    def check_if_already_in_db_by_manuf(self, mfr_part_numb: str) -> (None, int):
        for c in self.components:
            # temporary fix
            if c == 'PCBs':
                continue
            p = self.components[c].check_if_already_in_db_by_manuf(mfr_part_numb)
            if p is not None:
                return p, self.components[c]
        return None, None

    def wipe_database(self):
        """
            Wipes the component databases
        """
        for c in self.components.values():
            c.part_type.metadata.drop_all(self.db_conn)
            c.session.commit()
            # Recreate table
            c.part_type.metadata.create_all(self.db_conn)

    def update_database(self):
        """
            Updates the database to the most recent revision
        """
        with self.db_conn.connect() as conn:
            ctx = MigrationContext.configure(conn)
            op = Operations(ctx)
            self.log.info("Backing up database before applying changes")
            self.backup_db()
            v = self.config.get_db_version()
            if v == '0.2':   # From 0.2 -> 0.3
                for c in self.components:
                    op.add_column(self.components[c].table_name, Column('storage', String(spec.default_string_len)))
                    op.drop_column(self.components[c].table_name, 'part_comments')
                    op.alter_column(self.components[c].table_name, 'user_comments', new_column_name='comments', type_=Text)
                # Remove the capacitor's power column
                op.drop_column(self.components['Capacitors'].table_name, 'power')
                v = '0.3'
            if v == '0.3':
                # Add the datasheet column for each component
                for c in self.components:
                    op.add_column(self.components[c].table_name, Column('datasheet', Text))
                op.alter_column(self.pcbs.table_name, 'project_name', type_=String(spec.default_string_len), new_column_name='board_name')
                op.add_column(self.pcbs.table_name, Column('parts', JSON, nullable=False))
            self.config.store_current_db_version()

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
        new_db_file = os.path.dirname(os.path.abspath(__file__)) + '/partdb_backup_%s.json' % time.strftime('%y%m%d%H%M%S')
        self.log.info("Backing database under %s" % new_db_file)
        # https://stackoverflow.com/questions/47307873/read-entire-database-with-sqlalchemy-and-dump-as-json
        meta = sqlalchemy.MetaData()
        meta.reflect(bind=self.db_conn)  # http://docs.sqlalchemy.org/en/rel_0_9/core/reflection.html
        result = {}
        for table in meta.sorted_tables:
            result[table.name] = [dict(row) for row in self.db_conn.execute(table.select())]
        with open(new_db_file, 'x') as f:
            json.dump(result, f, indent=4)
