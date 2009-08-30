# -*- coding: utf-8 -*-
"""
gites.calendar

Licensed under the GPL license, see LICENCE.txt for more details.
Copyright by Affinitic sprl

$Id: event.py 67630 2006-04-27 00:54:03Z jfroche $
"""
from five import grok
from zope.app.schema.vocabulary import IVocabularyFactory
from z3c.sqlalchemy import getSAWrapper
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm
from Products.CMFCore.utils import getToolByName


class ProprioHebergements(grok.GlobalUtility):
    grok.provides(IVocabularyFactory)
    grok.name('proprio.hebergements')

    def __call__(self, context):
        wrapper = getSAWrapper('gites_wallons')
        session = wrapper.session
        items = []
        pm = getToolByName(context, 'portal_membership')
        user = pm.getAuthenticatedMember()
        userPk = user.getProperty('pk')
        if userPk:
            Proprio = wrapper.getMapper('proprio')
            proprietaire = session.query(Proprio).get(int(userPk))
            for heb in proprietaire.hebergements:
                items.append(SimpleTerm(heb.heb_pk,
                                        heb.heb_pk,
                                        u'%s - %s' % (heb.heb_pk, heb.heb_nom)))
        return SimpleVocabulary(items)
