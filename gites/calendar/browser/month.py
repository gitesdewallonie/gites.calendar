# -*- coding: utf-8 -*-
"""
gites.calendar

Licensed under the GPL license, see LICENCE.txt for more details.
Copyright by Affinitic sprl

$Id: event.py 67630 2006-04-27 00:54:03Z jfroche $
"""
from plone.memoize.instance import memoize
from dateable.chronos.browser.month import MonthView
from z3c.sqlalchemy import getSAWrapper
import plone.z3cform.z2
from zope.schema.interfaces import IVocabularyFactory
from zope.component import getUtility


class CalMonthView(MonthView):

    def calendarJS(self):
        """
        Calendar javascript
        """
        return """
        //<![CDATA[
        calsetup = function() {
          jQuery.noConflict();
          new Timeframe('calendars', {
                startField: 'start',
                endField: 'end',
                resetButton: 'reset',
                weekOffset: 1,
                hebPk: %s,
                earliest: new Date()});}
        registerPloneFunction(calsetup);
        //]]>""" % self.request.SESSION.get('cal-selected-heb')

    def title(self):
        hebPk = self.request.SESSION.get('cal-selected-heb')
        if hebPk:
            wrapper = getSAWrapper('gites_wallons')
            Hebergement = wrapper.getMapper('hebergement')
            session = wrapper.session
            hebergement = session.query(Hebergement).get(hebPk)
            return u'Calendrier pour %s - %s' % (hebergement.heb_pk,
                                                 hebergement.heb_nom)
        else:
            return u'Calendrier'

    def __call__(self):
        gitesPkAvailables = [item.token for item in \
                             getUtility(IVocabularyFactory,
                                        name='proprio.hebergements')(self.context)]
        pk = self.request.form.get('pk')
        if (not pk or pk not in gitesPkAvailables):
            self.request.RESPONSE.redirect('%s/unavailable' % self.context.absolute_url())
            return
        self.pk = pk
        self.request.SESSION.set('cal-selected-heb', pk)
        self.request.locale = plone.z3cform.z2.setup_locale(self.request)
        return super(CalMonthView, self).__call__()


class MultiCalView(MonthView):

    def calendarJS(self):
        """
        Calendar javascript
        """
        gites = self.getGitesForProprio()
        hebPks = [int(gite.token) for gite in gites]
        hebNames = [gite.title for gite in gites]
        return ("""
        //<![CDATA[
        calsetup = function() {
          jQuery.noConflict();
          new Timeframe('calendars', {
                startField: 'start',
                endField: 'end',
                resetButton: 'reset',
                months: 1,
                weekOffset: 1,
                hebsPks: %s,
                hebsNames: %s,
                earliest: new Date()});}
        registerPloneFunction(calsetup);
        //]]>""" % (hebPks, hebNames)).replace("[u'", "['").replace(", u'", ", '")

    @memoize
    def getGitesForProprio(self):
        return getUtility(IVocabularyFactory, name='proprio.hebergements')(self.context)
