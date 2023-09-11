"""
This file handles any revision migration stuff
This is only from rev 0.6 -> 0.7 and after, due to the major database changes
If you are running with a version <0.6, then migrate to 0.6 with the old e7epd module, then use this one to update
to 0.7
"""
import logging

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
except ImportError:
    old_sql_available = False
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


class Inductor(GenericItem):
    __tablename__ = 'inductor'

    inductance = Column(Float, nullable=False)
    tolerance = Column(Float)
    max_current = Column(Float)


class Diode(GenericItem):
    __tablename__ = 'diode'

    diode_type = Column(String(default_string_len), nullable=False)
    max_current = Column(Float)
    average_current = Column(Float)
    max_rv = Column(Float)


class IC(GenericItem):
    __tablename__ = 'ic'

    ic_type = Column(String(default_string_len), nullable=False)


class Crystal(GenericItem):
    __tablename__ = 'crystal'

    frequency = Column(Float, nullable=False)
    load_c = Column(Float)
    esr = Column(Float)
    stability_ppm = Column(Float)


class MOSFET(GenericItem):
    __tablename__ = 'mosfet'

    mosfet_type = Column(String(default_string_len), nullable=False)
    vdss = Column(Float)
    vgss = Column(Float)
    vgs_th = Column(Float)
    i_d = Column(Float)
    i_d_pulse = Column(Float)


class BJT(GenericItem):
    __tablename__ = 'bjt'

    bjt_type = Column(String(default_string_len), nullable=False)
    vcbo = Column(Float)
    vceo = Column(Float)
    vebo = Column(Float)
    i_c = Column(Float)
    i_c_peak = Column(Float)


class LED(GenericItem):
    __tablename__ = 'led'

    led_type = Column(String(default_string_len), nullable=False)
    vf = Column(Float)
    max_i = Column(Float)


class Fuse(GenericItem):
    __tablename__ = 'fuse'

    fuse_type = Column(String(default_string_len), nullable=False)
    max_v = Column(Float)
    max_i = Column(Float)
    trip_i = Column(Float)
    hold_i = Column(Float)


class Connector(GenericItem):
    __tablename__ = 'connector'

    conn_type = Column(String(default_string_len), nullable=False)


class Button(GenericItem):
    __tablename__ = 'button'

    bt_type = Column(String(default_string_len), nullable=False)
    circuit_t = Column(String(default_string_len))
    max_v = Column(Float)
    max_i = Column(Float)


class MiscComp(GenericItem):
    __tablename__ = 'misc_c'


all_components = [Resistor]

def update_06_to_07(parts_collection: pymongo.database.Collection, sql_conn: sqlalchemy.future.Engine):
    """
    Updates the database to the most recent revision
    """

    with sql_conn.connect() as conn:
        stmt = select(Resistor)
        for row in conn.execute(stmt):
            new_part = {'type': Resistor.db_type}
            for i in Resistor.sql_to_mong_mapping_gen:
                new_part[i[1]] = getattr(row, i[0])
            print(new_part)

