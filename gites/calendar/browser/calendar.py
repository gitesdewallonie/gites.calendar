# -*- coding: utf-8 -*-
"""
gites.calendar

Licensed under the GPL license, see LICENCE.txt for more details.
Copyright by Affinitic sprl

$Id: event.py 67630 2006-04-27 00:54:03Z jfroche $
"""
from five import grok
from gites.calendar.interfaces import IProprioCalendar
from zope.interface import Interface
import simplejson
from z3c.sqlalchemy import getSAWrapper
from sqlalchemy import select
from time import strptime
import datetime
from dateutil.relativedelta import relativedelta
from Products.CMFCore.utils import getToolByName
from zope.app.schema.vocabulary import IVocabularyFactory
from zope.component import getUtility

grok.context(Interface)
grok.templatedir('templates')


class CalendarAndDateRanges(grok.CodeView):
    """
    Configure calendar for proprio
    """
    grok.context(IProprioCalendar)
    grok.name('addRange')
    grok.require('zope2.View')

    def render(self):
        return

    def _removeSelection(self, start, end):
        wrapper = getSAWrapper('gites_wallons')
        session = wrapper.session
        ReservationProprio = wrapper.getMapper('reservation_proprio')
        subquery = select([ReservationProprio.res_id])
        subquery.append_whereclause(ReservationProprio.res_date.between(start,
                                                                        end))
        query = session.query(ReservationProprio)
        query = query.filter(ReservationProprio.res_id.in_(subquery))
        query.delete()

    def __call__(self):
        wrapper = getSAWrapper('gites_wallons')
        session = wrapper.session
        ReservationProprio = wrapper.getMapper('reservation_proprio')
        start = datetime.datetime(*strptime(self.request.get('start'),
                                   "%Y-%m-%d")[0:6])
        end = datetime.datetime(*strptime(self.request.get('end'),
                                   "%Y-%m-%d")[0:6])
        typeOfSelection = self.request.get('type')
        self._removeSelection(start, end)
        if typeOfSelection == 'libre':
            return
        currentdate = start
        hebPk = self.request.SESSION.get('cal-selected-heb')
        pm = getToolByName(self.context, 'portal_membership')
        gitesPkAvailables = [item.token for item in \
                             getUtility(IVocabularyFactory,
                                        name='proprio.hebergements')(self.context)]
        assert(hebPk in gitesPkAvailables)
        user = pm.getAuthenticatedMember()
        userPk = user.getProperty('pk')
        while currentdate <= end:
            res = ReservationProprio()
            res.res_date = currentdate
            res.heb_fk = hebPk
            res.pro_fk = userPk
            res.res_type = typeOfSelection
            res.res_date_cre = datetime.datetime.now()
            session.add(res)
            currentdate += datetime.timedelta(days=1)
        session.flush()


class GiteCalendarSelectedDays(grok.CodeView):
    """
    Configure calendar for proprio
    """
    grok.context(Interface)
    grok.name('selectedDays')
    grok.require('zope2.View')

    def render(self):
        return

    def __call__(self):
        hebPk = self.request.form.get('hebPk')
        year = self.request.form.get('year')
        month = self.request.form.get('month')
        monthRange = self.request.form.get('range')
        if hebPk == None or year == None or month == None or \
           monthRange == None:
            return
        minDate = datetime.datetime(int(year), int(month), 1)
        maxDate = minDate + relativedelta(months=+int(monthRange))
        self.request.RESPONSE.setHeader('content-type', 'text/x-json')
        wrapper = getSAWrapper('gites_wallons')
        ReservationProprio = wrapper.getMapper('reservation_proprio')
        session = wrapper.session
        query = select([ReservationProprio.res_date])
        query.append_whereclause(ReservationProprio.res_date.between(minDate, maxDate))
        query.append_whereclause(ReservationProprio.heb_fk==int(hebPk))
        dateList = []
        for res in query.execute().fetchall():
            dateList.append(res.res_date.strftime('%Y-%m-%d'))
        return simplejson.dumps({'rented': dateList})


class CalendarSelectedDays(grok.CodeView):
    """
    Configure calendar for proprio
    """
    grok.context(IProprioCalendar)
    grok.name('selectedDays')
    grok.require('cmf.ListFolderContents')

    def render(self):
        return

    def __call__(self):
        self.request.RESPONSE.setHeader('content-type', 'text/x-json')
        self.request.RESPONSE.setHeader('Cache-Control', 'no-cache')
        wrapper = getSAWrapper('gites_wallons')
        ReservationProprio = wrapper.getMapper('reservation_proprio')
        session = wrapper.session
        query = select([ReservationProprio.res_date,
                        ReservationProprio.res_type])
        dateList = []
        typeList = []
        for res in query.execute().fetchall():
            dateList.append(res.res_date.strftime('%Y-%m-%d'))
            typeList.append(res.res_type)
        return simplejson.dumps({'rented': dateList,
                                 'type': typeList})
