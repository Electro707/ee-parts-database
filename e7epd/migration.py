"""
This file handles any revision migration stuff
This is only from rev 0.6 -> 0.7 and after, due to the major database changes
If you are running with a version <0.6, then migrate to 0.6 with the old e7epd module, then use this one to update
to 0.7
"""
import logging
import pkg_resources
import pymongo
import pymongo.database
try:
    import sqlalchemy
    import sqlalchemy.future
    from sqlalchemy import Column, Integer, Float, String, Text, JSON
    from sqlalchemy.orm import declarative_base
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import select
    from sqlalchemy.orm import DeclarativeBase
    # importing to see if mysqlclient exits, as it is used by sqlalchemy internally
    import MySQLdb
    # A safety check to ensure the right version of sqlAlchemy is loaded
    if not sqlalchemy.__version__.startswith("2."):
        raise ImportError(f"SQLAlchemy version is not 2.x.x, but is {sqlalchemy.__version__}")
except ImportError as e:
    old_sql_available = False
    logging.getLogger('e7epd.migration').debug(e)
else:
    old_sql_available = True

default_string_len = 30


class GenericItem(DeclarativeBase):
    mfr_part_numb = Column(String(default_string_len), nullable=False, primary_key=True, autoincrement=False)
    stock = Column(Integer, nullable=False)
    manufacturer = Column(String(default_string_len))
    storage = Column(String(default_string_len))
    package = Column(String(default_string_len))
    comments = Column(Text)
    datasheet = Column(Text)
    user = Column(String(default_string_len))

    sql_to_mong_mapping_gen = [
        ['mfr_part_numb', 'ipn'],
        ['mfr_part_numb', 'mfg_part_numb'],
        ['stock', 'stock'],
        ['manufacturer', 'manufacturer'],
        ['storage', 'storage'],
        ['package', 'package'],
        ['comments', 'comments'],
        ['datasheet', 'datasheet'],
        ['user', 'user'],
    ]


class Resistor(GenericItem):
    __tablename__ = 'resistance'

    resistance = Column(Float, nullable=False)
    tolerance = Column(Float)
    power = Column(Float)

    sql_to_mong_mapping = [
        ['resistance', 'resistance'],
        ['tolerance', 'tolerance'],
        ['power', 'power'],
    ]
    db_type = 'resistor'


class Capacitor(GenericItem):
    __tablename__ = 'capacitor'

    capacitance = Column(Float, nullable=False)
    tolerance = Column(Float)
    max_voltage = Column(Float)
    temp_coeff = Column(String(default_string_len))
    cap_type = Column(String(default_string_len))

    sql_to_mong_mapping = [
        ['capacitance', 'capacitance'],
        ['tolerance', 'tolerance'],
        ['max_voltage', 'max_voltage'],
        ['temp_coeff', 'temp_coeff'],
        ['cap_type', 'cap_type'],
    ]
    db_type = 'capacitor'


class Inductor(GenericItem):
    __tablename__ = 'inductor'

    inductance = Column(Float, nullable=False)
    tolerance = Column(Float)
    max_current = Column(Float)

    sql_to_mong_mapping = [
        ['inductance', 'inductance'],
        ['tolerance', 'tolerance'],
        ['max_current', 'max_current'],
    ]
    db_type = 'inductor'


class Diode(GenericItem):
    __tablename__ = 'diode'

    diode_type = Column(String(default_string_len), nullable=False)
    max_current = Column(Float)
    average_current = Column(Float)
    max_rv = Column(Float)

    sql_to_mong_mapping = [
        ['diode_type', 'diode_type'],
        ['max_current', 'max_current'],
        ['average_current', 'average_current'],
        ['max_rv', 'max_rv'],
    ]
    db_type = 'diode'


class IC(GenericItem):
    __tablename__ = 'ic'

    ic_type = Column(String(default_string_len), nullable=False)

    sql_to_mong_mapping = [
        ['ic_type', 'ic_type'],
    ]
    db_type = 'ic'


class Crystal(GenericItem):
    __tablename__ = 'crystal'

    frequency = Column(Float, nullable=False)
    load_c = Column(Float)
    esr = Column(Float)
    stability_ppm = Column(Float)

    sql_to_mong_mapping = [
        ['frequency', 'frequency'],
        ['load_c', 'load_c'],
        ['esr', 'esr'],
        ['stability_ppm', 'stability'],
    ]
    db_type = 'crystal'


class MOSFET(GenericItem):
    __tablename__ = 'mosfet'

    mosfet_type = Column(String(default_string_len), nullable=False)
    vdss = Column(Float)
    vgss = Column(Float)
    vgs_th = Column(Float)
    i_d = Column(Float)
    i_d_pulse = Column(Float)

    sql_to_mong_mapping = [
        ['mosfet_type', 'fet_type'],
        ['vdss', 'vds'],
        ['vgss', 'vgs'],
        ['vgs_th', 'vgs_th'],
        ['i_d', 'i_d'],
        ['i_d_pulse', 'i_d_pulse'],
    ]
    db_type = 'fet'


class BJT(GenericItem):
    __tablename__ = 'bjt'

    bjt_type = Column(String(default_string_len), nullable=False)
    vcbo = Column(Float)
    vceo = Column(Float)
    vebo = Column(Float)
    i_c = Column(Float)
    i_c_peak = Column(Float)

    sql_to_mong_mapping = [
        ['bjt_type', 'bjt_type'],
        ['vcbo', 'vcb'],
        ['vceo', 'vce'],
        ['vebo', 'veb'],
        ['i_c', 'i_c'],
        ['i_c_peak', 'i_c_peak'],
    ]
    db_type = 'bjt'


class LED(GenericItem):
    __tablename__ = 'led'

    led_type = Column(String(default_string_len), nullable=False)
    vf = Column(Float)
    max_i = Column(Float)

    sql_to_mong_mapping = [
        ['led_type', 'led_type'],
        ['vf', 'vf'],
        ['max_i', 'max_i'],
    ]
    new_keys = ['color']
    db_type = 'led'


class Fuse(GenericItem):
    __tablename__ = 'fuse'

    fuse_type = Column(String(default_string_len), nullable=False)
    max_v = Column(Float)
    max_i = Column(Float)
    trip_i = Column(Float)
    hold_i = Column(Float)

    sql_to_mong_mapping = [
        ['fuse_type', 'fuse_type'],
        ['max_v', 'max_v'],
        ['max_i', 'max_i'],
        ['trip_i', 'trip_i'],
        ['hold_i', 'hold_i'],
    ]
    db_type = 'fuse'


class Connector(GenericItem):
    __tablename__ = 'connector'

    conn_type = Column(String(default_string_len), nullable=False)

    sql_to_mong_mapping = [
        ['conn_type', 'conn_type'],
    ]
    db_type = 'conn'


class Button(GenericItem):
    __tablename__ = 'button'

    bt_type = Column(String(default_string_len), nullable=False)
    circuit_t = Column(String(default_string_len))
    max_v = Column(Float)
    max_i = Column(Float)

    sql_to_mong_mapping = [
        ['bt_type', 'bt_type'],
        ['circuit_t', 'circuit_t'],
        ['max_v', 'max_v'],
        ['max_i', 'max_i'],
    ]
    db_type = 'sw_bw'


class MiscComp(GenericItem):
    __tablename__ = 'misc_c'

    sql_to_mong_mapping = [
    ]
    db_type = None


all_components = [Resistor, Capacitor, Inductor, Diode, IC, Crystal, MOSFET, BJT, LED, Fuse, Connector, Button, MiscComp]


def update_06_to_07(mongo_conn: pymongo.database.Database, sql_info: dict):
    """
    Updates the database to the most recent revision
    """
    if not old_sql_available:
        raise UserWarning("Cannot upgrade: sqlalchamy dependency is un-met")

    log = logging.getLogger('e7epd.migration')

    if sql_info['type'] == 'local':
        sql_conn = sqlalchemy.create_engine("sqlite:///{}".format(pkg_resources.resource_filename(__name__, 'data/' + sql_info['filename'])))
    elif sql_info['type'] == 'mysql_server':
        sql_conn = sqlalchemy.create_engine("mysql://{}:{}@{}/{}".format(sql_info['username'],
                                                                     sql_info['password'],
                                                                     sql_info['db_host'],
                                                                     sql_info['db_name']))
    elif sql_info['type'] == 'postgress_server':
        sql_conn = sqlalchemy.create_engine("postgresql://{}:{}@{}/{}".format(sql_info['username'],
                                                                          sql_info['password'],
                                                                          sql_info['db_host'],
                                                                          sql_info['db_name']))
    else:
        raise UserWarning("Invalid db_type")

    all_new_parts = []
    with sql_conn.connect() as conn:
        for comp in all_components:
            stmt = select(comp)
            for row in conn.execute(stmt):
                new_part = {'type': comp.db_type}
                for i in comp.sql_to_mong_mapping_gen:
                    new_part[i[1]] = getattr(row, i[0])
                for i in comp.sql_to_mong_mapping:
                    new_part[i[1]] = getattr(row, i[0])
                if hasattr(comp, 'new_keys'):
                    for k in comp.new_keys:
                        new_part[k] = None
                log.debug(f"New part: {new_part}")
                all_new_parts.append(new_part)

    # return

    coll = mongo_conn['parts']
    coll.insert_many(all_new_parts)
    log.info("Done with migration!")
