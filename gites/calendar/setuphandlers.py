# -*- coding: utf-8 -*-
"""
gites.calendar

Licensed under the GPL license, see LICENCE.txt for more details.
Copyright by Affinitic sprl

$Id: event.py 67630 2006-04-27 00:54:03Z jfroche $
"""
from zope.interface import alsoProvides
from gites.core.utils import (setupClassicPortlet, createFolder)
from gites.calendar.interfaces import IProprioCalendar
import logging
logger = logging.getLogger('gites.calendar')


def setupPortletsInZoneMembre(folder):
    setupClassicPortlet(folder, 'portlet_gites_calendar', 'left')


def setupgites(context):
    if context.readDataFile('gites.calendar_various.txt') is None:
        return
    logger.debug('Setup gites skin')
    portal = context.getSite()
    zoneMembreFolder = getattr(portal, 'zone-membre')
    setupPortletsInZoneMembre(zoneMembreFolder)
    createFolder(zoneMembreFolder, "calendrier", "Calendrier", True)
    alsoProvides(zoneMembreFolder.calendrier, IProprioCalendar)
