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
from sqlalchemy import select, desc
from time import strptime
import datetime
from dateutil.relativedelta import relativedelta
from Products.CMFCore.utils import getToolByName
from zope.schema.interfaces import IVocabularyFactory
from zope.component import getUtility
from zope.interface import implements
from zope.event import notify
from gites.db.content import Proprio, HebergementBlockingHistory
from gites.calendar.browser.interfaces import ICalendarUpdateEvent

grok.context(Interface)
grok.templatedir('templates')


class CalendarInfos(grok.View):
    """
    Get informations about calendars
    """
    grok.context(Interface)
    grok.name('calendarInfo')
    grok.require('zope2.View')

    def render(self):
        return

    def getLastModification(self, hebPk):
        """
        Return heb last modification date
        """
        wrapper = getSAWrapper('gites_wallons')
        session = wrapper.session
        Hebergement = wrapper.getMapper('hebergement')
        query = session.query(Hebergement)
        query = query.filter(Hebergement.heb_pk == hebPk)
        heb = query.one()
        return heb.heb_calendrier_proprio_date_maj


class CalendarReactivation(grok.View):
    """
    Allows to reactivate a calendar, directly from mails sent to proprios
    """
    grok.context(Interface)
    grok.name('reactivation-calendrier')
    grok.require('zope2.View')

    def getBlockedInfo(self, session, heb_pk):
        query = session.query(HebergementBlockingHistory)
        query = query.filter_by(heb_blockhistory_heb_pk=heb_pk)
        query = query.filter_by(heb_blockhistory_activated_dte=None)
        query = query.order_by(desc(HebergementBlockingHistory.heb_blockhistory_blocked_dte))
        return query.first()

    def getProprio(self, session, proprioHash):
        query = session.query(Proprio)
        query = query.filter(Proprio.pro_reactivation_hash == proprioHash)
        proprio = query.one()
        return proprio

    def reactivateCalendars(self, key):
        """
        Find proprio (by Postgres hash) and reactivate calendar
        """
        if not key:
            return
        wrapper = getSAWrapper('gites_wallons')
        session = wrapper.session
        proprio = self.getProprio(session, key)
        for hebergement in proprio.hebergements:
            hebergement.heb_calendrier_proprio_date_maj = datetime.date.today()
            if hebergement.heb_calendrier_proprio == u'bloque':
                hebergement.heb_calendrier_proprio = u'actif'
            session.add(hebergement)
            blockHist = self.getBlockedInfo(session, hebergement.heb_pk)
            if blockHist is not None:
                blockHist.heb_blockhistory_activated_dte = datetime.date.today()
                blockedDate = blockHist.heb_blockhistory_activated_dte - blockHist.heb_blockhistory_blocked_dte
                blockHist.heb_blockhistory_days = blockedDate.days
                session.add(blockHist)
        session.flush()


class CalendarUpdateEvent(object):
    implements(ICalendarUpdateEvent)

    def __init__(self, hebPk, start, end, typeOfSelection):
        self.hebPk = hebPk
        self.start = start
        self.end = end
        self.typeOfSelection = typeOfSelection


class CalendarAndDateRanges(grok.CodeView):
    """
    Change reservations (add / delete) in a calendar
    """
    grok.context(IProprioCalendar)
    grok.name('addRange')
    grok.require('zope2.View')

    def render(self):
        return

    def _removeSelection(self, session, wrapper, hebPk, start, end):
        ReservationProprio = wrapper.getMapper('reservation_proprio')
        subquery = select([ReservationProprio.res_id])
        subquery.append_whereclause(ReservationProprio.res_date.between(start,
                                                                        end))
        subquery.append_whereclause(ReservationProprio.heb_fk == hebPk)
        query = session.query(ReservationProprio)
        query = query.filter(ReservationProprio.res_id.in_(subquery))
        query.delete()
        session.flush()

    def __call__(self):
        hebPk = self.request.get('hebPk', None)
        if not hebPk:
            hebPk = self.request.SESSION.get('cal-selected-heb')
        gitesPkAvailables = [item.token for item in
                             getUtility(IVocabularyFactory,
                                        name='proprio.hebergements')(self.context)]
        assert(hebPk in gitesPkAvailables)
        wrapper = getSAWrapper('gites_wallons')
        session = wrapper.session
        # mise à jour dernière date de modification du calendrier
        Hebergement = wrapper.getMapper('hebergement')
        query = session.query(Hebergement)
        query = query.filter(Hebergement.heb_pk == hebPk)
        query.update({"heb_calendrier_proprio_date_maj": datetime.date.today()},
                     synchronize_session=False)
        session.flush()
        ReservationProprio = wrapper.getMapper('reservation_proprio')
        start = datetime.datetime(*strptime(self.request.get('start'),
                                  "%Y-%m-%d")[0:6])
        end = datetime.datetime(*strptime(self.request.get('end'),
                                "%Y-%m-%d")[0:6])
        typeOfSelection = self.request.get('type')
        self._removeSelection(session, wrapper, hebPk, start, end)
        notify(CalendarUpdateEvent(hebPk, start, end, typeOfSelection))
        if typeOfSelection == 'libre':
            return
        currentdate = start
        pm = getToolByName(self.context, 'portal_membership')
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


def notifyUpdate(event):
    from affinitic.zamqp.interfaces import IPublisher
    publisher = getUtility(IPublisher, name="walhebcalendar.gdw")
    wrapper = getSAWrapper('gites_wallons')
    Hebergement = wrapper.getMapper('hebergement')
    query = select([Hebergement.heb_code_cgt])
    query.append_whereclause(Hebergement.heb_pk == event.hebPk)
    cgtId = query.execute().fetchone().heb_code_cgt
    if cgtId and event.start >= datetime.datetime.now():
        infos = event.__dict__
        infos['cgtId'] = cgtId
        publisher.send(infos)


class GiteCalendarSelectedDays(grok.CodeView):
    """
    Get all busy days
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
        now = datetime.datetime.now()
        if minDate < now:
            minDate = now
        maxDate = minDate + relativedelta(months=int(monthRange))
        self.request.RESPONSE.setHeader('content-type', 'text/x-json')
        wrapper = getSAWrapper('gites_wallons')
        ReservationProprio = wrapper.getMapper('reservation_proprio')
        query = select([ReservationProprio.res_date])
        minDate = minDate + relativedelta(days=-1)  # 'between' SQL clause is
                                                    # exclusive, excluding
                                                    # TODAY day
        query.append_whereclause(ReservationProprio.res_date.between(minDate, maxDate))
        query.append_whereclause(ReservationProprio.heb_fk == int(hebPk))
        dateList = []
        for res in query.execute().fetchall():
            dateList.append(res.res_date.strftime('%Y-%m-%d'))
        return simplejson.dumps({'rented': dateList})


class CalendarSelectedDays(grok.CodeView):
    """
    Get all busy days
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
        hebPk = self.request.get('hebPk', None)
        if not hebPk:
            hebPk = self.request.SESSION.get('cal-selected-heb')
        query = select([ReservationProprio.res_date,
                        ReservationProprio.res_type])
        query.append_whereclause(ReservationProprio.heb_fk == int(hebPk))
        dateList = []
        typeList = []
        for res in query.execute().fetchall():
            dateList.append(res.res_date.strftime('%Y-%m-%d'))
            typeList.append(res.res_type)
        return simplejson.dumps({'rented': dateList,
                                 'type': typeList})
