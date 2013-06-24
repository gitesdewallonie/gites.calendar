# -*- coding: utf-8 -*-
"""
gites.calendar

Licensed under the GPL license, see LICENCE.txt for more details.
Copyright by Affinitic sprl
"""
import logging

from zope.interface import alsoProvides
from zope.component import getMultiAdapter

from plone.portlets.interfaces import IPortletAssignmentMapping

from p4a.subtyper.interfaces import ISubtyped
from dateable.chronos.interfaces import ICalendarEnhanced

from gites.core.utils import createFolder, createPage, getManager
from gites.calendar.portlets import calendarmenu
from gites.calendar.interfaces import IProprioCalendar

logger = logging.getLogger('gites.calendar')


def setupCalendar(calendarFolder):
    return


def setupPortletsInZoneMembre(folder):
    manager = getManager(folder, 'left')
    assignments = getMultiAdapter((folder, manager), IPortletAssignmentMapping)
    if 'calendarmenu' not in assignments:
        assignement = calendarmenu.Assignment('Calendrier')
        assignments['calendarmenu'] = assignement


def setupgites(context):
    if context.readDataFile('gites.calendar_various.txt') is None:
        return
    logger.debug('Setup gites calendar')
    portal = context.getSite()
    zoneMembreFolder = getattr(portal, 'zone-membre', None)
    if zoneMembreFolder is None:
        return
    setupPortletsInZoneMembre(zoneMembreFolder)
    createFolder(zoneMembreFolder, "calendrier", "Calendrier", True)
    calendrier = zoneMembreFolder.calendrier
    alsoProvides(calendrier, IProprioCalendar)
    alsoProvides(calendrier, ISubtyped)
    alsoProvides(calendrier, ICalendarEnhanced)
    createPage(calendrier, "transfert", "Transfert", True)
    createPage(calendrier, "aide", "Aide", True)
    setupCalendar(calendrier)
