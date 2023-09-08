"""
This file handles any revision migration stuff
This is only from rev 0.6 -> 0.7 and after, due to the major database changes
If you are running with a version <0.6, then migrate to 0.6 with the old e7epd module, then use this one to update
to 0.7
"""
import pymongo
try:
    from sqlalchemy import Column, Integer, Float, String, Text, JSON
    from sqlalchemy.orm import declarative_base
    from sqlalchemy.orm import sessionmaker
    from alembic.operations import Operations
except ImportError:
    old_sql_available = False
else:
    old_sql_available = True

class MigrationClass:
    def __init__(self):
        pass

    def update_database(self, current_db: str):
        """
        Updates the database to the most recent revision

        todo: from 0.6 to 0.7, make an external migration script!
        """
        def mydefault(context):
            return context.get_current_parameters()['name']

        with self.db_conn.connect() as conn:
            ctx = MigrationContext.configure(conn)
            op = Operations(ctx)
            self.log.info("Backing up database before applying changes")
            self.backup_db()
            v = current_db
            if v == '0.2':   # From 0.2 -> 0.3
                for c in self.components:
                    op.add_column(self.components[c].table_name, Column('storage', String(spec.default_string_len)))
                    op.drop_column(self.components[c].table_name, 'part_comments')
                    op.alter_column(self.components[c].table_name, 'user_comments', new_column_name='comments', type_=Text)
                # Remove the capacitor's power column
                op.drop_column(self.components['Capacitors'].table_name, 'power')
                v = '0.3'
            if v == '0.3':   # From 0.3 -> 0.4
                # Add the datasheet column for each component
                for c in self.components:
                    op.add_column(self.components[c].table_name, Column('datasheet', Text))
                op.alter_column(self.pcbs.table_name, 'project_name', type_=String(spec.default_string_len), new_column_name='board_name')
                op.add_column(self.pcbs.table_name, Column('parts', JSON, nullable=False))
            if v == '0.4':
                for c in self.components:
                    op.drop_column(self.components[c].table_name, 'id')
                    op.create_primary_key(None, self.components[c].table_name, ['mfr_part_numb'])
                    op.add_column(self.components[c].table_name, Column('user', String(spec.default_string_len)))
            if v == '0.5':
                for c in self.components:
                    op.add_column(self.components[c].table_name, Column('ipn', String(spec.default_string_len), default=mydefault, nullable=False))
                    # op.drop_constraint(self.components[c].table_name, 'mfr_part_numb', type_='primary')
                    # op.create_primary_key(None, self.components[c].table_name, ['ipn'])