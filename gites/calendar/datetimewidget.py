#!/usr/bin/env python
# -*- coding: utf-8 -*-
from zc.datetimewidget.datetimewidget import DateWidget


class GitesDateWidget(DateWidget):
    _format = '%d/%m/%Y'

    def _toFieldValue(self, input):
        day, month, year = input.split('/')
        return super(GitesDateWidget, self)._toFieldValue('{0}-{1}-{2}'.format(year, month, day))
