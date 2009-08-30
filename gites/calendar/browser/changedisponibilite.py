# -*- coding: utf-8 -*-
"""
gites.calendar

Licensed under the GPL license, see LICENCE.txt for more details.
Copyright by Affinitic sprl

$Id: event.py 67630 2006-04-27 00:54:03Z jfroche $
"""
from zope.interface import Interface
from zope.schema import Date
from z3c.form.form import EditForm
from z3c.form import field, button
from gites.calendar.interfaces import IProprioCalendar
from five import grok
from five.megrok.z3cform import Form
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from z3c.form.interfaces import INPUT_MODE
from collective.z3cform.datepicker.widget import DatePickerFieldWidget


class IChangeDispo(Interface):

    startDate = Date(
        title=u"Date de début",
        description=u"Selectionner la date début",
        required=True)

    endDate = Date(
        title=u"Date de fin",
        description=u"Selectionner la date fin",
        required=True)


class ChangeDispoForm(Form):
    fields = field.Fields(IChangeDispo)
    label = u"Editer la disponibilité"
    ignoreContext = True
    grok.context(IProprioCalendar)
    grok.name('changedisponibilite')
    grok.require('zope2.View')
    template = ViewPageTemplateFile('templates/selectheb.pt')
    fields['startDate'].widgetFactory[INPUT_MODE] = DatePickerFieldWidget
    fields['endDate'].widgetFactory[INPUT_MODE] = DatePickerFieldWidget

    @button.buttonAndHandler(u'Enregistrer')
    def handleApply(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = EditForm.formErrorsMessage
            return
