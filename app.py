import sys, math, platform, psutil
from datetime import datetime
try:
    from zoneinfo import ZoneInfo
    HAS_ZONEINFO = True
except Exception:
    ZoneInfo = None
    HAS_ZONEINFO = False

from PyQt6.QtCore import Qt, QTimer, QPointF, QRectF, QSize, QEvent
from PyQt6.QtGui import QPainter, QColor, QFont, QPen, QBrush, QIcon, QPixmap, QAction
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QMainWindow, QSizeGrip,
    QPushButton, QMenu, QColorDialog, QSystemTrayIcon, QInputDialog, QMessageBox
)

# --- helpers
def polar_point(r, angle_deg):
    rad = math.radians(angle_deg - 90)
    return QPointF(r * math.cos(rad), r * math.sin(rad))

def deg_to_qt(deg):
    return int(-deg * 16)

# --- Watch drawing widget (analog + battery ring + date)
class WatchWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMinimumSize(320, 320)

        self.BASE = 400
        self.tick_radius = 184
        self.num_dist = 136
        self.num_font = 92
        self.date_y = -60
        self.date_font = 20
        self.battery_y = 110
        self.battery_r = 46
        self.battery_thick = 10

        self.num_offsets = {0: QPointF(0, +8), 90: QPointF(-6, 0), 270: QPointF(+6, 0)}

        self.default_colors = {
            "num_color": QColor(180, 215, 235),
            "tick_color": QColor(155, 185, 200),
            "hour_color": QColor(135, 170, 190),
            "min_color": QColor(200, 225, 245),
            "sec_color": QColor(200, 240, 255, 220),
            "batt_bg": QColor(95, 125, 145, 120),
        }

        self.num_color = QColor(self.default_colors["num_color"])
        self.tick_color = QColor(self.default_colors["tick_color"])
        self.hour_color = QColor(self.default_colors["hour_color"])
        self.min_color = QColor(self.default_colors["min_color"])
        self.sec_color = QColor(self.default_colors["sec_color"])
        self.batt_bg = QColor(self.default_colors["batt_bg"])
        self.center_dot = QColor(240, 250, 255)

        self.show_battery = True
        self.show_ticks = True
        self.timezone_name = None
        self.timezone = None

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._on_tick)
        self.timer.start(40)
        self.charge_phase = 0.0

    def reset_colors(self):
        for k, v in self.default_colors.items():
            setattr(self, k, QColor(v))

    def set_timezone(self, tz_name):
        if tz_name is None:
            self.timezone_name = None
            self.timezone = None
            return True
        if not HAS_ZONEINFO:
            return False
        try:
            tz = ZoneInfo(tz_name)
            self.timezone_name = tz_name
            self.timezone = tz
            return True
        except Exception:
            return False

    def _on_tick(self):
        try:
            batt = psutil.sensors_battery()
        except Exception:
            batt = None
        if batt and getattr(batt, "power_plugged", False):
            self.charge_phase = (self.charge_phase + 6.0) % 360.0
        else:
            self.charge_phase *= 0.9
        self.update()

    def _get_now(self):
        if self.timezone:
            return datetime.now(self.timezone)
        return datetime.now()

    def sizeHint(self):
        return QSize(420, 420)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        side = min(w, h)
        scale = side / self.BASE
        p.translate(w / 2.0, h / 2.0)
        p.scale(scale, scale)

        if self.show_ticks:
            self._draw_ticks(p)
        self._draw_numerals(p)
        self._draw_date(p)
        if self.show_battery:
            self._draw_battery(p)
        self._draw_hands(p)
        self._draw_center(p)
        p.end()

    def _draw_ticks(self, p):
        p.save()
        pen = QPen(self.tick_color)
        pen.setWidthF(3.0)
        p.setPen(pen)
        r = self.tick_radius
        for i in range(60):
            angle = math.radians(i * 6)
            ax, ay = math.cos(angle - math.pi / 2), math.sin(angle - math.pi / 2)
            length = 12 if i % 5 == 0 else 6
            ix, iy = (r - length) * ax, (r - length) * ay
            ox, oy = r * ax, r * ay
            p.drawLine(QPointF(ix, iy), QPointF(ox, oy))
        p.restore()

    def _draw_numerals(self, p):
        p.save()
        p.setPen(self.num_color)
        fontbig = QFont("Segoe UI", self.num_font, QFont.Weight.Bold)
        p.setFont(fontbig)
        fm = p.fontMetrics()

        def draw_text(angle_deg, text):
            pos = polar_point(self.num_dist, angle_deg)
            off = self.num_offsets.get(angle_deg, QPointF(0, 0))
            pos += off
            w = fm.horizontalAdvance(text)
            h = fm.height()
            rect = QRectF(pos.x() - w / 2.0, pos.y() - h / 2.0, w, h)
            glow = QColor(self.num_color)
            glow.setAlpha(50)
            p.setPen(glow)
            p.drawText(rect.translated(0, -4), Qt.AlignmentFlag.AlignCenter, text)
            p.setPen(self.num_color)
            p.drawText(rect, Qt.AlignmentFlag.AlignCenter, text)

        draw_text(0, "12")
        draw_text(90, "3")
        draw_text(270, "9")
        p.restore()

    def _draw_date(self, p):
        now = self._get_now()
        date_str = now.strftime("%d %b")
        p.save()
        font = QFont("Segoe UI", self.date_font, QFont.Weight.DemiBold)
        p.setFont(font)
        p.setPen(self.num_color)
        rect = QRectF(-80, self.date_y - 14, 160, 28)
        p.drawText(rect, Qt.AlignmentFlag.AlignCenter, date_str)
        p.restore()

    def _draw_battery(self, p):
        p.save()
        p.translate(0, self.battery_y)
        percent, plugged = 100, False
        try:
            batt = psutil.sensors_battery()
            if batt:
                percent = max(0, min(100, int(batt.percent)))
                plugged = bool(batt.power_plugged)
        except Exception:
            pass

        r, thickness = self.battery_r, self.battery_thick
        rect = QRectF(-r, -r, 2 * r, 2 * r)

        pen_bg = QPen(self.batt_bg)
        pen_bg.setWidthF(thickness)
        p.setPen(pen_bg)
        p.drawArc(rect, deg_to_qt(-210), deg_to_qt(240))

        p.setPen(QPen(self.min_color, thickness + 1))
        sweep = 240.0 * (percent / 100.0)
        p.drawArc(rect, deg_to_qt(-210), deg_to_qt(sweep))

        if plugged:
            phase = self.charge_phase
            pen_ch = QPen(QColor(210, 245, 255, 180), thickness + 2)
            pen_ch.setCapStyle(Qt.PenCapStyle.RoundCap)
            p.setPen(pen_ch)
            p.drawArc(rect, deg_to_qt(-210 + (phase % 360)), deg_to_qt(50))

        p.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        p.setPen(self.min_color)
        p.drawText(QRectF(-30, -18, 60, 36), Qt.AlignmentFlag.AlignCenter, f"{percent}%")
        p.restore()

    def _draw_hands(self, p):
        now = self._get_now()
        hour_val = (now.hour % 12) + now.minute / 60.0 + now.second / 3600.0
        minute_val = now.minute + now.second / 60.0
        second_val = now.second + now.microsecond / 1_000_000.0
        hour_angle = 30.0 * hour_val
        minute_angle = 6.0 * minute_val
        second_angle = 6.0 * second_val

        p.save()
        p.rotate(hour_angle - 90)
        p.setBrush(QBrush(self.hour_color))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(QRectF(-8, -9, 92, 18), 10, 10)
        p.restore()

        p.save()
        p.rotate(minute_angle - 90)
        p.setBrush(QBrush(self.min_color))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(QRectF(-7, -8, 145, 16), 10, 10)
        p.restore()

        p.save()
        p.rotate(second_angle - 90)
        pen = QPen(self.sec_color)
        pen.setWidthF(3.0)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        p.drawLine(QPointF(0, 0), QPointF(160, 0))
        p.restore()

    def _draw_center(self, p):
        p.save()
        p.setBrush(QBrush(self.center_dot))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QPointF(0, 0), 8, 8)
        p.restore()


# --- Main Window
class FramelessWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.watch = WatchWidget(self)
        layout = QVBoxLayout()
        layout.addWidget(self.watch)
        layout.setContentsMargins(10, 10, 10, 10)
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self._size_grip = QSizeGrip(self)
        self._size_grip.setFixedSize(18, 18)
        self._size_grip.show()

        self.hamburger_btn = QPushButton(self)
        self.hamburger_btn.setFixedSize(36, 28)
        self.hamburger_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.hamburger_btn.setStyleSheet("QPushButton { background: rgba(0,0,0,0); border: none; }")
        self.hamburger_btn.setIcon(self._create_hamburger_icon(28, 20))
        self.hamburger_btn.setIconSize(QSize(28, 20))
        self.hamburger_btn.clicked.connect(self._show_menu)

        # Menu setup
        self.menu = QMenu(self)
        act_color = QAction("Change Clock Color", self)
        act_color.triggered.connect(self._pick_whole_color)
        self.menu.addAction(act_color)
        self.menu.addSeparator()

        self.act_batt = QAction("Toggle Battery Ring", self, checkable=True, checked=self.watch.show_battery)
        self.act_batt.triggered.connect(lambda c: self._toggle("battery", c))
        self.menu.addAction(self.act_batt)

        self.act_ticks = QAction("Toggle Ticks", self, checkable=True, checked=self.watch.show_ticks)
        self.act_ticks.triggered.connect(lambda c: self._toggle("ticks", c))
        self.menu.addAction(self.act_ticks)
        self.menu.addSeparator()

        self.act_top = QAction("Always on Top", self, checkable=True)
        self.act_top.triggered.connect(self._toggle_top)
        self.menu.addAction(self.act_top)
        self.menu.addSeparator()

        # Timezone submenu
        tz_menu = QMenu("Set Timezone", self.menu)
        presets = {
            "Local Time": None,
            "UTC": "UTC",
            "Mumbai (Asia/Kolkata)": "Asia/Kolkata",
            "New York": "America/New_York",
            "London": "Europe/London",
            "Tokyo": "Asia/Tokyo"
        }
        for label, tz in presets.items():
            act = QAction(label, self)
            act.triggered.connect(lambda _, t=tz: self._set_timezone(t))
            tz_menu.addAction(act)
        custom = QAction("Custom (IANA Name)...", self)
        custom.triggered.connect(self._custom_timezone)
        tz_menu.addAction(custom)
        self.menu.addMenu(tz_menu)
        self.menu.addSeparator()

        act_hide = QAction("Hide (to tray)", self)
        act_hide.triggered.connect(self._hide_to_tray)
        self.menu.addAction(act_hide)
        self.menu.addSeparator()

        act_reset = QAction("Reset Colors & Settings", self)
        act_reset.triggered.connect(self._reset_settings)
        self.menu.addAction(act_reset)

        act_exit = QAction("Exit", self)
        act_exit.triggered.connect(self.close)
        self.menu.addAction(act_exit)

        # Tray
        self.tray = None
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray = QSystemTrayIcon(self)
            self.tray.setIcon(self._create_tray_icon())
            tray_menu = QMenu()
            restore = QAction("Restore", self)
            restore.triggered.connect(self._restore)
            tray_menu.addAction(restore)
            quit = QAction("Quit", self)
            quit.triggered.connect(self.close)
            tray_menu.addAction(quit)
            self.tray.setContextMenu(tray_menu)
            self.tray.activated.connect(self._tray_clicked)
            self.tray.show()

        self.installEventFilter(self)
        self.watch.installEventFilter(self)
        self.resize(460, 460)
        self._drag_pos = None

    # --- Hamburger icon that can change color
    def _create_hamburger_icon(self, w, h, color=None):
        pix = QPixmap(w, h)
        pix.fill(Qt.GlobalColor.transparent)
        p = QPainter(pix)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        c = color if color else QColor(200, 225, 245)
        pen = QPen(c)
        pen.setWidthF(4.0)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        spacing = h / 3
        for i in range(3):
            y = spacing * (i + 0.5)
            p.drawLine(QPointF(3, y), QPointF(w - 3, y))
        p.end()
        return QIcon(pix)

    def _create_tray_icon(self):
        size = 64
        pix = QPixmap(size, size)
        pix.fill(Qt.GlobalColor.transparent)
        p = QPainter(pix)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setBrush(QBrush(self.watch.num_color))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(8, 8, size - 16, size - 16)
        p.end()
        return QIcon(pix)

    def _show_menu(self):
        pos = self.hamburger_btn.mapToGlobal(self.hamburger_btn.rect().bottomLeft())
        self.menu.exec(pos)

    # --- Color sync: clock + hamburger
    def _pick_whole_color(self):
        cur = self.watch.num_color
        col = QColorDialog.getColor(cur, self, "Pick clock base color")
        if not col.isValid():
            return
        base = QColor(col)

        num = base.lighter(140)
        tick = base.darker(115)
        min_c = base.lighter(110)
        hour = base.darker(140)
        sec = QColor(base.red(), base.green(), base.blue(), 220)
        batt = QColor(base.darker(160))
        batt.setAlpha(120)

        self.watch.num_color, self.watch.tick_color = num, tick
        self.watch.min_color, self.watch.hour_color = min_c, hour
        self.watch.sec_color, self.watch.batt_bg = sec, batt

        # 🔹 Update hamburger icon color
        self.hamburger_btn.setIcon(self._create_hamburger_icon(28, 20, num))

        if self.tray:
            self.tray.setIcon(self._create_tray_icon())

        self.watch.update()

    def _toggle(self, what, checked):
        if what == "battery":
            self.watch.show_battery = checked
        elif what == "ticks":
            self.watch.show_ticks = checked
        self.watch.update()

    def _toggle_top(self, checked):
        flags = self.windowFlags()
        if checked:
            self.setWindowFlags(flags | Qt.WindowType.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(flags & ~Qt.WindowType.WindowStaysOnTopHint)
        self.show()

    def _hide_to_tray(self):
        if self.tray:
            self.hide()
            self.tray.showMessage("Clock hidden", "Click tray icon to restore", QSystemTrayIcon.MessageIcon.Information, 2000)

    def _restore(self):
        self.showNormal()
        self.activateWindow()

    def _tray_clicked(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self._restore()

    def _set_timezone(self, tz):
        if not HAS_ZONEINFO:
            QMessageBox.warning(self, "Timezone", "Timezone support requires Python 3.9+.")
            return
        ok = self.watch.set_timezone(tz)
        if ok:
            QMessageBox.information(self, "Timezone", f"Timezone set to {tz or 'Local Time'}.")
        else:
            QMessageBox.warning(self, "Timezone", "Invalid timezone name.")

    def _custom_timezone(self):
        tz, ok = QInputDialog.getText(self, "Custom Timezone", "Enter IANA name (e.g. America/New_York):")
        if ok and tz:
            self._set_timezone(tz.strip())

    def _reset_settings(self):
        self.watch.reset_colors()
        self.watch.show_battery = True
        self.watch.show_ticks = True
        self.act_batt.setChecked(True)
        self.act_ticks.setChecked(True)
        self.hamburger_btn.setIcon(self._create_hamburger_icon(28, 20))
        if self.tray:
            self.tray.setIcon(self._create_tray_icon())
        self.watch.update()

    def eventFilter(self, obj, e):
        if e.type() == QEvent.Type.MouseButtonPress:
            if e.button() == Qt.MouseButton.LeftButton and not self.hamburger_btn.geometry().contains(e.position().toPoint()):
                self._drag_pos = e.globalPosition().toPoint() - self.frameGeometry().topLeft()
                return True
        elif e.type() == QEvent.Type.MouseMove and self._drag_pos is not None:
            self.move(e.globalPosition().toPoint() - self._drag_pos)
            return True
        elif e.type() == QEvent.Type.MouseButtonRelease:
            self._drag_pos = None
            return True
        return super().eventFilter(obj, e)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        margin = 8
        bx = self.width() - self.hamburger_btn.width() - margin - self._size_grip.width()
        by = margin
        self.hamburger_btn.move(bx, by)
        self._size_grip.move(self.width() - self._size_grip.width() - margin,
                            self.height() - self._size_grip.height() - margin)


def main():
    app = QApplication(sys.argv)
    win = FramelessWindow()
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
