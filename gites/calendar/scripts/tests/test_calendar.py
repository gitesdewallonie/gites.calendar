# -*- coding: utf-8 -*-
"""
gites.calendar

Licensed under the GPL license, see LICENCE.txt for more details.
Copyright by Affinitic sprl
"""
from datetime import date, datetime
from gites.db.content import ReservationProprio
from gites.calendar.zcml import parseZCML
from gites.calendar.scripts.tests.base import BaseTestCase
from gites.calendar.scripts.calendar import ExportCalendarActivity

_BOOKINGS = []


def addBooking(event):
    _BOOKINGS.append(event.__dict__)


class ExportCalendarActivityTest(BaseTestCase):

    def setUp(self):
        super(ExportCalendarActivityTest, self).setUp()
        import gites.calendar.scripts
        parseZCML(gites.calendar.scripts, 'calendar_testing.zcml')
        self.exporter = ExportCalendarActivity(self.pg)
        self.exporter.connect()

    def _fillDB(self):
        super(ExportCalendarActivityTest, self)._fillDB()
        # reservations
        session = self.pg.session()
        res = ReservationProprio()
        res.res_date = date(2001, 1, 1)
        res.res_type = 'loue'
        res.heb_fk = 1
        session.add(res)
        res = ReservationProprio()
        res.res_date = date(2020, 1, 1)
        res.res_type = 'loue'
        res.heb_fk = 1
        session.add(res)
        res = ReservationProprio()
        res.res_date = date(2020, 1, 2)
        res.res_type = 'loue'
        res.heb_fk = 1
        session.add(res)
        res = ReservationProprio()
        res.res_date = date(2015, 1, 1)
        res.res_type = 'loue'
        res.heb_fk = 2
        session.add(res)
        session.flush()

    def testListReservations(self):
        self._fillDB()
        reservations = [i for i in self.exporter.listReservations()]
        self.assertEqual(len(reservations), 3)

    def testExport(self):
        self._fillDB()
        self.assertEqual(len(_BOOKINGS), 0)
        self.exporter.export()
        self.assertEqual(len(_BOOKINGS), 2)
        self.assertEqual(_BOOKINGS[0],
                         {'typeOfSelection': u'loue',
                          'start': datetime(2020, 1, 1, 0, 0),
                          'hebPk': 1,
                          'end': datetime(2020, 1, 2, 0, 0)})
        self.assertEqual(_BOOKINGS[1],
                         {'typeOfSelection': u'loue',
                          'start': datetime(2015, 1, 1, 0, 0),
                          'hebPk': 2,
                          'end': datetime(2015, 1, 1, 0, 0)})


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(ExportCalendarActivityTest))
    return suite
