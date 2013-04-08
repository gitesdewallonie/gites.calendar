from setuptools import setup, find_packages
import os

version = '0.1'

setup(name='gites.calendar',
      version=version,
      description="",
      long_description=open("README.txt").read() + "\n" +
      open(os.path.join("docs", "HISTORY.txt")).read(),
      classifiers=[
          "Programming Language :: Python",
          "Topic :: Software Development :: Libraries :: Python Modules"],
      keywords='',
      author='',
      author_email='',
      url='',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['gites'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'affinitic.zamqp',
          'zope.app.testing>=3.5',
          'setuptools',
          'gites.core',
          'gites.db',
          'affinitic.db',
          'dateutil',
          'simplejson',
          'p4a.calendar',
          'p4a.plonecalendar',
          'p4a.ploneevent',
          'p4a.subtyper',
          'zope.app.i18n'],
      entry_points={'console_scripts':
                    ['checkCalendarActivity = gites.calendar.scripts.activity:main',
                     'exportCalendarEvents = gites.calendar.scripts.calendar:main',
                     'importCalendarEventsFromWalhebCalendarDaemon = gites.calendar.scripts.calendarimport:main']})
