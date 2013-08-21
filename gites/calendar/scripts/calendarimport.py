# -*- coding: utf-8 -*-
"""
gites.calendar

Licensed under the GPL license, see LICENCE.txt for more details.
Copyright by Affinitic sprl
"""
from datetime import date, datetime, timedelta
from sqlalchemy import select
from zope.component import getUtility
import grokcore.component as grok
from affinitic.db.interfaces import IDatabase
from affinitic.zamqp.consumer import Consumer
from affinitic.db.utils import initialize_declarative_mappers, initialize_defered_mappers
from gites.db.content import ReservationProprio, Hebergement
from gites.db import DeclarativeBase
from gites.calendar.zcml import parseZCML


class WalhebCalendarImportConsumer(Consumer):
    grok.name('booking.update')
    queue = "booking.update.fromwalhebcalendar"
    exchange = 'booking.update'
    exchange_type = 'direct'
    routing_key = 'gdw'
    connection_id = 'walhebcalendar'


def removeSelection(session, hebPk, start, end):
    subquery = session.query(ReservationProprio.res_id)
    subquery = subquery.filter(ReservationProprio.res_date.between(start,
                                                                   end))
    subquery = subquery.filter(ReservationProprio.heb_fk == hebPk)
    resIds = subquery.all()
    if resIds:
        query = session.query(ReservationProprio)
        query.filter(ReservationProprio.res_id.in_(resIds)).delete(synchronize_session='fetch')


def updateLastUpdateDate(session, hebPk):
    query = session.query(Hebergement)
    query = query.filter(Hebergement.heb_pk == hebPk)
    query.update({"heb_calendrier_proprio_date_maj": date.today()},
                 synchronize_session=False)


def handleNewBookingFromWalhebCalendar(bookingInfo, msg):
    print bookingInfo
    db = getUtility(IDatabase, 'postgres')
    session = db.session
    query = select([Hebergement.heb_pk])
    query.append_whereclause(Hebergement.heb_code_cgt == bookingInfo.get('cgt_id'))
    result = query.execute().fetchone()
    if result is not None:
        hebPk = result.heb_pk
        currentdate = bookingInfo['start_date']
        end = bookingInfo['end_date']
        removeSelection(session, hebPk, currentdate, end)
        updateLastUpdateDate(session, hebPk)
        while currentdate <= end:
            reservation = ReservationProprio()
            if bookingInfo['booking_type'] == 'unavailable':
                reservation.res_type = 'indisp'
            elif bookingInfo['booking_type'] == 'available':
                break
            else:
                reservation.res_type = 'loue'
            reservation.res_date = currentdate
            reservation.heb_fk = hebPk
            reservation.res_date_cre = datetime.now()
            session.add(reservation)
            currentdate += timedelta(days=1)
        session.flush()
        session.commit()
    msg.ack()


def main():
    import gites.calendar.scripts
    parseZCML(gites.calendar.scripts, 'calendar_import.zcml')
    pg = getUtility(IDatabase, 'postgres')
    pg.session
    initialize_declarative_mappers(DeclarativeBase, pg.metadata)
    initialize_defered_mappers(pg.metadata)
    consumer = WalhebCalendarImportConsumer()
    consumer.connection
    consumer.backend
    consumer.register_callback(handleNewBookingFromWalhebCalendar)
    consumer.wait()
