#  Copyright (c) 2013 Neil Domalik; 2018-2019 Garrett Herschleb
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

import math
import time

try:
    from PyQt5.QtGui import *
    from PyQt5.QtCore import *
    from PyQt5.QtWidgets import *
except:
    from PyQt4.QtGui import *
    from PyQt4.QtCore import *
import pyavtools.fix as fix

class HSI(QGraphicsView):
    def __init__(self, parent=None, font_size=15, fgcolor=Qt.black, bgcolor=Qt.white):
        super(HSI, self).__init__(parent)
        self.setStyleSheet("background-color: rgba(0, 0, 0, 0%); border: 0px")
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setRenderHint(QPainter.Antialiasing)
        self.setFocusPolicy(Qt.NoFocus)
        self.fontSize = font_size
        self.fg_color = fgcolor
        self.bg_color = bgcolor
        item = fix.db.get_item("COURSE")
        self._headingSelect = item.value
        item.valueChanged[float].connect(self.setHeadingBug)
        self._courseSelect = 1

        self.cdidb = fix.db.get_item("CDI")
        self._courseDeviation = self.cdidb.value
        self.cdidb.valueChanged[float].connect(self.setCdi)
        self._showCDI = not self.cdidb.old

        self.gsidb = fix.db.get_item("GSI")
        self._glideSlopeIndicator = self.gsidb.value
        self.gsidb.valueChanged[float].connect(self.setGsi)
        self._showGSI = not self.gsidb.old
        self.cardinal = ["N", "E", "S", "W"]

        self.item = fix.db.get_item("HEAD")
        self._heading = self.item.value
        self.item.valueChanged[float].connect(self.setHeading)
        self.heading_bug = None
        self.item.failChanged[bool].connect(self.setFail)
        self._fail = False
        self.myparent = parent
        self.update_period = None

    def resizeEvent(self, event):
        self.update_period = self.myparent.get_config_item('update_period')
        if self.update_period is None:
            self.update_period = .1
        self.last_update_time = 0
        self.scene = QGraphicsScene(0, 0, self.width(), self.height())
        self.cx = self.width() / 2
        self.cy = self.height() / 2
        self.r = self.height() / 2 - 5
        self.cdippw = self.r * .5
        self.gsipph = self.r * .5

        # Setup Pens
        compassPen = QPen(QColor(self.fg_color))
        compassBrush = QBrush(QColor(self.bg_color))
        nobrush = QBrush()

        headingPen = QPen(QColor(Qt.red))
        headingBrush = QBrush(QColor(Qt.red))
        headingPen.setWidth(2)

        cdiPen = QPen(QColor(Qt.yellow))
        cdiPen.setWidth(3)

        f = QFont()
        f.setBold(True)
        f.setFamily ("Sans")
        f.setPixelSize(self.fontSize)
        self.scene.setFont(f)

        # Compass Setup
        self.scene.addEllipse(self.cx-self.r, self.cy-self.r, self.r*2, self.r*2,
                                compassPen, nobrush)

        refsize = self.fontSize*.7
        self.labels = list()
        for count in range(0, 360, 5):
            angle = (count) * math.pi / 180
            cosa = math.cos(angle)
            sina = math.sin(angle)
            iy1 = -self.r
            iy2 = -self.r + refsize
            if count % 10 != 0:
                iy2 -= refsize/2
            x1 = (-iy1*sina) + self.cx # (ix*cosa - iy*sina) ix factor removed Since x is 0
            y1 = iy1*cosa + self.cy # (iy*cosa + ix*sina)
            x2 = (-iy2*sina) + self.cx
            y2 = iy2*cosa + self.cy
            self.scene.addLine(x1, y1, x2, y2, compassPen)
            if count % 90 == 0:
                t = self.scene.addSimpleText(self.cardinal[int(count / 90)])
                t.setRotation(count)
                t.setPen(compassPen)
                iy3 = -self.r + refsize*1.1
                ix3 = -refsize/2
                x3 = (ix3*cosa - iy3*sina) + self.cx
                y3 = (iy3*cosa + ix3*sina) + self.cy
                t.setPos(x3, y3)
                self.labels.append(t)
            elif count % 30 == 0:
                text = str(int(count / 10))
                t = self.scene.addSimpleText(text)
                t.setRotation(count)
                t.setPen(compassPen)
                iy3 = -self.r + refsize*1.1
                ix3 = -refsize*len(text)/2
                x3 = (ix3*cosa - iy3*sina) + self.cx
                y3 = (iy3*cosa + ix3*sina) + self.cy
                t.setPos(x3, y3)
                self.labels.append(t)

        #Draw Heading Bug
        triangle = self.heading_bug_polygon()
        self.heading_bug = self.scene.addPolygon(triangle, headingPen, headingBrush)

        self.setScene(self.scene)
        self.rotate(-self._heading)
        self.setFail(self.item.fail)

    def heading_bug_polygon(self):
        inc = int(self.fontSize / 2 * 0.8)
        iyb = -self.r
        points = [ (inc, -self.r - inc/2),
                  (-inc, -self.r - inc/2),
                  (0, -self.r + (inc/2))]
        angle = (self._headingSelect) * math.pi / 180
        cosa = math.cos(angle)
        sina = math.sin(angle)

        points = [((ix*cosa - iy*sina), (iy*cosa + ix*sina)) for ix,iy in points]
        points = [QPointF((ix + self.cx), (iy + self.cy)) for ix,iy in points]
        triangle = QPolygonF(points)
        return triangle

    def paintEvent(self, event):
        super(HSI, self).paintEvent(event)
        c = QPainter(self.viewport())
        compassPen = QPen(QColor(self.fg_color))
        compassBrush = QBrush(QColor(self.bg_color))
        cdiPen = QPen(QColor(Qt.yellow))
        cdiPen.setWidth(3)
        c.setRenderHint(QPainter.Antialiasing)

        #Non-moving items
        c.setPen(cdiPen)
        c.drawLine(self.cx, self.cy - self.r - 5,
                   self.cx, self.cy - self.r + self.fontSize*2)
        c.drawLine(self.cx, self.cy + self.r - self.fontSize,
                   self.cx, self.cy + self.r - self.fontSize*2)
        c.drawLine(self.cx + self.r - self.fontSize, self.cy,
                   self.cx + self.r - self.fontSize*2, self.cy)
        c.drawLine(self.cx - self.r + self.fontSize, self.cy,
                   self.cx - self.r + self.fontSize*2, self.cy)

        # GSI index tics
        c.setPen(compassPen)
        deviation = -1.0
        while deviation <= 1.0:
            c.drawLine(self.cx - 5, self.cy + deviation*self.gsipph,
                       self.cx + 5, self.cy + deviation*self.gsipph)
            c.drawLine(self.cx + deviation*self.cdippw, self.cy - 5,
                       self.cx + deviation*self.cdippw, self.cy + 5)
            deviation += 1.0/3.0

        c.setPen(cdiPen)
        self._showCDI = not self.cdidb.old
        if self._showCDI:
            x = self.cx + self._courseDeviation * self.cdippw
            c.drawLine(x, self.cy + self.r - self.fontSize*2 - 6,
                   x, self.cy - self.r + self.fontSize*2 + 6)

        self._showGSI = not self.gsidb.old
        if self._showGSI:
            y = self.cy - self._glideSlopeIndicator * self.gsipph
            c.drawLine(self.cx + self.r - self.fontSize*2 - 6, y,
                   self.cx - self.r + self.fontSize*2 + 6, y)

    def getHeading(self):
        return self._heading

    def setHeading(self, heading):
        if not self.isVisible():
            return
        if heading != self._heading:
            now = time.time()
            if now - self.last_update_time >= self.update_period:
                newheading = common.bounds(0, 360, heading)
                diff = newheading - self._heading
                if diff > 180:
                    diff -= 360
                elif diff < -180:
                    diff += 360
                self._heading = newheading
                self.rotate(-diff)
                self.last_update_time = now

    heading = property(getHeading, setHeading)

    def setFail(self, fail):
        if fail != self._fail:
            self._fail = fail
            if self.isVisible():
                if fail:
                    for l in self.labels:
                        l.setOpacity(0)
                else:
                    for l in self.labels:
                        l.setOpacity(1)

    def getHeadingBug(self):
        return self._headingSelect

    def setHeadingBug(self, headingBug):
        if headingBug != self._headingSelect:
            self._headingSelect = common.bounds(0, 360, headingBug)
            if self.heading_bug is not None:
                triangle = self.heading_bug_polygon()
                self.heading_bug.setPolygon(triangle)

    headingBug = property(getHeadingBug, setHeadingBug)

    def getCdi(self):
        return self._courseDeviation

    def setCdi(self, cdi):
        if cdi != self._courseDeviation:
            self._courseDeviation = cdi
            self.update()

    cdi = property(getCdi, setCdi)

    def getGsi(self):
        return self._glideSlopeIndicator

    def setGsi(self, gsi):
        if gsi != self._glideSlopeIndicator:
            self._glideSlopeIndicator = gsi
            self.update()

    gsi = property(getGsi, setGsi)

class HeadingDisplay(QWidget):
    def __init__(self, parent=None, font_size=15, fgcolor=Qt.black, bgcolor=Qt.white):
        super(HeadingDisplay, self).__init__(parent)
        self.setFocusPolicy(Qt.NoFocus)
        self.fontSize = font_size
        self.fg_color = fgcolor
        self.bg_color = bgcolor

        self.item = fix.db.get_item("HEAD")
        self._heading = self.item.value
        self.item.valueChanged[float].connect(self.setHeading)
        self.item.failChanged[bool].connect(self.setFail)
        self.item.badChanged[bool].connect(self.setBad)
        self.item.oldChanged[bool].connect(self.setOld)
        self._bad = self.item.bad
        self._old = self.item.old
        self._fail = self.item.fail

        self.font = QFont()
        self.font.setBold(True)
        self.font.setFamily ("Sans")
        self.font.setPixelSize(self.fontSize)
        t = QGraphicsSimpleTextItem ("999")
        t.setFont (self.font)
        br = t.boundingRect()
        self.resize(br.width()*1.2, br.height()*1.2)

    def paintEvent(self, event):
        c = QPainter(self)
        compassPen = QPen(QColor(self.fg_color))
        compassBrush = QBrush(QColor(self.bg_color))
        c.setPen(compassPen)
        c.setFont(self.font)
        tr = QRect(0, 0, self.width(), self.height())
        c.drawRect(tr)
        if self._fail:
            heading_text = "XXX"
            c.setBrush(QBrush(QColor(Qt.red)))
            c.setPen(QPen(QColor(Qt.red)))
        elif self._bad:
            heading_text = ""
            c.setBrush(QBrush(QColor(255, 150, 0)))
            c.setPen(QPen(QColor(255, 150, 0)))
        elif self._old:
            heading_text = ""
            c.setBrush(QBrush(QColor(255, 150, 0)))
            c.setPen(QPen(QColor(255, 150, 0)))
        else:
            heading_text = str(int(self._heading))

        c.drawText(tr, Qt.AlignHCenter | Qt.AlignVCenter, heading_text)

    def getHeading(self):
        return self._heading

    def setHeading(self, heading):
        if heading != self._heading:
            self._heading = common.bounds(0, 360, heading)
            self.update()

    heading = property(getHeading, setHeading)

    def setFail(self, fail):
        self._fail = fail
        self.repaint()

    def setOld(self, old):
        self._old = old
        self.repaint()

    def setBad(self, bad):
        self._bad = bad
        self.repaint()

class DG_Tape(QGraphicsView):
    def __init__(self, parent=None):
        super(DG_Tape, self).__init__(parent)
        self.setStyleSheet("border: 0px")
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setRenderHint(QPainter.Antialiasing)
        self.setFocusPolicy(Qt.NoFocus)
        self.fontsize = 20
        self._heading = 1
        self._headingSelect = 1
        self._courseSelect = 1
        self._courseDevation = 1
        self.cardinal = ["N", "E", "S", "W", "N"]

        item = fix.db.get_item("HEAD", True)
        item.valueChanged[float].connect(self.setHeading)

        #fix.db.get_item("COURSE", True).valueChanged[float].connect(self.setHeadingBug)

    def resizeEvent(self, event):
        w = self.width()
        h = self.height()

        self.dpp = 10
        compassPen = QPen(QColor(Qt.white))
        compassPen.setWidth(2)

        headingPen = QPen(QColor(Qt.red))
        headingPen.setWidth(8)

        f = QFont()
        f.setPixelSize(self.fontsize)

        self.scene = QGraphicsScene(0, 0, 5000, h)
        self.scene.addRect(0, 0, 5000, h,
                           QPen(QColor(Qt.black)), QBrush(QColor(Qt.black)))

        self.setScene(self.scene)

        for i in range(-50, 410, 5):
            if i % 10 == 0:
                self.scene.addLine((i * 10) + w / 2, 0, (i * 10) + w / 2, h / 2,
                                   compassPen)
                if i > 360:
                    t = self.scene.addText(str(i - 360))
                    t.setFont(f)
                    self.scene.setFont(f)
                    t.setDefaultTextColor(QColor(Qt.white))
                    t.setX(((i * 10) + w / 2) - t.boundingRect().width() / 2)
                    t.setY(h - t.boundingRect().height())
                elif i < 1:
                    t = self.scene.addText(str(i + 360))
                    t.setFont(f)
                    self.scene.setFont(f)
                    t.setDefaultTextColor(QColor(Qt.white))
                    t.setX(((i * 10) + w / 2) - t.boundingRect().width() / 2)
                    t.setY(h - t.boundingRect().height())
                else:
                    if i % 90 == 0:
                        t = self.scene.addText(self.cardinal[int(i / 90)])
                        t.setFont(f)
                        self.scene.setFont(f)
                        t.setDefaultTextColor(QColor(Qt.cyan))
                        t.setX(((i * 10) + w / 2) - t.boundingRect().width() / 2)
                        t.setY(h - t.boundingRect().height())
                    else:
                        t = self.scene.addText(str(i))
                        t.setFont(f)
                        self.scene.setFont(f)
                        t.setDefaultTextColor(QColor(Qt.white))
                        t.setX(((i * 10) + w / 2) - t.boundingRect().width() / 2)
                        t.setY(h - t.boundingRect().height())
            else:
                self.scene.addLine((i * 10) + w / 2, 0,
                                   (i * 10) + w / 2, h / 2 - 20,
                                    compassPen)

    def redraw(self):
        self.resetTransform()
        self.centerOn(self._heading * self.dpp + self.width() / 2,
                      self.scene.height() / 2)

    def getHeading(self):
        return self._heading

    def setHeading(self, heading):
        if heading != self._heading:
            self._heading = heading
            self.redraw()

    heading = property(getHeading, setHeading)
