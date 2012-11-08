# -*- coding: utf-8 -*-
"""
gites.calendar

Licensed under the GPL license, see LICENCE.txt for more details.
Copyright by Affinitic sprl
"""
from datetime import date
from dateutil.relativedelta import relativedelta

from gites.db.content import Hebergement
from gites.calendar.scripts.activity import CalendarActivity
from gites.calendar.scripts.tests.base import BaseTestCase


class NotifyProprietairesTest(BaseTestCase):

    def setUp(self):
        super(NotifyProprietairesTest, self).setUp()
        self.checker = CalendarActivity(self.pg)
        self.checker.connect()
        def now():
            return date(2010, 1, 1)
        self.checker.now = now
        def sendMail(pk, majDate):
            pass
        self.checker.sendFirstMail = sendMail
        self.checker.sendSecondMail = sendMail

    def tearDown(self):
        super(NotifyProprietairesTest, self).tearDown()

    def testLastUpdate(self):
        self._fillDB()
        calendars = self.checker.getActiveCalendars()
        self.assertEqual(len(calendars), 2)
        cal1 = calendars[0]
        self.assertEqual(cal1.heb_calendrier_proprio_date_maj, \
                         date(2010, 1, 1))
        cal1 = calendars[1]
        self.assertEqual(cal1.heb_calendrier_proprio_date_maj, \
                         date(2010, 1, 2))

    def testOneMonthDelay(self):
        self._fillDB()
        session = self.checker.pg.session()
        query = session.query(Hebergement)
        query = query.filter(Hebergement.heb_pk == 3)
        heb = query.one()
        heb.heb_calendrier_proprio_date_maj = self.checker.now() + relativedelta(days=-29)
        session.add(heb)
        session.flush()
        calendars = self.checker.getActiveCalendars()
        cal2 = calendars[1]
        self.failIf(self.checker.mustBeNotified(cal2))

        notified, blocked = self.checker.checkCalendarActivity()
        self.assertEqual(len(notified), 0)
        self.assertEqual(len(blocked), 0)

        query = session.query(Hebergement)
        query = query.filter(Hebergement.heb_pk == 3)
        heb = query.one()
        heb.heb_calendrier_proprio_date_maj = self.checker.now() + relativedelta(days=-30)
        session.add(heb)
        session.flush()
        calendars = self.checker.getActiveCalendars()
        cal2 = calendars[1]
        self.failUnless(self.checker.mustBeNotified(cal2))

        notified, blocked = self.checker.checkCalendarActivity()
        self.assertEqual(len(notified), 1)
        self.assertEqual(len(blocked), 0)

        query = session.query(Hebergement)
        query = query.filter(Hebergement.heb_pk == 3)
        heb = query.one()
        heb.heb_calendrier_proprio_date_maj = self.checker.now() + relativedelta(days=-31)
        session.add(heb)
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
        query = session.query(Hebergement)
        query = query.filter(Hebergement.heb_pk == 3)
        heb = query.one()
        heb.heb_calendrier_proprio_date_maj = self.checker.now() + relativedelta(days=-40)
        session.add(heb)
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
