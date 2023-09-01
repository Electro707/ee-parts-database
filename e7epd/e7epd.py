import dataclasses
import logging
import json
import os
import time
import pymongo
import pymongo.database
from engineering_notation import EngNumber
import typing

import e7epd.e707pd_spec as spec

# Version of the database spec
database_spec_rev = '0.7.0-dev'

# A safety check to ensure the right version of sqlAlchemy is loaded
# if sqlalchemy.__version__ != "1.4.0":
#     raise ImportError(f"SQLAlchemy version is not 1.4.0, but is {sqlalchemy.__version__}")

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

class E7EPDConfigTable:
    """
    A generic configuration table. Currently, this is only used to store a db_ver key

    This creates a table (`e7epd_config`) with a key-value style data scheme.
    """
    def __init__(self, db_conn: pymongo.database.Database):
        self.log = logging.getLogger('config')
        self.coll = db_conn['e7epd_config']

    def get(self, key: str) -> typing.Union[str, None]:
        d = self.coll.find_one({'key': key})
        if d is None:
            return None
        else:
            return d['val']

    def set(self, key: str, value: str):
        d = self.coll.find_one_and_update({'key': key}, {'$set': {'val': value}})
        if d is None:
            self.coll.insert_one({'key': key, 'val': value})

    def save(self):
        # This does nothing. It's mostly here for compatibility with any set-get-save class callback
        pass

    def get_db_version(self) -> typing.Union[str, None]:
        return self.get('db_ver')

    def store_current_db_version(self):
        self.set('db_ver', database_spec_rev)

class E7EPD:
    class GenericComponent:  # todo: this is only here to have the cli run due to many typehints. remove at will
        pass

    # class GenericItem(typing.Generic[ComponentTypeVar]):
    #     """ This is a generic part constructor, which other components (like Resistors) will base off of """
    #     def __init__(self, session: sqlalchemy.orm.Session):
    #         self.session = session
    #         self.table_item_spec: list
    #         self.table_item_display_order: list
    #         self.part_type: ComponentTypeVar
    #
    #         if not hasattr(self, 'table_item_spec'):
    #             self.table_item_spec = None
    #         if not hasattr(self, 'table_item_display_order'):
    #             self.table_item_display_order = None
    #         if not hasattr(self, 'part_type'):
    #             self.part_type = None
    #
    #         self.table_name = self.part_type.__tablename__
    #         self.log = logging.getLogger(self.part_type.__tablename__)
    #
    #     def create_part(self, part_info: ComponentTypeVar):
    #         """
    #             Function to create a part for the given info
    #
    #             Args:
    #                  part_info (GenericItem): The part item class to add to the database
    #         """
    #         # Check if key already exists in table
    #         for item in self.table_item_spec:
    #             if item['required'] is True:
    #                 if getattr(part_info, item['db_name']) is None:
    #                     raise InputException("Did not assign key %s, but it's required" % item['db_name'])
    #         # Create a new part inside the database
    #         self._insert_part_in_db(part_info)
    #
    #     def _insert_part_in_db(self, part_info: ComponentTypeVar):
    #         """ Internal function to insert a part into the database """
    #         # Run an insert command into the database
    #         self.log.debug('Inserting %s into database' % part_info)
    #         self.session.add(part_info)
    #         self.session.commit()
    #
    #     # def append_stock_by_manufacturer_part_number(self, mfr_part_numb: str, append_by: int) -> int:
    #     #     """ Appends stock to a part by the manufacturer part number
    #     #
    #     #     Args:
    #     #         mfr_part_numb (str): The manufacturer number to add the stock to
    #     #         append_by: How much stock to add
    #     #
    #     #     Returns:
    #     #         The new stock of the part after the appending
    #     #
    #     #     Raises:
    #     #         EmptyInDatabase: Raises this if the manufacturer part number does not exist in the database
    #     #     """
    #     #     part = self.get_part_by_mfr_part_numb(mfr_part_numb)
    #     #     part.stock += append_by
    #     #     self.session.commit()
    #     #     return part.stock
    #
    #     # Deprecated as it should be done thru a returned querry then substracting the amount there
    #     # def remove_stock_by_manufacturer_part_number(self, mfr_part_numb: str, remove_by: int) -> int:
    #     #     """ Removes stock from a part by the manufacturer part number
    #     #
    #     #     Args:
    #     #         mfr_part_numb (str): The manufacturer number to add the stock to
    #     #         remove_by: How much stock to remove from the part
    #     #
    #     #     Returns:
    #     #         The new stock of the part after removal
    #     #
    #     #     Raises:
    #     #         EmptyInDatabase: Raises this if the manufacturer part number does not exist in the database
    #     #     """
    #     #     part = self.get_part_by_mfr_part_numb(mfr_part_numb)
    #     #     if part.stock - remove_by < 0:
    #     #         raise NegativeStock(part.stock)
    #     #     part.stock -= remove_by
    #     #     self.session.commit()
    #     #     return part.stock
    #
    #     def get_all_parts(self) -> typing.Iterable[ComponentTypeVar]:
    #         """ Get all parts in the database
    #
    #             Returns:
    #                 EmptyInDatabase: Raises this if the manufacturer part number does not exist in the database
    #         """
    #         return self.session.query(self.part_type).all()
    #
    #     def is_database_empty(self):
    #         """ Checks if the database is empty
    #
    #         Returns:
    #             True if the database is empty, False if not
    #         """
    #         d = self.session.query(self.part_type).count()
    #         self.log.debug('Number of parts in database for %s: %s' % (self.table_name, d))
    #         if d == 0:
    #             return True
    #         return False
    #
    #     def commit(self):
    #         """
    #             Commits any changes done to part(s)
    #         """
    #         self.session.commit()
    #
    #     def rollback(self):
    #         """
    #             Roll back changes done to part(s)
    #         """
    #         self.session.rollback()
    #
    # class GenericComponent(GenericItem[ComponentTypeVar]):
    #     def get_all_mfr_part_numb_in_db(self) -> list:
    #         """ Get all manufaturer part numbers as a list
    #
    #         Returns:
    #             A list of all manufacturer part numbers in the database
    #         """
    #         d = self.session.query(self.part_type).with_entities(self.part_type.mfr_part_numb).all()
    #         return [p.mfr_part_numb for p in d]
    #
    #     def get_sorted_parts(self, search_filter: list):
    #         q = self.session.query(self.part_type)
    #
    #         if q.count() == 0:
    #             raise EmptyInDatabase()
    #
    #         filter_const = []
    #         for item in search_filter:
    #             if 'op' in item:
    #                 if item['op'] == '>':
    #                     filter_const.append(getattr(self.part_type, item['db_name']) > item['val'])
    #                 elif item['op'] == '>=':
    #                     filter_const.append(getattr(self.part_type, item['db_name']) >= item['val'])
    #                 elif item['op'] == '<':
    #                     filter_const.append(getattr(self.part_type, item['db_name']) < item['val'])
    #                 elif item['op'] == '<=':
    #                     filter_const.append(getattr(self.part_type, item['db_name']) <= item['val'])
    #                 elif item['op'] == '==':
    #                     filter_const.append(getattr(self.part_type, item['db_name']) == item['val'])
    #                 else:
    #                     raise UserWarning("Invalid Operator %s" % item['op'])
    #             else:
    #                 filter_const.append(getattr(self.part_type, item['db_name']) == item['val'])
    #
    #         d = q.filter(*filter_const).all()
    #         return d
    #
    #     def get_part_by_mfr_part_numb(self, mfr_part_numb: str) -> ComponentTypeVar:
    #         """
    #             Function that returns parts parameters by part ID
    #
    #             Args:
    #                 mfr_part_numb (str): The part's manufacturer part number
    #
    #             Returns:
    #                 The part's item class
    #
    #             Raises:
    #                 EmptyInDatabase: If the SQL ID does not exist in the database
    #         """
    #         d = self.session.query(self.part_type).filter_by(mfr_part_numb=mfr_part_numb).one()
    #         return d
    #
    #     def delete_part_by_mfr_number(self, mfr_part_numb: str):
    #         """
    #             Function to delete a part by the manufacturer part number
    #
    #             Args:
    #                 mfr_part_numb: The manufacturer part number of the part to delete
    #
    #             Raises:
    #                  EmptyInDatabase: Raises this exception if there is no part in the database with that manufacturer part number
    #         """
    #         self.log.debug("Deleting part %s" % mfr_part_numb)
    #         self.session.delete(self.get_part_by_mfr_part_numb(mfr_part_numb))
    #
    #     def check_if_already_in_db(self, part_info: ComponentTypeVar):
    #         """ Checks if a given part is already in the database
    #             Currently it's done through checking for a match with the manufacturer part number
    #
    #             Args:
    #                 part_info (GenericItem): A part item class
    #
    #             Raises:
    #                 UserWarning: This should NEVER be triggered unless something went terribly wrong or if you manually edited the database. If the former, please create an bug entry on the project's Github page with the traceback
    #                 InputException: If the manufacturer part number is None, this will get raised
    #         """
    #         return self.check_if_already_in_db_by_manuf(part_info.mfr_part_numb)
    #
    #     def check_if_already_in_db_by_manuf(self, mfr_part_numb: str) -> (None, int):
    #         """
    #             Function that checks if a part is already in the database. A generic part just goes by manufacturer
    #             part number, otherwise a component-specific callback needs to be added (to look up generic parts for
    #             example without a manufacturer part number)
    #
    #             Args:
    #                 mfr_part_numb (str): The manufacturer part number to look for.
    #
    #             Returns:
    #                 None if the part doesn't exist in the database, The SQL ID if it does
    #
    #             Raises:
    #                 UserWarning: This should NEVER be triggered unless something went terribly wrong or if you manually edited the database. If the former, please create an bug entry on the project's Github page with the traceback
    #                 InputException: If the manufacturer part number is None, this will get raised
    #         """
    #         if mfr_part_numb is not None:
    #             d = self.session.query(self.part_type).filter_by(mfr_part_numb=mfr_part_numb).all()
    #             if len(d) == 0:
    #                 return None
    #             elif len(d) == 1:
    #                 return d[0].id
    #             else:
    #                 raise UserWarning("There is more than 1 entry for a manufacturer part number")
    #         else:
    #             raise InputException("Did not give a manufacturer part number")

        # todo: re-implement this resistance printing function
        # @staticmethod
        # def print_formatted_from_spec(spec_dict: dict) -> str:
        #     def get_value_and_operator_from_spec(spec_name: str) -> [typing.Union[float, int, None], typing.Union[None, str]]:
        #         if spec_name not in spec_dict:
        #             return None, None
        #         if (spec_dict[spec_name]) == dict:
        #             return spec_dict[spec_name]['val'], spec_dict[spec_name]['op']
        #         else:
        #             return spec_dict[spec_name], None
        #     """
        #     Prints out a nice string depending on the given spec_list
        #
        #     Args:
        #         spec_list: A list of dictionary containing the spec list in the format of for example
        #                    [{'db_name': 'resistance': 'val': 1000}, {'db_name': 'tolerance': 'val': 0.1, 'op': '>'}].
        #                    The db_name of `resistance` is required
        #
        #     Returns: A nicely formatted string describing the resistor, in the example above it will return `A 1k resistor with >1% tolerance`
        #     """
        #     resistance, op = get_value_and_operator_from_spec('resistance')
        #     ret_str = "A {:} resistor".format(str(EngNumber(resistance)))
        #
        #     tolerance, op = get_value_and_operator_from_spec('tolerance')
        #     if tolerance is not None:
        #         ret_str += " with a "
        #         if op is not None:
        #             ret_str += op
        #         ret_str += "{:.1f}% tolerance".format(tolerance)
        #
        #     power, op = get_value_and_operator_from_spec('power')
        #     if power is not None:
        #         ret_str += " with "
        #         if op is not None:
        #             ret_str += op
        #         ret_str += "{:.1f}%".format(power)
        #         ret_str += "W capability"
        #
        #     return ret_str

    def __init__(self, db_client: pymongo.MongoClient):
        self.log = logging.getLogger('E7EPD')
        self.db_client = db_client              # Store the connection engine

        self.db = self.db_client['ee-parts-db']       # The database itself

        # The config table in the database
        self.config = E7EPDConfigTable(self.db)

        self.part_coll = self.db['parts']
        self.pcb_coll = self.db['pcbs']
        self.users_coll = self.db['user']

        # Constructor for available part types:
        self.comp_types = {     # type: typing.Dict[str, spec.PartSpec]
            'Resistor': spec.Resistor,
        }

        # If the DB version is None (if the config table was just created), then populate the current version
        if self.config.get_db_version() is None:
            self.config.store_current_db_version()

    def add_new_pcb(self, pcb_data: dict):
        # Validate that all given keys are part of the spec, and the type matches
        for d in pcb_data:
            if d not in spec.PCBItems.keys():
                raise InputException(f"Given key of {d} is not part of the spec")
            try:
                spec.PCBItems[d].input_type(pcb_data[d])
            except ValueError:
                raise InputException(f"Input value of {pcb_data[d]} for {d} is not of type {spec.PCBItems[d].input_type}")

        # Check if all required keys are matched
        for d in spec.PCBItems:
            if spec.PCBItems[d].required:
                if d not in pcb_data:
                    raise InputException(f"Required key of {d} is not found in the new part dict")
        # Add part to DB
        self.pcb_coll.insert_one(pcb_data)

    def add_user(self, u: spec.UserSpec):
        # Do a check to ensure the same name does not exist
        co = self.users_coll.count_documents({'name': u.name})
        if co != 0:
            raise InputException("The user (by name) already exists in the database")
        self.users_coll.insert_one(dataclasses.asdict(u))

    def get_user_by_name(self, name: str) -> typing.Union[dict, None]:
        co = self.users_coll.find_one({'name': name})
        return co

    def close(self):
        """
        Call this when exiting your program
        """
        pass

    def check_if_already_in_db_by_ipn(self, ipn: str) -> bool:
        """
        Checks if an ipn is already in the database

        Args:
            ipn: The internal part number to look for

        Returns: A tuple, the first index being the SQL ID, the second being the component GenericPart class of the part
        """
        if ipn is not None:
            d = self.part_coll.count_documents({'ipn': ipn})
            if d == 0:
                return False
            elif d == 1:
                return True
            else:
                raise UserWarning("There is more than 1 entry for a manufacturer part number")
        else:
            raise InputException("Did not give a manufacturer part number")

    def get_part_by_ipn(self, ipn: str) -> dict:
        """

        Args:
            ipn: The IPN to search for

        Returns: The part's info
        """
        d = self.part_coll.find_one({'ipn': ipn})
        return d

    def get_number_of_parts_in_db(self, part_class: spec.PartSpec) -> int:
        """
        Gets the number of parts in the database per given type
        Args:
            part_class: he part spec class, which is used to determine the type

        Returns: The number of documents in the database
        """
        if part_class.db_type_name is None:
            raise UserWarning("Invalid input part class")
        d = self.part_coll.count_documents({'type': part_class.db_type_name})
        return d

    def get_all_parts(self, part_class: typing.Union[spec.PartSpec, None]) -> typing.List[dict]:
        """
        Get all parts in the database , optionally filtering by the part type
        Args:
            part_class: The part spec class, which is used to determine the type

        Returns: A dist of all part's data of the specific type
        """
        q = {}
        if part_class is not None:
            q['type'] = part_class.db_type_name
        d = self.part_coll.find(q)
        return list(d)

    def get_all_parts_one_keys(self, part_class: typing.Union[spec.PartSpec, None], ret_key: str) -> list:
        """
        Returns all parts in the database, but filtered to only return one key
        Args:
            part_class: The part spec class, which is used to determine the type
            ret_key: The key to return

        Returns: A list of all part's value per the given key
        """
        ret = []
        d = self.get_all_parts(part_class)
        for d_i in d:
            ret.append(d_i[ret_key])
        return ret

    def add_new_part(self, part_class: spec.PartSpec, new_part: dict):
        """
        Adds a new part to the database
        Args:
            part_class: The part spec class, which is used to determine the type
            new_part: A dictionary storing all the values for the new part
        """
        # Validate that all given keys are part of the spec, and the type matches
        for d in new_part:
            if d not in part_class.items.keys():
                raise InputException(f"Given key of {d} is not part of the spec")
            try:
                part_class.items[d].input_type(new_part[d])
            except ValueError:
                raise InputException(f"Input value of {new_part[d]} for {d} is not of type {part_class.items[d].input_type}")
        # Set type
        new_part['type'] = part_class.db_type_name
        # Check if all required keys are matched
        for d in part_class.items:
            if part_class.items[d].required:
                if d not in new_part:
                    raise InputException(f"Required key of {d} is not found in the new part dict")
        # Add part to DB
        self.part_coll.insert_one(new_part)

    def delete_part(self, part_class: spec.PartSpec, ipn: str):
        self.part_coll.delete_one({'type': part_class.db_type_name, 'ipn': ipn})

    def update_part(self, part_class: typing.Union[spec.PartSpec, None], ipn: str, new_values: dict):
        """
        Updates a part with a certain type and IPN with some new values given as a dictionary

        Args:
            part_class: The part class to update. If given as None, then type checking on new_values is not done (thus recommended!!)
            ipn: The IPN of the part to update
            new_values: The new dictionary key-values to update the part with
        """
        q = {'ipn': ipn}
        if part_class is not None:
            q['type'] = part_class.db_type_name
            for d in new_values:
                if d not in part_class.items.keys():
                    raise InputException(f"Given key of {d} is not part of the spec")
                try:
                    part_class.items[d].input_type(new_values[d])
                except ValueError:
                    raise InputException(f"Input value of {new_values[d]} for {d} is not of type {part_class.items[d].input_type}")
        self.part_coll.find_one_and_update(q, {"$set": new_values})

    def update_part_stock(self, ipn: str, new_qty: int):
        """
        Function to purely update a part's stock

        Args:
            ipn: The IPN to update the part for
            new_qty: The new part quantity
        """
        self.update_part(None, ipn, {'stock': new_qty})
        # self.part_coll.find_one_and_update({'ipn': ipn}, {"$set": {'stock': new_qty}})

    def get_part_spec_by_db_name(self, db_name: str):
        for i in self.comp_types:
            if db_name == self.comp_types[i].db_type_name:
                return self.comp_types[i]
        raise InputException(f"Cannot find part type from db_name of {db_name}")

    def wipe_database(self):
        """
        Wipes the component databases

        .. warning::
            THIS IS A DANGEROUS FUNCTION. Only call if you are sure. No going back

        """
        self.part_coll.drop()

    def update_database(self):
        """
        Updates the database to the most recent revision

        todo: from 0.6 to 0.7, make an external migration script!
        """
        v = self.config.get_db_version()
        # note: no new version to upgrade to yet
        self.config.store_current_db_version()

        # def mydefault(context):
        #     return context.get_current_parameters()['name']
        #
        # with self.db_conn.connect() as conn:
        #     ctx = MigrationContext.configure(conn)
        #     op = Operations(ctx)
        #     self.log.info("Backing up database before applying changes")
        #     self.backup_db()
        #     v = self.config.get_db_version()
        #     if v == '0.2':   # From 0.2 -> 0.3
        #         for c in self.components:
        #             op.add_column(self.components[c].table_name, Column('storage', String(spec.default_string_len)))
        #             op.drop_column(self.components[c].table_name, 'part_comments')
        #             op.alter_column(self.components[c].table_name, 'user_comments', new_column_name='comments', type_=Text)
        #         # Remove the capacitor's power column
        #         op.drop_column(self.components['Capacitors'].table_name, 'power')
        #         v = '0.3'
        #     if v == '0.3':   # From 0.3 -> 0.4
        #         # Add the datasheet column for each component
        #         for c in self.components:
        #             op.add_column(self.components[c].table_name, Column('datasheet', Text))
        #         op.alter_column(self.pcbs.table_name, 'project_name', type_=String(spec.default_string_len), new_column_name='board_name')
        #         op.add_column(self.pcbs.table_name, Column('parts', JSON, nullable=False))
        #     if v == '0.4':
        #         for c in self.components:
        #             op.drop_column(self.components[c].table_name, 'id')
        #             op.create_primary_key(None, self.components[c].table_name, ['mfr_part_numb'])
        #             op.add_column(self.components[c].table_name, Column('user', String(spec.default_string_len)))
        #     if v == '0.5':
        #         for c in self.components:
        #             op.add_column(self.components[c].table_name, Column('ipn', String(spec.default_string_len), default=mydefault, nullable=False))
        #             # op.drop_constraint(self.components[c].table_name, 'mfr_part_numb', type_='primary')
        #             # op.create_primary_key(None, self.components[c].table_name, ['ipn'])

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
        # todo: this
        # new_db_file = os.path.dirname(os.path.abspath(__file__)) + '/partdb_backup_%s.json' % time.strftime('%y%m%d%H%M%S')
        # self.log.info("Backing database under %s" % new_db_file)
        # # https://stackoverflow.com/questions/47307873/read-entire-database-with-sqlalchemy-and-dump-as-json
        # meta = sqlalchemy.MetaData()
        # meta.reflect(bind=self.db_conn)  # http://docs.sqlalchemy.org/en/rel_0_9/core/reflection.html
        # result = {}
        # for table in meta.sorted_tables:
        #     result[table.name] = [dict(row) for row in self.db_conn.execute(table.select())]
        # with open(new_db_file, 'x') as f:
        #     json.dump(result, f, indent=4)


def print_formatted_from_spec(part_class: spec.PartSpec, part_data: dict) -> typing.Union[None, str]:
    """
    Prints out a nice string depending on the given part_class

    Args:

    Returns: A nicely formatted string describing the resistor, in the example above it will return `A 1k resistor with >1% tolerance`
    """
    ret_str = None
    if part_class is spec.Resistor:
        ret_str = f"A {str(EngNumber(part_data['resistance'])):s} resistor"

        tolerance = part_data['tolerance']
        if tolerance is not None:
            ret_str += " with a "
            ret_str += f"{tolerance:.1f}% tolerance"

        power = part_data['power']
        if power is not None:
            ret_str += f" with {power:.1f}%W capability"

    return ret_str
