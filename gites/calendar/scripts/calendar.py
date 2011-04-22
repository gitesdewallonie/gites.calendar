# -*- coding: utf-8 -*-
"""
gites.calendar

Licensed under the GPL license, see LICENCE.txt for more details.
Copyright by Affinitic sprl
"""
from datetime import date
from datetime import timedelta
from zope.event import notify
from gites.db.content import ReservationProprio
from gites.calendar.zcml import parseZCML
from gites.calendar.scripts.pg import PGDB
from gites.calendar.browser.calendar import CalendarUpdateEvent


class ExportCalendarActivity(object):

    def __init__(self, pg):
        self.pg = pg

    def connect(self):
        self.pg.connect()
        self.pg.setMappers()
        self.session = self.pg.session()

    def now(self):
        # Useful for tests
        return date.today()

    def listReservations(self):
        query = self.pg.session().query(ReservationProprio)
        query = query.filter(ReservationProprio.res_date >= self.now())
        return query

    def export(self):
        lastKey = None
        event = None
        for reservation in self.listReservations():
            newKey = (reservation.res_date, reservation.res_type, reservation.heb_fk)
            if lastKey is None or lastKey != newKey:
                if event is not None:
                    notify(event)
                event = CalendarUpdateEvent(reservation.heb_fk,
                                            reservation.res_date,
                                            reservation.res_date,
                                            reservation.res_type)
            else:
                event.end = reservation.res_date
            lastKey = (reservation.res_date + timedelta(days=1),
                       reservation.res_type,
                       reservation.heb_fk)
        notify(event)


def main():
    import gites.calendar.scripts
    parseZCML(gites.calendar.scripts, 'calendar.zcml')
    pg = PGDB('zope', 'zope', 'localhost', 5432, 'gites_wallons')
    exporter = ExportCalendarActivity(pg)
    exporter.connect()
    exporter.export()
