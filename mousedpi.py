#!/usr/bin/env python3
"""MouseDPI — маленькая настройка игровой мышки (DPI, частота опроса, подсветка) через libratbag.

Нужна служба ratbagd (пакет libratbag-ratbagd). Настройки записываются в память мышки,
поэтому работают и без программы, и на другом компьютере.
"""
import re
import subprocess
import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QIcon
from PySide6.QtWidgets import (
    QApplication, QButtonGroup, QCheckBox, QColorDialog, QComboBox, QFormLayout, QGroupBox, QHBoxLayout, QLabel,
    QMessageBox, QPushButton, QRadioButton, QSlider, QVBoxLayout, QWidget,
)

APP = "MouseDPI"
COLORS = {"bg": "#1a1b26", "panel": "#24283b", "line": "#3b4261", "text": "#c0caf5", "dim": "#7a83aa",
          "accent": "#7aa2f7"}
STYLE = f"""
QWidget {{ background: {COLORS['bg']}; color: {COLORS['text']}; font-size: 14px; }}
QGroupBox {{ background: {COLORS['panel']}; border: 1px solid {COLORS['line']}; border-radius: 8px;
            margin-top: 14px; padding: 12px; }}
QGroupBox::title {{ subcontrol-origin: margin; left: 12px; padding: 0 4px; color: {COLORS['accent']}; }}
QGroupBox QWidget {{ background: {COLORS['panel']}; }}
QLabel#hint {{ color: {COLORS['dim']}; font-size: 12px; }}
QLabel#dpi {{ font-weight: bold; min-width: 80px; }}
QComboBox, QPushButton {{ background: {COLORS['bg']}; border: 1px solid {COLORS['line']}; border-radius: 6px;
                         padding: 6px 10px; }}
QPushButton:hover, QComboBox:hover {{ border-color: {COLORS['accent']}; }}
QPushButton#primary {{ background: {COLORS['accent']}; color: {COLORS['bg']}; border: none; font-weight: bold; }}
QComboBox QAbstractItemView {{ background: {COLORS['panel']}; selection-background-color: {COLORS['line']}; }}
QSlider::groove:horizontal {{ height: 4px; background: {COLORS['line']}; border-radius: 2px; }}
QSlider::handle:horizontal {{ background: {COLORS['accent']}; width: 14px; margin: -6px 0; border-radius: 7px; }}
"""
LED_NAMES = ["Логотип", "Полоска DPI"]
LED_MODES = {"on": "Горит", "breathing": "Дышит", "cycle": "Радуга", "off": "Выключена"}


def rb(*args):
    r = subprocess.run(["ratbagctl", *args], capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(f"ratbagctl {' '.join(args)}: {r.stderr.strip() or r.stdout.strip()}")
    return r.stdout


def find_device():
    out = rb("list")
    m = re.match(r"(\S+):\s+(.*)", out.strip())
    return (m.group(1), m.group(2).strip()) if m else (None, None)


def read_profile(dev, n):
    """Разбирает «ratbagctl DEV profile N get» в словарь."""
    out = rb(dev, "profile", str(n), "get")
    p = {"res": [], "rate": None, "leds": []}
    m = re.search(r"Report Rate: (\d+)Hz", out)
    p["rate"] = int(m.group(1)) if m else None
    for m in re.finditer(r"^\s+(\d+): (\d+)dpi(.*)$", out, re.M):
        flags = m.group(3)
        p["res"].append({"dpi": int(m.group(2)), "active": "active" in flags, "default": "default" in flags,
                         "disabled": "disabled" in flags})
    for m in re.finditer(r"LED: (\d+), depth: \w+, mode: (\w+)(?:, color: (\w+))?", out):
        p["leds"].append({"mode": m.group(2), "color": m.group(3) or "ffffff"})
    return p


def hint(text):
    lbl = QLabel(text)
    lbl.setObjectName("hint")
    lbl.setWordWrap(True)
    return lbl


class Window(QWidget):
    def __init__(self, dev, name):
        super().__init__()
        self.dev = dev
        self.setWindowTitle(APP)
        self.setWindowIcon(QIcon.fromTheme("input-mouse"))
        self.resize(560, 640)
        self.dpis = [int(x) for x in rb(dev, "dpi", "get-all").split()]
        self.rates = [int(x) for x in rb(dev, "rate", "get-all").split()]
        self.profile = int(rb(dev, "profile", "active", "get").strip())

        root = QVBoxLayout(self)
        root.addWidget(QLabel(f"<span style='font-size:20px; font-weight:bold'>{name}</span>"))
        row = QHBoxLayout()
        row.addWidget(QLabel("Профиль"))
        self.profile_combo = QComboBox()
        n_profiles = int(re.search(r"Number of Profiles: (\d+)", rb(dev, "info")).group(1))
        for i in range(n_profiles):
            self.profile_combo.addItem(f"Профиль {i + 1}", i)
        self.profile_combo.setCurrentIndex(self.profile)
        self.profile_combo.currentIndexChanged.connect(self.load)
        row.addWidget(self.profile_combo, 1)
        root.addLayout(row)

        box = QGroupBox("DPI")
        self.dpi_form = QVBoxLayout(box)
        root.addWidget(box)
        box_rate = QGroupBox("Частота опроса")
        f = QHBoxLayout(box_rate)
        self.rate_combo = QComboBox()
        for r in self.rates:
            self.rate_combo.addItem(f"{r} Гц", r)
        f.addWidget(self.rate_combo)
        root.addWidget(box_rate)

        box_led = QGroupBox("Подсветка")
        self.led_form = QFormLayout(box_led)
        root.addWidget(box_led)

        self.status = hint("")
        btn = QPushButton("Записать в мышку")
        btn.setObjectName("primary")
        btn.clicked.connect(self.save)
        bottom = QHBoxLayout()
        bottom.addWidget(self.status, 1)
        bottom.addWidget(btn)
        root.addStretch(1)
        root.addLayout(bottom)
        self.load()

    def load(self):
        self.profile = self.profile_combo.currentData()
        p = read_profile(self.dev, self.profile)
        self.p = p
        while self.dpi_form.count():
            item = self.dpi_form.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                lay = item.layout()
                while lay.count():
                    w = lay.takeAt(0).widget()
                    if w:
                        w.deleteLater()
        self.rows = []
        self.active_group = QButtonGroup(self)
        for i, r in enumerate(p["res"]):
            line = QHBoxLayout()
            on = QCheckBox()
            on.setChecked(not r["disabled"])
            on.setToolTip("Включён этот уровень (переключается кнопками DPI на мышке)")
            radio = QRadioButton()
            radio.setChecked(r["active"])
            radio.setToolTip("Сейчас выбран")
            self.active_group.addButton(radio, i)
            slider = QSlider(Qt.Horizontal)
            slider.setRange(0, len(self.dpis) - 1)
            slider.setValue(min(range(len(self.dpis)), key=lambda k: abs(self.dpis[k] - r["dpi"])))
            label = QLabel()
            label.setObjectName("dpi")
            slider.valueChanged.connect(lambda v, lb=label: lb.setText(f"{self.dpis[v]} DPI"))
            label.setText(f"{self.dpis[slider.value()]} DPI")
            line.addWidget(on)
            line.addWidget(radio)
            line.addWidget(slider, 1)
            line.addWidget(label)
            self.dpi_form.addLayout(line)
            self.rows.append((on, radio, slider))
        self.dpi_form.addWidget(hint("Галочка — уровень включён, кружок — какой выбран сейчас. "
                                     "Кнопки DPI на мышке листают включённые уровни."))
        if p["rate"] in self.rates:
            self.rate_combo.setCurrentIndex(self.rates.index(p["rate"]))

        while self.led_form.rowCount():
            self.led_form.removeRow(0)
        self.leds = []
        for i, led in enumerate(p["leds"]):
            mode = QComboBox()
            for k, v in LED_MODES.items():
                mode.addItem(v, k)
            mode.setCurrentIndex(max(0, mode.findData(led["mode"])))
            color_btn = QPushButton()
            color_btn.setFixedWidth(60)
            color_btn.setProperty("color", led["color"])
            color_btn.setStyleSheet(f"background: #{led['color']};")
            color_btn.clicked.connect(lambda _=False, b=color_btn: self.pick_color(b))
            row = QHBoxLayout()
            row.addWidget(mode, 1)
            row.addWidget(color_btn)
            self.led_form.addRow(LED_NAMES[i] if i < len(LED_NAMES) else f"Свет {i}", row)
            self.leds.append((mode, color_btn))
        self.status.setText("")

    def pick_color(self, btn):
        c = QColorDialog.getColor(QColor(f"#{btn.property('color')}"), self, "Цвет подсветки")
        if c.isValid():
            hexc = c.name()[1:]
            btn.setProperty("color", hexc)
            btn.setStyleSheet(f"background: #{hexc};")

    def save(self):
        d, pr = self.dev, str(self.profile)
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            for i, (on, radio, slider) in enumerate(self.rows):
                old = self.p["res"][i]
                dpi = self.dpis[slider.value()]
                if dpi != old["dpi"]:
                    rb(d, "profile", pr, "resolution", str(i), "dpi", "set", str(dpi))
                if on.isChecked() == old["disabled"] and not radio.isChecked():
                    rb(d, "profile", pr, "resolution", str(i), "enabled" if on.isChecked() else "disabled", "set")
            active = self.active_group.checkedId()
            if active >= 0 and not self.p["res"][active]["active"]:
                rb(d, "profile", pr, "resolution", "active", "set", str(active))
            rate = self.rate_combo.currentData()
            if rate != self.p["rate"]:
                rb(d, "profile", pr, "rate", "set", str(rate))
            for i, (mode, btn) in enumerate(self.leds):
                old = self.p["leds"][i]
                if mode.currentData() != old["mode"]:
                    rb(d, "profile", pr, "led", str(i), "set", "mode", mode.currentData())
                if btn.property("color") != old["color"] and mode.currentData() in ("on", "breathing"):
                    rb(d, "profile", pr, "led", str(i), "set", "color", btn.property("color"))
            if self.profile != int(rb(d, "profile", "active", "get").strip()):
                rb(d, "profile", "active", "set", pr)
        except RuntimeError as e:
            QApplication.restoreOverrideCursor()
            QMessageBox.warning(self, APP, f"Мышка не приняла настройку:\n{e}")
            return
        QApplication.restoreOverrideCursor()
        self.load()
        self.status.setText("Записано в мышку ✓")


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP)
    app.setDesktopFileName("mousedpi")
    app.setStyleSheet(STYLE)
    try:
        dev, name = find_device()
    except (RuntimeError, FileNotFoundError):
        dev = None
    if not dev:
        QMessageBox.critical(None, APP, "Мышка не найдена. Нужна служба ratbagd: "
                                        "sudo dnf install libratbag-ratbagd && sudo systemctl enable --now ratbagd")
        sys.exit(1)
    win = Window(dev, name)
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
