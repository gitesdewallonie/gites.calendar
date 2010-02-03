# -*- coding: utf-8 -*-
"""
gites.calendar

Licensed under the GPL license, see LICENCE.txt for more details.
Copyright by Affinitic sprl

$Id: event.py 67630 2006-04-27 00:54:03Z jfroche $
"""
from datetime import date
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from five import grok
from gites.calendar.interfaces import IProprioCalendar
from z3c.form import field, button
from z3c.form.form import EditForm
from z3c.form import widget
from zope.interface import Interface
from zope.schema import Choice
from five.megrok import z3cform
from plone.z3cform.layout import FormWrapper
from Products.CMFCore.utils import getToolByName
from z3c.sqlalchemy import getSAWrapper
from gites.calendar.vocabulary import getHebergementsForProprio


class ICalendarConfiguration(Interface):

    calendarConfig = Choice(
        title=u"Utilisation du calendrier",
        description=u"Selectionner le type d'utilisation du calendrier",
        vocabulary='proprio.calendarconfig',
        required=True)


class MyCoolFormWrapper(FormWrapper):
    index = ViewPageTemplateFile('templates/selectheb.pt')


class CalendarConfigForm(z3cform.EditForm):
    fields = field.Fields(ICalendarConfiguration)
    label = u"Configurer votre calendrier"
    ignoreContext = True
    wrap = True
    z3cform.wrapper(MyCoolFormWrapper)
    grok.context(IProprioCalendar)
    grok.name('configuration')
    grok.require('zope2.View')

    @button.buttonAndHandler(u'Enregistrer')
    def handleApply(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = EditForm.formErrorsMessage
            return
        wrapper = getSAWrapper('gites_wallons')
        session = wrapper.session
        config = data.get('calendarConfig')
        for heb in getHebergementsForProprio(self.context, session):
            heb.heb_calendrier_proprio = config
            # mise à jour dernière date de modification du calendrier
            heb.heb_calendrier_proprio_date_maj = date.today()
            session.add(heb)
        session.flush()
        session.clear()
        self.status = self.successMessage


def getConfig(data):
    wrapper = getSAWrapper('gites_wallons')
    session = wrapper.session
    context = data.context
    pm = getToolByName(context, 'portal_membership')
    user = pm.getAuthenticatedMember()
    userPk = user.getProperty('pk')
    if userPk:
        Proprio = wrapper.getMapper('proprio')
        proprietaire = session.query(Proprio).get(int(userPk))
        for heb in proprietaire.hebergements:
            return heb.heb_calendrier_proprio

Defaultconfig = widget.ComputedWidgetAttribute(
    getConfig,
    field=ICalendarConfiguration['calendarConfig'], view=CalendarConfigForm)

grok.global_adapter(Defaultconfig, name='default')
