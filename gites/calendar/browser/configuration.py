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
from sqlalchemy import desc
from gites.db.content import HebergementBlockingHistory
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

    def getBlockedInfo(self, session, heb_pk):
        query = session.query(HebergementBlockingHistory)
        query = query.filter_by(heb_blockhistory_heb_pk=heb_pk)
        query = query.filter_by(heb_blockhistory_activated_dte=None)
        query = query.order_by(desc(HebergementBlockingHistory.heb_blockhistory_blocked_dte))
        return query.first()

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
            oldConfig = heb.heb_calendrier_proprio
            heb.heb_calendrier_proprio = config
            # mise à jour dernière date de modification du calendrier
            heb.heb_calendrier_proprio_date_maj = date.today()
            session.add(heb)
            if oldConfig != config:
                if config == u'non actif':
                    hebBlockHist = HebergementBlockingHistory()
                    hebBlockHist.heb_blockhistory_blocked_dte = date.today()
                    hebBlockHist.heb_blockhistory_heb_pk = heb.heb_pk
                    session.add(hebBlockHist)
                else:
                    blockHist = self.getBlockedInfo(session, heb.heb_pk)
                    if blockHist is not None:
                        blockHist.heb_blockhistory_activated_dte = date.today()
                        blockedDate = blockHist.heb_blockhistory_activated_dte - blockHist.heb_blockhistory_blocked_dte
                        blockHist.heb_blockhistory_days = blockedDate.days
                        session.add(blockHist)
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
