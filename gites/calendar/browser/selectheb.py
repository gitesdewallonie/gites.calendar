# -*- coding: utf-8 -*-
"""
gites.calendar

Licensed under the GPL license, see LICENCE.txt for more details.
Copyright by Affinitic sprl

$Id: event.py 67630 2006-04-27 00:54:03Z jfroche $
"""
from zope.interface import Interface
from zope.schema import Choice
from z3c.form.form import EditForm
from z3c.form import field, button
from gites.calendar.interfaces import IProprioCalendar
from five import grok
from five.megrok.z3cform import Form
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile


class ISelectHebergement(Interface):

    selectedHeb = Choice(
        title=u"Hebergements",
        description=u"Selectionner un de vos hebergements",
        required=True,
        vocabulary="proprio.hebergements")


class SelectHebergementForm(Form):
    fields = field.Fields(ISelectHebergement)
    label = u"Editer la disponibilité de vos hébergements"
    ignoreContext = True
    grok.context(IProprioCalendar)
    grok.name('edit.html')
    grok.require('zope2.View')
    template = ViewPageTemplateFile('templates/selectheb.pt')

    @button.buttonAndHandler(u'Selectionner')
    def handleApply(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = EditForm.formErrorsMessage
            return
        self.request.SESSION.set('cal-selected-heb', int(data.get('selectedHeb')))
        return  self.request.RESPONSE.redirect('%s/month.html' % self.context.absolute_url())
