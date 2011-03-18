# -*- coding: utf-8 -*-
"""
gites.calendar

Licensed under the GPL license, see LICENCE.txt for more details.
Copyright by Affinitic sprl
"""
from zope.interface import Interface

class ICalendarUpdateEvent(Interface):
    """
    Marker interface for an update event on a calendar
    """
