# -*- coding: utf-8 -*-
"""
gites.calendar

Licensed under the GPL license, see LICENCE.txt for more details.
Copyright by Affinitic sprl
"""
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.orm import mapper
from zope.component import getUtility
import grokcore.component as grok
from affinitic.db.interfaces import IDatabase
from affinitic.zamqp.consumer import Consumer
from gites.db.tables import (getReservationProprio, getHebergementTable, getCommune,
                             getProvinces, getMaisonTourisme, getTypeHebergementTable,
                             getCharge, getProprio, getCivilite)
from gites.db.content import ReservationProprio, Hebergement
from gites.calendar.zcml import parseZCML


class WalhebCalendarImportConsumer(Consumer):
    grok.name('booking.update')
    queue = "booking.update.fromwalhebcalendar"
    exchange = 'booking.update'
    exchange_type = 'direct'
    routing_key = 'gdw'
    connection_id = 'walhebcalendar'


def setPGMappers(metadata, event):
    reservationProprioTable = getReservationProprio(metadata)
    getCommune(metadata)
    getProvinces(metadata)
    getMaisonTourisme(metadata)
    getCharge(metadata)
    getTypeHebergementTable(metadata)
    getCivilite(metadata)
    getProprio(metadata)
    mapper(ReservationProprio, reservationProprioTable)
    hebergementTable = getHebergementTable(metadata)
    mapper(Hebergement, hebergementTable)


def removeSelection(session, hebPk, start, end):
    subquery = select([ReservationProprio.res_id])
    subquery.append_whereclause(ReservationProprio.res_date.between(start,
                                                                    end))
    subquery.append_whereclause(ReservationProprio.heb_fk == hebPk)
    query = session.query(ReservationProprio)
    query = query.filter(ReservationProprio.res_id.in_(subquery))
    query.delete()


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
    consumer = WalhebCalendarImportConsumer()
    consumer.connection
    consumer.backend
    consumer.register_callback(handleNewBookingFromWalhebCalendar)
    consumer.wait()
