# -*- coding: utf-8 -*-
"""
gites.calendar

Licensed under the GPL license, see LICENCE.txt for more details.
Copyright by Affinitic sprl
"""
import grokcore.component as grok
from affinitic.zamqp.consumer import Consumer
from gites.calendar.zcml import parseZCML


class WalhebCalendarImportConsumer(Consumer):
    grok.name('booking.update')
    queue = "booking.update.fromwalhebcalendar"
    exchange = 'booking.update'
    exchange_type = 'direct'
    routing_key = 'gdw'
    connection_id = 'walhebcalendar'


def handleNewBookingFromWalhebCalendar(bookingInfo, msg):
    #XXX
    pass


def main():
    import gites.calendar.scripts
    parseZCML(gites.calendar.scripts, 'calendar_import.zcml')
    consumer = WalhebCalendarImportConsumer()
    consumer.connection
    consumer.backend
    consumer.register_callback(handleNewBookingFromWalhebCalendar)
    consumer.wait()
