# -*- coding: utf-8 -*-
"""
gites.calendar

Licensed under the GPL license, see LICENCE.txt for more details.
Copyright by Affinitic sprl

$Id: event.py 67630 2006-04-27 00:54:03Z jfroche $
"""
from dateable.chronos.browser.month import MonthView
from z3c.sqlalchemy import getSAWrapper
import plone.z3cform.z2


class CalMonthView(MonthView):

    def title(self):
        hebPk = self.request.SESSION.get('cal-selected-heb')
        if hebPk:
            wrapper = getSAWrapper('gites_wallons')
            Hebergement = wrapper.getMapper('hebergement')
            session = wrapper.session
            hebergement = session.query(Hebergement).get(hebPk)
            return u'Calendrier pour %s' % hebergement.heb_nom
        else:
            return u'Calendrier'

    def update(self):
        self.request.locale = plone.z3cform.z2.setup_locale(self.request)
        super(CalMonthView, self).update()
