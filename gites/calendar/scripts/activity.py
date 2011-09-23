# -*- coding: utf-8 -*-
"""
gites.calendar

Licensed under the GPL license, see LICENCE.txt for more details.
Copyright by Affinitic sprl
"""

import smtplib
from datetime import date
from email.MIMEText import MIMEText
from sqlalchemy import select, and_, func

from gites.db.content import Proprio, Hebergement, HebergementBlockingHistory
from gites.calendar.crypt import encrypt
from gites.calendar.scripts.pg import PGDB

FIRST_MAIL = """Cher Membre,\n
Nous avons constaté que le calendrier de disponibilités de votre hébergement sur www.gitesdewallonie.be n'a pas été modifié depuis 30 jours.\n
Si aucune modification n'est intervenue depuis un mois, nous vous invitons simplement à cliquer sur ce lien pour nous le signaler : %s.\n
S'il s'agit d'un simple oubli de votre part, nous vous remercions de le mettre à jour très rapidement.\n
Le touriste qui recherche un hébergement pour une période déterminée désire, en effet, obtenir une information à jour. D'où l'importance de maintenir cette information précise. Nous souhaitons qu'à travers cette démarche que nous vous demandons, le touriste fasse entièrement confiance aux disponibilités qui s'offrent à lui et se réfèrent principalement à notre site pour la précision des informations qu'il en retire.\n
Nous restons à votre entière disposition et nous vous remercions, cher Membre, de votre démarche.\n
Les Gîtes de Wallonie.
"""

BLOCKING_MAIL = """Madame, Monsieur,\n
Malgré notre mail précédent, nous constatons qu’aucune mise à jour de votre calendrier de disponibilités sur www.gitesdewallonie.be n’a été réalisée.\n
Afin de garantir une information correcte et à jour aux touristes utilisant notre site, nous sommes au regret de vous informer que votre calendrier a été désactivé. Cliquez sur ce lien pour le réactiver : %s.\n
Nous restons à votre entière disposition pour tout renseignement complémentaire.\n
Les Gîtes de Wallonie.
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
        # On ne garde que la date de mise à jour la plus récente par proprio,
        # les autres n'ont pas d'importance
        query = select([Hebergement.heb_pro_fk,
                        func.max(Hebergement.heb_calendrier_proprio_date_maj).label('heb_calendrier_proprio_date_maj')],
                        and_(Hebergement.heb_site_public == '1',
                             Hebergement.heb_calendrier_proprio != 'non actif',
                             Hebergement.heb_calendrier_proprio != 'bloque',
                             Hebergement.heb_pro_fk == Proprio.pro_pk,
                             Proprio.pro_etat == True),
                        order_by=[Hebergement.heb_pro_fk],
                        group_by=[Hebergement.heb_pro_fk])
        return query.execute().fetchall()

    def now(self):
        # Useful for tests
        return date.today()

    def sendFirstMail(self, proprioPk, majDate):
        proprio = self.getProprio(proprioPk)
        proprioMail = proprio.pro_email
        if not proprioMail:
            print 'WARNING : %s %s has no email' % (proprio.pro_prenom1,
                                                    proprio.pro_nom1)
            return
        mailFrom = "info@gitesdewallonie.be"
        subject = "Votre calendrier sur le site des Gîtes de Wallonie"

        encryptedPk = encrypt(proprioPk)
        mail = MIMEText(FIRST_MAIL % encryptedPk)
        mail['From'] = mailFrom
        mail['Subject'] = subject
        mail['To'] = proprioMail
        mail.set_charset('utf-8')

        server = smtplib.SMTP('localhost')
        server.sendmail(mailFrom, [proprioMail], mail.as_string())
        server.quit()
        print 'Sending warning mail to %s %s (%s) - last modification date : %s' % \
                              (proprio.pro_prenom1,
                               proprio.pro_nom1,
                               proprioMail,
                               majDate.strftime('%d-%m-%Y'))

    def sendSecondMail(self, proprioPk, majDate):
        proprio = self.getProprio(proprioPk)
        proprioMail = proprio.pro_email
        if not proprioMail:
            print 'WARNING : %s %s has no email' % (proprio.pro_prenom1,
                                                    proprio.pro_nom1)
            return
        mailFrom = "info@gitesdewallonie.be"
        subject = "Désactivation de votre calendrier"

        encryptedPk = encrypt(proprioPk)
        mail = MIMEText(BLOCKING_MAIL % encryptedPk)
        mail['From'] = mailFrom
        mail['Subject'] = subject
        mail['To'] = proprioMail
        mail.set_charset('utf-8')

        server = smtplib.SMTP('localhost')
        server.sendmail(mailFrom, [proprioMail], mail.as_string())
        server.quit()
        print 'Sending blocking mail to %s %s (%s) - last modification date : %s' % \
                              (proprio.pro_prenom1,
                               proprio.pro_nom1,
                               proprioMail,
                               majDate.strftime('%d-%m-%Y'))

    def mustBeNotified(self, calendar):
        lastUpdate = calendar.heb_calendrier_proprio_date_maj
        delta = self.now() - lastUpdate
        return (delta.days == 30)

    def mustBeBlocked(self, calendar):
        lastUpdate = calendar.heb_calendrier_proprio_date_maj
        delta = self.now() - lastUpdate
        return (delta.days >= 40)

    def blockCalendars(self, proprioPk):
        proprio = self.getProprio(proprioPk)
        for hebergement in proprio.hebergements:
            hebergement.heb_calendrier_proprio = u'bloque'
            self.session.add(hebergement)
            hebBlockHist = HebergementBlockingHistory()
            hebBlockHist.heb_blockhistory_blocked_dte = self.now()
            hebBlockHist.heb_blockhistory_heb_pk = hebergement.heb_pk
            self.session.add(hebBlockHist)
            self.session.flush()

    def checkCalendarActivity(self):
        calendars = self.getActiveCalendars()
        blockedProprios = []
        notifiedProprios = []

        for calendar in calendars:
            if self.mustBeNotified(calendar):
                notifiedProprios.append([calendar.heb_pro_fk,
                                         calendar.heb_calendrier_proprio_date_maj])
            elif self.mustBeBlocked(calendar):
                blockedProprios.append([calendar.heb_pro_fk,
                                        calendar.heb_calendrier_proprio_date_maj])

        for proprio, majDate in notifiedProprios:
            self.sendFirstMail(proprio, majDate)

        for proprio, majDate in blockedProprios:
            self.sendSecondMail(proprio, majDate)
            self.blockCalendars(proprio)

        return notifiedProprios, blockedProprios


def main():
    pg = PGDB('jfroche', 'xxxxxx', 'localhost', 5432, 'gites_wallons')
    checker = CalendarActivity(pg)
    checker.connect()
    checker.checkCalendarActivity()

if __name__ == "__main__":
    main()
