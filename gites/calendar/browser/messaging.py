# -*- coding: utf-8 -*-
"""
gites.calendar

Licensed under the GPL license, see LICENCE.txt for more details.
Copyright by Affinitic sprl
"""
import os
import grokcore.component as grok
from affinitic.zamqp.connection import BrokerConnection
from affinitic.zamqp.publisher import Publisher


def getBrokerHost():
    return os.environ.get('AMQP_BROKER_HOST', 'gauss.interne.affinitic.be')


class WalhebCalendarConnection(BrokerConnection):
    grok.name("walhebcalendar")
    virtual_host = "/walhebcalendar"
    hostname = getBrokerHost()
    port = 5672
    userid = "gdw"
    password = "tototo"


class GitesWalhebcalendarPublisher(Publisher):
    grok.name('walhebcalendar.gdw')
    connection_id = 'walhebcalendar'
    exchange = 'booking.update.gdw'
    exchange_type = 'direct'
    routing_key = 'import'
    serializer = 'pickle'
