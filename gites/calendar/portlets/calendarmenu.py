# -*- coding: utf-8 -*-
"""
gites.calendar

Licensed under the GPL license, see LICENCE.txt for more details.
Copyright by Affinitic sprl

$Id: event.py 67630 2006-04-27 00:54:03Z jfroche $
"""
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from zope.interface import implements
from plone.app.portlets.portlets import base
from plone.portlets.interfaces import IPortletDataProvider
from zope import schema
from zope.formlib import form
from zope.component import getUtility
from zope.schema.interfaces import IVocabularyFactory
from plone.memoize.instance import memoize
from gites.calendar.vocabulary import getHebergementsForProprio
from z3c.sqlalchemy import getSAWrapper


class ICalendarMenuPortlet(IPortletDataProvider):
    """A portlet which renders a menu
    """

    title = schema.TextLine(title=u'Title',
                            description=u'The title of the menu',
                            required=True)


class Assignment(base.Assignment):
    """Portlet assignment.

    This is what is actually managed through the portlets UI and associated
    with columns.
    """
    implements(ICalendarMenuPortlet)

    def __init__(self, title=u'', menu_id=u''):
        self._title = title

    @property
    def title(self):
        return self._title


class Renderer(base.Renderer):
    """Portlet renderer.

    This is registered in configure.zcml. The referenced page template is
    rendered, and the implicit variable 'view' will refer to an instance
    of this class. Other methods can be added and referenced in the template.
    """

    render = ZopeTwoPageTemplateFile('templates/calendarmenu.pt')

    def title(self):
        return self.data.title

    @property
    def available(self):
        """By default, portlets are available
        """
        return len(self.getGitesForProprio()) > 0

    def hasActiveConfiguration(self):
        """
        Does the proprio activated the calendar ?
        """
        cal = self.request.get('form.widgets.calendarConfig')
        if cal is not None:
            if cal == ['non actif'] or cal == ['bloque']:
                return False
            else:
                return True
        wrapper = getSAWrapper('gites_wallons')
        session = wrapper.session
        for heb in getHebergementsForProprio(self.context, session):
            return (heb.heb_calendrier_proprio != 'non actif')

    def isBlocked(self):
        """
        See if proprio calendars are blocked (due to 40 days delay)
        """
        cal = self.request.get('form.widgets.calendarConfig')
        if cal is not None:
            return (cal == ['bloque'])
        wrapper = getSAWrapper('gites_wallons')
        session = wrapper.session
        for heb in getHebergementsForProprio(self.context, session):
            if heb.heb_calendrier_proprio == 'bloque':
                return True
        return False

    @memoize
    def getGitesForProprio(self):
        return getUtility(IVocabularyFactory, name='proprio.hebergements')(self.context)


class AddForm(base.AddForm):
    """Portlet add form.
    This is registered in configure.zcml. The form_fields variable tells
    zope.formlib which fields to display. The create() method actually
    constructs the assignment that is being added.
    """
    form_fields = form.Fields(ICalendarMenuPortlet)

    def create(self, data):
        return Assignment(title=data.get('title', u''))


class EditForm(base.EditForm):
    """Portlet edit form.
    This is registered with configure.zcml. The form_fields variable tells
    zope.formlib which fields to display.
    """
    form_fields = form.Fields(ICalendarMenuPortlet)
