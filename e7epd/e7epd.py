import dataclasses
import enum
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


class ComparisonOperators(enum.StrEnum):
    """ Comparison operators as an enum """
    equal = '=='
    less = '<'
    greater = '>'
    less_equal = '<='
    greater_equal = '>='


@dataclasses.dataclass
class SpecWithOperator:
    """ Dataclass for a specification with optional operators """
    key: str
    val: typing.Union[float, int, str]
    operator: ComparisonOperators = ComparisonOperators.equal


# Internal variable to convert comparison operators to Mongo ones
operator_to_mongo_comp = {
    ComparisonOperators.equal: '$eq',
    ComparisonOperators.less: '$lt',
    ComparisonOperators.greater: '$gt',
    ComparisonOperators.less_equal: '$lte',
    ComparisonOperators.greater_equal: '$gte',
}


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

    def set(self, key: str, value: typing.Any):
        d = self.coll.find_one_and_update({'key': key}, {'$set': {'val': value}})
        if d is None:
            self.coll.insert_one({'key': key, 'val': value})

    def save(self):
        # This does nothing. It's mostly here for compatibility with any set-get-save class callback
        pass

    def check_first_time(self):
        if self.get('first_time') is None:
            self.set('first_time', True)

    def get_db_version(self) -> typing.Union[str, None]:
        return self.get('db_ver')

    def store_current_db_version(self):
        self.set('db_ver', database_spec_rev)


class E7EPD:
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
            'resistor': spec.Resistor,
        }

        # If the DB version is None (if the config table was just created), then populate the current version
        if self.config.get_db_version() is None:
            self.config.store_current_db_version()

    def get_autocomplete_list(self, part_spec: spec.PartSpec, item_key: str) -> typing.Union[None, list]:
        """
        Gets a list of current data for autocomplete when asking for a spec

        Args:
            part_spec:
            item_key:

        Returns:

        """
        # todo: have the autofill helpers be stored and configurable in the database
        autocomplete_choices = None
        autofill_helpers = spec.autofill_helpers_list
        # if db_name == 'manufacturer' and table_name == 'ic':
        #     autocomplete_choices = autofill_helpers['ic_manufacturers']
        # if db_name == 'manufacturer' and table_name == 'resistor':
        #     autocomplete_choices = autofill_helpers['passive_manufacturers']
        # elif db_name == 'ic_type' and table_name == 'ic':
        #     autocomplete_choices = autofill_helpers['ic_types']
        # elif db_name == 'cap_type' and table_name == 'capacitor':
        #     autocomplete_choices = autofill_helpers['capacitor_types']
        # elif db_name == 'diode_type' and table_name == 'diode':
        #     autocomplete_choices = autofill_helpers['diode_type']
        # elif db_name == 'bjt_type' and table_name == 'bjt':
        #     autocomplete_choices = autofill_helpers['bjt_types']
        # elif db_name == 'mosfet_type' and table_name == 'mosfet':
        #     autocomplete_choices = autofill_helpers['mosfet_types']
        # elif db_name == 'led_type' and table_name == 'led':
        #     autocomplete_choices = autofill_helpers['led_types']
        # elif db_name == 'fuse_type' and table_name == 'fuse':
        #     autocomplete_choices = autofill_helpers['fuse_types']
        # # Package Auto-Helpers
        # elif db_name == 'package' and table_name == 'ic':
        #     autocomplete_choices = autofill_helpers['ic_packages']
        # elif db_name == 'package' and (table_name == 'resistor' or table_name == 'capacitor' or table_name == 'inductor'):
        #     autocomplete_choices = autofill_helpers['passive_packages']
        if item_key == 'ipn':
            autocomplete_choices = self.get_all_parts_by_keys(part_spec, 'ipn')
        elif item_key == 'package' and (part_spec in [spec.Resistor]):
            autocomplete_choices = autofill_helpers['passive_packages']

        return autocomplete_choices

    def add_new_pcb(self, pcb_data: dict):
        """
        Adds a new PCB to the database

        Args:
            pcb_data: The PCB info to add to the database

        Raises:
            InputException: If the given `pcb_data` input has something invalid about it.
                            See specific exception message as to what

        """
        # Validate that all given keys are part of the spec, and the type matches
        for d in pcb_data:
            if d not in spec.PCBItems.keys():
                raise InputException(f"Given key of {d} is not part of the spec")
            if type(pcb_data[d]) not in [type(None), spec.PCBItems[d].input_type]:
                raise InputException(f"Input value of {pcb_data[d]} for {d} is not of "
                                     f"type {spec.PCBItems[d].input_type}. Instead is {type(pcb_data[d])}")
        # todo: add verification of parts
        # Check if all required keys are matched
        for d in spec.PCBItems:
            self._check_spec_required(d, spec.PCBItems[d], pcb_data)
            # if spec.PCBItems[d].required:
            #     if d not in pcb_data:
            #         raise InputException(f"Required key of {d} is not found in the new part dict")
        # Check for any duplicates
        if self.pcb_coll.count_documents({'id': pcb_data['id'], 'rev': pcb_data['rev']}) != 0:
            raise InputException("PCB ID already exists in the database")
        # Add part to DB
        self.pcb_coll.insert_one(pcb_data)

    def get_pcb(self, pcb_id: str = None, rev: str = None) -> dict:
        doc = self.pcb_coll.find_one({'id': pcb_id, 'rev': rev})
        return doc

    def get_all_unique_pcbs(self) -> typing.List[typing.Dict]:
        ret = []
        q = self.pcb_coll.find()
        for i in q:
            ret.append({'id': i['id'], 'rev': i['rev']})
        return ret

    def find_pcb_part(self, part: dict) -> typing.Union[None, typing.List[dict]]:
        part_type = part['type']
        part = part['part']
        if 'ipn' in part:
            p = self.get_part_by_ipn(part['ipn'])
            if p is not None:
                return [p]
        else:
            spec_search = []
            for k in part:
                spec_search.append(SpecWithOperator(key=k, val=part[k]['val'],
                                                    operator=ComparisonOperators(part[k]['op'])))
            return self.get_sorted_parts(self.comp_types[part_type], spec_search)
        return []

    def add_user(self, u: spec.UserSpec):
        # Do a check to ensure the same name does not exist
        co = self.users_coll.count_documents({'name': u.name})
        if co != 0:
            raise InputException("The user (by name) already exists in the database")
        self.users_coll.insert_one(dataclasses.asdict(u))

    def get_user_by_name(self, name: str) -> typing.Union[dict, None]:
        co = self.users_coll.find_one({'name': name})
        return co

    def get_all_users_name(self) -> typing.List[str]:
        co = self.users_coll.find({})
        return [i['name'] for i in co]

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

    def get_sorted_parts(self, part_class: typing.Union[spec.PartSpec],
                         to_filter: typing.List[SpecWithOperator]) -> typing.List[dict]:
        q = {}
        if part_class is not None:
            q['type'] = part_class.db_type_name
        # Go thru parts to filter
        for f in to_filter:
            if f.operator != ComparisonOperators.equal and type(f.val) is str:
                raise InputException("Gave some comparison operator while input is a string")
            if f.key not in part_class.items:
                raise InputException(f"Input key of {f.key} is not part of the part class's spec")
            q[f.key] = {operator_to_mongo_comp[f.operator]: f.val}

        d = self.part_coll.find(q)
        return list(d)

    def get_all_parts_by_keys(self, part_class: typing.Union[spec.PartSpec, None],
                              ret_key: typing.Union[str, list]) -> list:
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
            if type(ret_key) is list:
                ret.append({i: d_i[i] for i in ret_key})
            else:
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
            if type(new_part[d]) != part_class.items[d].input_type:
                raise InputException(f"Input value of {new_part[d]} for {d} is "
                                     f"not of type {part_class.items[d].input_type}")
        # Set type
        new_part['type'] = part_class.db_type_name
        # Check if all required keys are matched
        for d in part_class.items:
            self._check_spec_required(d, part_class.items[d], new_part)
            # if part_class.items[d].required:
            #     if d not in new_part:
            #         raise InputException(f"Required key of {d} is not found in the new part dict")
        # Add part to DB
        self.log.debug(f"Writing to database: {new_part}")
        self.part_coll.insert_one(new_part)

    def delete_part(self, part_class: spec.PartSpec, ipn: str):
        q = {'type': part_class.db_type_name, 'ipn': ipn}
        self.log.debug(f"Deleting: {q}")
        self.part_coll.delete_one(q)

    def update_part(self, part_class: typing.Union[spec.PartSpec, None], ipn: str, new_values: dict):
        """
        Updates a part with a certain type and IPN with some new values given as a dictionary

        Args:
            part_class: The part class to update. If given as None, then type checking on
                        new_values is not done (thus recommended!!)
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
                    raise InputException(f"Input value of {new_values[d]} for {d} is not "
                                         f"of type {part_class.items[d].input_type}")
        self.log.debug(f"Updating {q} with {new_values}")
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

    @staticmethod
    def _check_spec_required(spec_k: str, spec_i: spec.SpecLineItem, part_dict: dict):
        if spec_i.required:
            if spec_k not in part_dict:
                raise InputException(f"Required key of {d} is not found in the new part dict")


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
