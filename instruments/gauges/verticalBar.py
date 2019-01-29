#  Copyright (c) 2013 Phil Birkelbach
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.

try:
    from PyQt5.QtGui import *
    from PyQt5.QtCore import *
    from PyQt5.QtWidgets import *
except:
    from PyQt4.QtGui import *
    from PyQt4.QtCore import *

import fix
from .abstract import AbstractGauge

class VerticalBar(AbstractGauge):
    def __init__(self, parent=None):
        super(VerticalBar, self).__init__(parent)
        self.setMinimumSize(10, 30)

    def paintEvent(self, e):
        p = QPainter()
        p.begin(self)
        p.setPen(self.outlineColor)
        p.setBrush(self.bgColor)
        height = self.height()  # keep from calling functions and shorten code
        width = self.width()
        p.drawRect(0, 0, width - 1, height - 1)
        # Calculate the positions of the setpoint lines
        if self.highWarn:
            highWarnLine = self.height() - int(self.interpolate(self.highWarn,
                                                                self.height()))
        if self.highAlarm:
            highAlarmLine = self.height() - int(self.interpolate(self.highAlarm,
                                                                 self.height()))
        # This calculates where the top of the graph should be
        valueLine = self.height() - int(self.interpolate(self._value,
                                                         self.height()))
        # Draws the Alarm (Red) part of the graph
        if self._value > self.highAlarm:
            p.setPen(self.alarmColor)
            p.setBrush(self.alarmColor)
            p.drawRect(1, valueLine, width - 3, highAlarmLine - valueLine - 1)
        # Draw the warning part of the graph if it's above the setpoint
        if self._value > self.highWarn:
            p.setPen(self.warnColor)
            p.setBrush(self.warnColor)
            start = max(valueLine, highAlarmLine)
            p.drawRect(1, start, width - 3, highWarnLine - start - 1)
        if self._value > 0:
            # Draw the green part of the graph
            p.setPen(self.safeColor)
            p.setBrush(self.safeColor)
            start = max(valueLine, highWarnLine)
            p.drawRect(1, start, width - 3, height - start - 2)
            # Draw the top of the graph
            p.setPen(QColor(Qt.white))
            p.drawLine(1, valueLine, width - 2, valueLine)
        # Draw Setpoint Lines
        if self.highWarn:
            p.setPen(self.warnColor)
            p.drawLine(1, highWarnLine, self.width() - 2, highWarnLine)
        if self.highAlarm:
            p.setPen(self.alarmColor)
            p.drawLine(1, highAlarmLine, self.width() - 2, highAlarmLine)
        p.end()
