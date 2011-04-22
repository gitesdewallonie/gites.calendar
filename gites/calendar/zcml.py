# -*- coding: utf-8 -*-
"""
gites.calendar

Licensed under the GPL license, see LICENCE.txt for more details.
Copyright by Affinitic sprl
"""
from zope.configuration import xmlconfig


def parseZCML(package, configFile='configure.zcml'):
    context = xmlconfig._getContext()
    xmlconfig.include(context, configFile, package)
    context.execute_actions()
