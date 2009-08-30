# -*- coding: utf-8 -*-
"""
gites.calendar

Licensed under the GPL license, see LICENCE.txt for more details.
Copyright by Affinitic sprl

$Id: event.py 67630 2006-04-27 00:54:03Z jfroche $
"""
from five import grok
from gites.calendar.interfaces import IProprioCalendar
from zope.interface import Interface

grok.context(Interface)
grok.templatedir('templates')


class CalendarConfiguration(grok.View):
    """
    Configure calendar for proprio
    """
    grok.context(IProprioCalendar)
    grok.name('configuration')
    grok.require('zope2.View')
