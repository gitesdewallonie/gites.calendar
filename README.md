gites.calendar
==============

gites.calendar gère la disponibilité des gites tel que représentés sur le site web des gites de Wallonie.

Il y a deux manières de mettre à jour les calendriers, mais chacun d'eux vont mettre à jour la table reservation_proprio dans la DB des gites de Wallonie.


Via l'interface
---------------

En se connectant sur le site web comme propriétaire, on peut accéder à une page permettant de changer les disponibilités du gite en cliquant sur les calendrier. Les changements seront alors appliqué via un call ajax de la vue 'addRange'.


Via webservice
--------------

Il existe un webservice qui permet entre autre de changer les dates de réservations d'un gite.

Pour plus d'informations sur ces webservices, http://doc.walhebcalendar.be/ et https://github.com/gitesdewallonie/gites.walhebcalendar

Le code de walhebcalendar ne va pas directement mettre à jour la base de données des gites, il se contentera d'envoyer un message à une queue RabbitMQ qui se trouve sur le serveur gauss.

Cependant, le consumer de cette queue se trouve bien dans gites.calendar, celui ci va récupérer tous les messages de walhebcalendar et ainsi mettre à jour la base de données des gites de Wallonie. Voir script bin/importCalendarEventsFromWalhebCalendarDaemon


Déploiement localhost
=====================

Vu la complexité du workflow, voici les étapes à suivre pour pouvoir tester tout le cheminement en local.


Configuration de RabbitMQ
-------------------------

Il est conseillé de d'abord suivre la documentation du gites.walhebcalendar avant d'appliquer celle ci.

Ajouter via l'interface de configuration de RabbitMQ ( http://localhost:15672 ), l'utilisateur gdw:tototo qui doit posséder les meme droits que l'utilisateur admin créé pour gites.walhebcalendar.


Lancement du consumer
---------------------

Il faut simplement changer le serveur auquel le consumer va se connecter:

export AMQP_BROKER_HOST=localhost

Et lancer le consumer:

bin/importCalendarEventsFromWalhebCalendarDaemon

Grace à cette configuration, vous les informations envoyées via le webservice se répercuteront dans la base de données des gites de Wallonie et ainsi sur les calendriers visible.


Problèmes connus
----------------

Si RabbitMQ est coupé, le daemon **bin/importCalendarEventsFromWalhebCalendarDaemon** sera coupé également.

De plus, le webservice walhebcalendar continuera de fonctionner à moitié: il enregistrera les changements dans la DB walhebcalendar, mais il n'enverra pas de message à RabbitMQ et il renverra un message d'erreur au client.

L'instance des webservice doit etre relancée après un reboot de RabbitMQ, elle ne se reconnecte pas automatiquement à celui ci.


Schéma
------

![Walhebcalendar workflow](https://www.lucidchart.com/publicSegments/view/55706155-0af0-4db6-9278-59a90a0050c0/image.png)
