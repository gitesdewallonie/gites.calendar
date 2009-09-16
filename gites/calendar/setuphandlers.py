# -*- coding: utf-8 -*-
"""
gites.calendar

Licensed under the GPL license, see LICENCE.txt for more details.
Copyright by Affinitic sprl

$Id: event.py 67630 2006-04-27 00:54:03Z jfroche $
"""
from zope.interface import alsoProvides
from gites.core.utils import (createFolder, createPage, getManager)
from gites.calendar.interfaces import IProprioCalendar
from zope.component import getUtility, getMultiAdapter
from p4a.subtyper.interfaces import ISubtyper
from plone.portlets.interfaces import IPortletAssignmentMapping
import logging
from gites.calendar.portlets import calendarmenu
logger = logging.getLogger('gites.calendar')


def setupCalendar(calendarFolder):

    subtyper = getUtility(ISubtyper)
    existing = subtyper.existing_type(calendarFolder)
    if existing is None or existing.name != 'p4a.plonecalendar.FolderCalendar':
        subtyper.change_type(calendarFolder, 'p4a.plonecalendar.FolderCalendar')


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
    zoneMembreFolder = getattr(portal, 'zone-membre')
    setupPortletsInZoneMembre(zoneMembreFolder)
    createFolder(zoneMembreFolder, "calendrier", "Calendrier", True)
    calendrier = zoneMembreFolder.calendrier
    alsoProvides(calendrier, IProprioCalendar)
    createPage(calendrier, "transfert", "Transfert", True)
    createPage(calendrier, "aide", "Aide", True)
    setupCalendar(calendrier)
