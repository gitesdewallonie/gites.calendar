# -*- coding: utf-8 -*-
"""
gites.calendar

Licensed under the GPL license, see LICENCE.txt for more details.
Copyright by Affinitic sprl
"""
from sqlalchemy import create_engine
from sqlalchemy import MetaData
from sqlalchemy.orm import clear_mappers, create_session

from gites.db.initializer import GitesModel


class PGDB(object):

    def __init__(self, db_user, db_passwd, pg_host, pg_port, db_name):
        self.pg_string = 'postgres://%s:%s@%s:%s/%s' % (db_user, db_passwd,
                                                        pg_host, pg_port,
                                                        db_name)
        self.engine = create_engine(self.pg_string)

    def connect(self):
        self.db = self.engine.connect()
        self.metadata = MetaData(self.engine)

    def setMappers(self):
        model = GitesModel()
        mappers = model.getModel(self.metadata)

    def session(self):
        return create_session(bind=self.engine)

    def clearSession(self, session):
        session.flush()

    def disconnect(self):
        clear_mappers()
        self.db.close()
        del self.db
        del self.engine
