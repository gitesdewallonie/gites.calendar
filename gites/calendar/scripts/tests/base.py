# -*- coding: utf-8 -*-
"""
gites.calendar

Licensed under the GPL license, see LICENCE.txt for more details.
Copyright by Affinitic sprl
"""
import unittest
from datetime import datetime
from sqlalchemy import create_engine

from gites.db.content import Proprio, Hebergement
from gites.calendar.scripts.pg import PGDB


class BaseTestCase(unittest.TestCase):

    def setUp(self):
        self.pg = PGDB('user', 'pwd', 'host', 0, 'dbname')
        self.pg.engine = create_engine('sqlite:///:memory:')
        self.pg.connect()
        self.pg.setMappers()

    def _fillDB(self):
        session = self.pg.session()

        # Propriétaires
        p1 = Proprio()
        p1.pro_pk = 1
        p1.pro_etat = True
        p1.pro_prenom1 = u'Jean'
        p1.pro_nom1 = u'Bon'
        p1.pro_email = u'jean@bon.au'
        p2 = Proprio()
        p2.pro_pk = 2
        p2.pro_etat = True
        p2.pro_prenom1 = u'Vero'
        p2.pro_nom1 = u'Nique'
        p2.pro_email = u'vero@nique.be'
        p3 = Proprio()
        p3.pro_pk = 3
        p3.pro_etat = True
        p3.pro_prenom1 = u'Paul'
        p3.pro_nom1 = u'Dugenou'
        p3.pro_email = u'paul@ici.be'
        p4 = Proprio()
        p4.pro_pk = 4
        p4.pro_etat = False
        p4.pro_prenom1 = u'Marc'
        p4.pro_nom1 = u'Moulin'
        p4.pro_email = u'moulin@retebe.be'
        session.add(p1)
        session.add(p2)
        session.add(p3)
        session.add(p4)
        session.flush()

        # Hébergements
        h1 = Hebergement()
        h1.heb_pk = 1
        h1.heb_pro_fk = 1
        h1.heb_site_public = True
        h1.heb_calendrier_proprio = 'actif'
        h1.heb_nom = 'Heb 1'
        h1.heb_calendrier_proprio_date_maj = datetime(2010, 1, 1)
        h2 = Hebergement()
        h2.heb_pk = 2
        h2.heb_pro_fk = 2
        h2.heb_site_public = False
        h2.heb_calendrier_proprio = 'actif'
        h2.heb_nom = 'Heb 2'
        h2.heb_calendrier_proprio_date_maj = datetime(2010, 2, 2)
        h3 = Hebergement()
        h3.heb_pk = 3
        h3.heb_pro_fk = 3
        h3.heb_site_public = True
        h3.heb_calendrier_proprio = 'searchactif'
        h3.heb_nom = 'Heb 3'
        h3.heb_calendrier_proprio_date_maj = datetime(2010, 1, 2)
        h4 = Hebergement()
        h4.heb_pk = 4
        h4.heb_pro_fk = 4
        h4.heb_site_public = True
        h4.heb_calendrier_proprio = 'non actif'
        h4.heb_nom = 'Heb 4'
        h4.heb_calendrier_proprio_date_maj = datetime(2010, 3, 2)
        h5 = Hebergement()
        h5.heb_pk = 5
        h5.heb_pro_fk = 4
        h5.heb_site_public = True
        h5.heb_calendrier_proprio = 'bloque'
        h5.heb_nom = 'Heb 5'
        h5.heb_calendrier_proprio_date_maj = datetime(2010, 3, 2)
        session.add(h1)
        session.add(h2)
        session.add(h3)
        session.add(h4)
        session.add(h5)
        session.flush()

    def tearDown(self):
        self.pg.disconnect()
