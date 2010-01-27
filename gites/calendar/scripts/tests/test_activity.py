# -*- coding: utf-8 -*-
"""
gites.calendar

Licensed under the GPL license, see LICENCE.txt for more details.
Copyright by Affinitic sprl
"""
from datetime import datetime
from dateutil.relativedelta import relativedelta

from gites.db.content import ReservationProprio, Hebergement
from gites.calendar.scripts.activity import CalendarActivity
from gites.calendar.scripts.tests.base import BaseTestCase


class NotifyProprietairesTest(BaseTestCase):

    def setUp(self):
        super(NotifyProprietairesTest, self).setUp()
        self.checker = CalendarActivity(self.pg)
        self.checker.connect()
        def now():
            return datetime(2010, 1, 1)
        self.checker.now = now
        def sendMail(pk):
            print 'Sending fake mail ...'
        self.checker.sendFirstMail = sendMail
        self.checker.sendSecondMail = sendMail

    def tearDown(self):
        super(NotifyProprietairesTest, self).tearDown()

    def testLastReservation(self):
        self._fillDB()
        calendars = self.checker.getActiveCalendars()
        self.assertEqual(len(calendars), 2)
        cal1 = calendars[0]
        self.assertEqual(cal1.max_1, datetime(2010, 2, 2))

    def testOneMonthDelay(self):
        self._fillDB()
        session = self.checker.pg.session()
        query = session.query(ReservationProprio)
        query = query.filter(ReservationProprio.res_id == 3)
        res = query.one()
        res.res_date_cre = self.checker.now() + relativedelta(days=-29)
        session.add(res)
        session.flush()
        calendars = self.checker.getActiveCalendars()
        cal2 = calendars[1]
        self.failIf(self.checker.mustBeNotified(cal2))

        notified, blocked = self.checker.checkCalendarActivity()
        self.assertEqual(len(notified), 0)
        self.assertEqual(len(blocked), 0)

        query = session.query(ReservationProprio)
        query = query.filter(ReservationProprio.res_id == 3)
        res = query.one()
        res.res_date_cre = self.checker.now() + relativedelta(days=-30)
        session.add(res)
        session.flush()
        calendars = self.checker.getActiveCalendars()
        cal2 = calendars[1]
        self.failUnless(self.checker.mustBeNotified(cal2))

        notified, blocked = self.checker.checkCalendarActivity()
        self.assertEqual(len(notified), 1)
        self.assertEqual(len(blocked), 0)

        query = session.query(ReservationProprio)
        query = query.filter(ReservationProprio.res_id == 3)
        res = query.one()
        res.res_date_cre = self.checker.now() + relativedelta(days=-31)
        session.add(res)
        session.flush()
        calendars = self.checker.getActiveCalendars()
        cal2 = calendars[1]
        self.failIf(self.checker.mustBeNotified(cal2))

        notified, blocked = self.checker.checkCalendarActivity()
        self.assertEqual(len(notified), 0)
        self.assertEqual(len(blocked), 0)

    def testCalendarBlocking(self):
        self._fillDB()
        session = self.checker.pg.session()
        query = session.query(ReservationProprio)
        query = query.filter(ReservationProprio.res_id == 3)
        res = query.one()
        res.res_date_cre = self.checker.now() + relativedelta(days=-40)
        session.add(res)
        session.flush()
        calendars = self.checker.getActiveCalendars()
        cal2 = calendars[1]
        self.failUnless(self.checker.mustBeBlocked(cal2))

        query = session.query(Hebergement)
        query = query.filter(Hebergement.heb_pk == 3)
        heb = query.one()
        self.assertEqual(heb.heb_calendrier_proprio, 'searchactif')

        notified, blocked = self.checker.checkCalendarActivity()
        self.assertEqual(len(notified), 0)
        self.assertEqual(len(blocked), 1)

        session = self.checker.pg.session()
        query = session.query(Hebergement)
        query = query.filter(Hebergement.heb_pk == 3)
        heb = query.one()
        self.assertEqual(heb.heb_calendrier_proprio, 'bloque')


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(NotifyProprietairesTest))
    return suite
