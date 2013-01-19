# -*- coding: utf-8 -*-
"""
gites.calendar

Licensed under the GPL license, see LICENCE.txt for more details.
Copyright by Affinitic sprl

$Id: event.py 67630 2006-04-27 00:54:03Z jfroche $
"""
from five import grok
from zope.schema.interfaces import IVocabularyFactory
from z3c.sqlalchemy import getSAWrapper
from sqlalchemy import and_
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm
from Products.CMFCore.utils import getToolByName
from gites.core.memcached import cache

CONFIG = {'actif': "Calendrier visible par tous (recherches et page d'hebergement)",
          'searchactif': "Calendrier visible pour recherches uniquement",
          'non actif': "Calendrier non activé"}


def cacheKey(meth, propioPk, session):
    return (propioPk,)


@cache(cacheKey, lifetime=10)
def getHebergementsForProprioId(proprioPk, session):
    wrapper = getSAWrapper('gites_wallons')
    if session is None:
        session = wrapper.session
    Proprio = wrapper.getMapper('proprio')
    query = session.query(Proprio)
    query = query.filter(and_(Proprio.pro_pk == int(proprioPk),
                              Proprio.pro_etat == True))
    proprietaire = query.one()
    hebs = proprietaire.hebergements
    hebs.sort(key=lambda x: x.heb_pk)
    publicHebs = []
    for heb in hebs:
        if heb.heb_site_public == '1':
            publicHebs.append(heb)
    return publicHebs


def getHebergementsForProprio(context, session=None):
    pm = getToolByName(context, 'portal_membership')
    user = pm.getAuthenticatedMember()
    userPk = user.getProperty('pk')
    if userPk:
        return getHebergementsForProprioId(userPk, session)


class CalendarConfiguration(grok.GlobalUtility):
    grok.provides(IVocabularyFactory)
    grok.name('proprio.calendarconfig')

    def __call__(self, context):
        items = []
        for key, value in CONFIG.items():
            items.append(SimpleTerm(key,
                                    key,
                                    value))
        return SimpleVocabulary(items)


class ProprioHebergements(grok.GlobalUtility):
    grok.provides(IVocabularyFactory)
    grok.name('proprio.hebergements')

    def __call__(self, context):
        items = []
        for heb in getHebergementsForProprio(context):
                items.append(SimpleTerm(heb.heb_pk,
                                        heb.heb_pk,
                                        u'%s - %s' % (heb.heb_pk, heb.heb_nom)))
        return SimpleVocabulary(items)
