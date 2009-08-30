# -*- coding: utf-8 -*-
"""
gites.calendar

Licensed under the GPL license, see LICENCE.txt for more details.
Copyright by Affinitic sprl

$Id: event.py 67630 2006-04-27 00:54:03Z jfroche $
"""
from gites.calendar.interfaces import IProprioCalendar
from p4a.plonecalendar.eventprovider import EventProviderBase
from zope.interface import implements
from zope.component import adapts
from dateable import kalends


class GitesCalendarEventProvider(EventProviderBase):
    implements(kalends.IEventProvider)
    adapts(IProprioCalendar)

    def getEvents(self, start=None, stop=None, **kw):
        return []


class GitesCalendarEventCreator(object):
    implements(kalends.IWebEventCreator)
    adapts(IProprioCalendar)

    def __init__(self, context):
        self.context = context

    def url(self, start=None, stop=None):
        """Returns a url to a page that can create an event.
        Optional start and stop times to pre-fill start and end of event.
        """
        if start:
            # if there is a start date, use it to initalize the new Event
            if not stop:
                stop = start
            start = start.strftime('%m/%d/%Y')
            stop = stop.strftime('%m/%d/%Y')
            return self.context.absolute_url() +\
                '/changedisponibilite?form.widgets.startDate=%s&form.widgets.endDate=%s' % \
                (start, stop)
        else:
            return self.context.absolute_url() +\
                '/changedisponibilite'

    def canCreate(self):
        """Test to know if the current user can create events"""
        return self.context.request.SESSION.get('cal-selected-heb') is not None
