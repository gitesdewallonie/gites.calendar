# -*- coding: utf-8 -*-
"""
gites.calendar

Licensed under the GPL license, see LICENCE.txt for more details.
Copyright by Affinitic sprl
"""

import smtplib
from sets import Set
from datetime import date
from email.MIMEText import MIMEText
from sqlalchemy import select, and_

from gites.db.content import Proprio, Hebergement, HebergementBlockingHistory
from gites.calendar.scripts.pg import PGDB

FIRST_MAIL = """Madame, Monsieur,\n
Nous avons constaté que le calendrier de disponibilités de votre hébergement sur www.gitesdewallonie.be n’a pas été modifié depuis 30 jours.\n
Nous insistons sur l’importance de mettre à jour votre calendrier.  Les touristes qui utilisent la recherche par date doivent trouver une information à jour.  Cela vous évitera également de devoir répondre par la négative pour des dates déjà occupées.\n
Nous vous invitons à mettre rapidement à jour votre calendrier.\n
Si vous n’avez pas eu de réservations depuis 1 mois, merci de prendre contact avec la Maison des Gîtes de Wallonie afin d’éviter que votre calendrier soit désactivé.\n
Nous restons à votre entière disposition pour tout renseignement complémentaire.\n
Les Gîtes de Wallonie
"""

BLOCKING_MAIL = """Madame, Monsieur,\n
Malgré notre mail précédent, nous constatons qu’aucune mise à jour de votre calendrier de disponibilités sur www.gitesdewallonie.be n’a été réalisée.\n
Afin de garantir une information correcte et à jour aux touristes utilisant notre site, nous sommes au regret de vous informer que votre calendrier a été désactivé.  Les touristes ne sont donc plus en mesure de trouver votre hébergement en effectuant une recherche par date.\n
Nous restons à votre entière disposition pour tout renseignement complémentaire.\n
Les Gîtes de Wallonie
"""


class CalendarActivity(object):
    """
    Manage calendar activity notifications
    """

    def __init__(self, pg):
        self.pg = pg

    def connect(self):
        self.pg.connect()
        self.pg.setMappers()
        self.session = self.pg.session()

    def getProprio(self, proprioPk):
        query = self.session.query(Proprio)
        query = query.filter(Proprio.pro_pk == proprioPk)
        proprio = query.one()
        return proprio

    def getActiveCalendars(self):
        query = select([Hebergement.heb_pro_fk,
                        Hebergement.heb_calendrier_proprio_date_maj],
                        and_(Hebergement.heb_site_public == '1',
                             Hebergement.heb_calendrier_proprio != 'non actif',
                             Hebergement.heb_pro_fk == Proprio.pro_pk,
                             Proprio.pro_etat == True),
                        order_by=[Hebergement.heb_pk])
        return query.execute().fetchall()

    def now(self):
        # Useful for tests
        return date.today()

    def sendFirstMail(self, proprioPk):
        proprio = self.getProprio(proprioPk)
        proprioMail = proprio.pro_email
        if not proprioMail:
            print 'WARNING : %s %s has no email' % (proprio.pro_prenom1,
                                                    proprio.pro_nom1)
            return
        mailFrom = "info@gitesdewallonie.be"
        subject = "Votre calendrier sur le site des Gîtes de Wallonie"

        mail = MIMEText(FIRST_MAIL)
        mail['From'] = mailFrom
        mail['Subject'] = subject
        mail['To'] = proprioMail
        mail.set_charset('utf-8')

        server = smtplib.SMTP('localhost')
        server.sendmail(mailFrom, [proprioMail], mail.as_string())
        server.quit()
        print 'Sending warning mail to %s %s (%s)' % (proprio.pro_prenom1,
                                                      proprio.pro_nom1,
                                                      proprioMail)

    def sendSecondMail(self, proprioPk):
        proprio = self.getProprio(proprioPk)
        proprioMail = proprio.pro_email
        if not proprioMail:
            print 'WARNING : %s %s has no email' % (proprio.pro_prenom1,
                                                    proprio.pro_nom1)
            return
        mailFrom = "info@gitesdewallonie.be"
        subject = "Désactivation de votre calendrier"

        mail = MIMEText(BLOCKING_MAIL)
        mail['From'] = mailFrom
        mail['Subject'] = subject
        mail['To'] = proprioMail
        mail.set_charset('utf-8')

        server = smtplib.SMTP('localhost')
        server.sendmail(mailFrom, [proprioMail], mail.as_string())
        server.quit()
        print 'Sending blocking mail to %s %s (%s)' % (proprio.pro_prenom1,
                                                       proprio.pro_nom1,
                                                       proprioMail)

    def mustBeNotified(self, calendar):
        lastUpdate = calendar.heb_calendrier_proprio_date_maj
        delta = self.now() - lastUpdate
        return (delta.days == 30)

    def mustBeBlocked(self, calendar):
        lastUpdate = calendar.heb_calendrier_proprio_date_maj
        delta = self.now() - lastUpdate
        return (delta.days == 40)

    def isActive(self, calendar):
        lastUpdate = calendar.heb_calendrier_proprio_date_maj
        delta = self.now() - lastUpdate
        return (delta.days < 30)

    def blockCalendars(self, proprioPk):
        proprio = self.getProprio(proprioPk)
        for hebergement in proprio.hebergements:
            hebergement.heb_calendrier_proprio = u'bloque'
            self.session.add(hebergement)
            hebBlockHist = HebergementBlockingHistory()
            hebBlockHist.heb_blockhistory_blocked_dte = date.today()
            hebBlockHist.heb_blockhistory_heb_pk = hebergement.heb_pk
            self.session.add(hebBlockHist)
            self.session.flush()

    def checkCalendarActivity(self):
        calendars = self.getActiveCalendars()
        blockedProprios = Set()
        notifiedProprios = Set()
        activeProprios = Set()

        for calendar in calendars:
            if self.isActive(calendar):
                activeProprios.add(calendar.heb_pro_fk)
            elif self.mustBeBlocked(calendar) and \
               calendar.heb_pro_fk not in blockedProprios:
                blockedProprios.add(calendar.heb_pro_fk)
                if calendar.heb_pro_fk in notifiedProprios:
                    notifiedProprios.remove(calendar.heb_pro_fk)
            elif self.mustBeNotified(calendar) and \
                 calendar.heb_pro_fk not in blockedProprios and \
                 calendar.heb_pro_fk not in notifiedProprios:
                notifiedProprios.add(calendar.heb_pro_fk)

        notifiedProprios = notifiedProprios - activeProprios
        blockedProprios = blockedProprios - activeProprios

        for proprio in notifiedProprios:
            self.sendFirstMail(proprio)

        for proprio in blockedProprios:
            self.sendSecondMail(proprio)
            self.blockCalendars(proprio)

        return notifiedProprios, blockedProprios


def main():
    pg = PGDB('zope', 'zope', 'localhost', 5432, 'gites_wallons')
    checker = CalendarActivity(pg)
    checker.connect()
    checker.checkCalendarActivity()

if __name__ == "__main__":
    main()
