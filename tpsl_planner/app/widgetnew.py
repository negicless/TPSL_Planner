# -*- coding: utf-8 -*-
# widgets.py — TP-SL Planner (Pro, EN/JA, Dark/Light, Lock-R)

from typing import Optional
import os, sys, shutil, re

# ---- Qt imports (PyQt5) ----
from PyQt5 import QtCore
from PyQt5.QtCore import Qt, QSettings, QTimer, QLineF, QRectF, QPropertyAnimation, pyqtProperty
from PyQt5.QtGui import QFont, QColor, QPainter, QPen, QBrush
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QGridLayout, QDoubleSpinBox, QSpinBox, QComboBox, QSlider, QPushButton,
    QHBoxLayout, QVBoxLayout, QCheckBox, QGroupBox, QLineEdit, QMessageBox, QFileDialog, QMenu,
    QMainWindow, QFrame, QDialog, QDialogButtonBox, QSizePolicy, QPlainTextEdit, QToolButton)
from tpsl_planner.charts.theme import apply_theme as _theme

# ---------------- Basic i18n ----------------
_I18N = {
    "en": {
        "title": "TP-SL Planner",
        "btn_copy": "Copy",
        "btn_save": "Save",
        "btn_reset": "Reset",
        "btn_overlay": "Overlay",
        "btn_push": "Push",
        "inputs": "Inputs",
        "ticker": "Ticker",
        "side": "Side",
        "entry": "Entry",
        "current": "Current",
        "shares": "Shares",
        "tick": "Tick",
        "flat": "Flat fee",
        "ps": "Per-share fee",
        "open": "Open trade?",
        "sliders": "Stop / Target",
        "stop": "Stop %",
        "target": "Target %",
        "outputs": "Outputs",
        "price_box": "Prices",
        "risk_box": "Risk / Reward",
        "upl_box": "Unrealized P/L",
        "note": "Note",
    },
    "ja": {
        "title": "TP-SL プランナー",
        "btn_copy": "コピー",
        "btn_save": "保存",
        "btn_reset": "リセット",
        "btn_overlay": "オーバーレイ",
        "btn_push": "Notionへ",
        "inputs": "入力",
        "ticker": "銘柄コード",
        "side": "サイド",
        "entry": "エントリー",
        "current": "現在値",
        "shares": "株数",
        "tick": "値幅",
        "flat": "固定コスト",
        "ps": "株ごとのコスト",
        "open": "建玉中？",
        "sliders": "損切り / 目標",
        "stop": "損切り %",
        "target": "目標 %",
        "outputs": "結果",
        "price_box": "価格",
        "risk_box": "リスク / リワード",
        "upl_box": "含み損益",
        "note": "メモ",
    }
}

# ---------------- Output i18n ----------------
_UI_I18N = {
    "en": {
        "stop_ui": "Stop 🛑: {stop}  |  {spct}",
        "tgt_ui":  "Target 🎯: {tgt}  |  {tpct}",
        "rr_ui":   "Risk 💰: {risk}  |  Reward 🤑: {reward}  |  R {R}  |  RR {RR}",
        "upl_ui":  "UR P/L 🫰: {upl}  |  Breakeven 👔: {be}",
    },
    "ja": {
        "stop_ui": "損切り 🛑: {stop}  |  {spct}",
        "tgt_ui":  "目標 🎯: {tgt}  |  {tpct}",
        "rr_ui":   "リスク 💰: {risk}  |  リワード 🤑: {reward}  |  R {R}  |  RR {RR}",
        "upl_ui":  "含み損益 🫰: {upl}  |  損益分岐点 👔: {be}",
    }
}

# ---------------- Markdown i18n ----------------
_MD_I18N = {
    "en": {
        "hdr": "##   {title}",
        "ticker": "- **Ticker**: `{ticker}`  ({side})",
        "entry":  "- **Entry**: `{entry}`",
        "curr":   "- **Current**: `{curr}`",
        "stop":   "- **Stop**: `{stop}`  ({spct})",
        "tgt":    "- **Target**: `{tgt}`  ({tpct})",
        "risk":   "- **Risk**: `{risk}`  |  **Reward**: `{reward}`",
        "R":      "- **R multiple**: `{R}`  |  **RR**: `{RR}`",
        "upl":    "- **UR P/L**: `{upl}`  |  **Breakeven**: `{be}`",
        "notes":  "### Notes\n{notes}",
    },
    "ja": {
        "hdr": "##   {title}",
        "ticker": "- **銘柄**: `{ticker}`  ({side})",
        "entry":  "- **エントリー**: `{entry}`",
        "curr":   "- **現在値**: `{curr}`",
        "stop":   "- **損切り**: `{stop}`  ({spct})",
        "tgt":    "- **目標**: `{tgt}`  ({tpct})",
        "risk":   "- **リスク**: `{risk}`  |  **リワード**: `{reward}`",
        "R":      "- **R倍数**: `{R}`  |  **RR比**: `{RR}`",
        "upl":    "- **含み損益**: `{upl}`  |  **損益分岐点**: `{be}`",
        "notes":  "### メモ\n{notes}",
    }
}

# ---------------- Settings defaults ----------------
DEFAULTS = {
    "ticker": "",
    "entry": 1.38,
    "current": 1.36,
    "shares": 100,
    "tick": 0.01,
    "flat": 0.0,
    "ps": 0.0,
    "always_on_top": False,
    "open": False,
    "ui_lang": "en",
    "ui_theme": "dark",
    "note_folded": True,
}

# ---------------- Engine / deps ----------------
from tpsl_planner.core.engine import fmt2
from tpsl_planner.io.env_tools import load_env, ensure_env_template, env_file_path, has_valid_env
from tpsl_planner.io.company_lookup import normalize_ticker, get_company_name


class Switch(QCheckBox):
    """Custom on/off switch used in the UI."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._checked = False
        self._thumb_pos = 0.0
        self._anim = QPropertyAnimation(self, b"position", self)
        self._anim.setDuration(150)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumWidth(60)
        self.setMinimumHeight(28)
        # theme colors
        self._dark = True
        self._bg_on = QColor("#50fa7b")
        self._bg_off_dark = QColor("#2D365A")
        self._bg_off_light = QColor("#E0E6F3")
        self._knob = QColor("#f8f8f2")
        self._knob_border = QColor("#44475a")
        self.setTheme(True)  # default

    def setTheme(self, dark: bool):
        self._dark = dark
        self.update()

    def sizeHint(self):
        return QtCore.QSize(60, 28)

    def hitButton(self, pos):
        return self.contentsRect().contains(pos)

    def paintEvent(self, event):
        radius = 12
        knob_radius = 10

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = QRectF(0, 0, self.width(), self.height())
        rect = rect.adjusted(4, 4, -4, -4)

        # background
        if self.isChecked():
            painter.setBrush(self._bg_on)
        else:
            painter.setBrush(self._bg_off_dark if self._dark else self._bg_off_light)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(rect, radius, radius)

        # knob
        x = rect.x() + self._thumb_pos * (rect.width() - 2 * knob_radius)
        y = rect.y() + (rect.height() - 2 * knob_radius) / 2
        knob_rect = QRectF(x, y, 2 * knob_radius, 2 * knob_radius)

        painter.setBrush(self._knob)
        painter.setPen(QPen(self._knob_border, 1))
        painter.drawEllipse(knob_rect)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.setChecked(not self.isChecked())
        super().mouseReleaseEvent(event)

    def isChecked(self):
        return self._checked

    def setChecked(self, checked):
        if self._checked == checked:
            return
        self._checked = checked
        self._anim.stop()
        self._anim.setStartValue(self._thumb_pos)
        self._anim.setEndValue(1.0 if checked else 0.0)
        self._anim.start()
        super().setChecked(checked)
        self.stateChanged.emit(Qt.Checked if checked else Qt.Unchecked)

    @pyqtProperty(float)
    def position(self):
        return self._thumb_pos

    @position.setter
    def position(self, pos):
        self._thumb_pos = pos
        self.update()


class OverlayWindow(QWidget):
    """Small floating overlay showing entry/stop/target."""

    def __init__(self, i18n=None, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.Tool |
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.i18n = i18n or _UI_I18N["en"]

        self.lbl = QLabel("", self)
        self.lbl.setFont(QFont("Yu Gothic UI", 9))
        self.lbl.setStyleSheet("color: white;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.addWidget(self.lbl)

        self.setFixedSize(260, 90)

    def update_values(self, entry, stop, tgt, curr, long_side, open_):
        # Simple text for now
        side = "Long" if long_side else "Short"
        txt = (
            f"{side}\n"
            f"Entry: {fmt2(entry)}  |  Curr: {fmt2(curr)}\n"
            f"Stop:  {fmt2(stop)}  |  Tgt:  {fmt2(tgt)}"
        )
        self.lbl.setText(txt)


class TPSLWidget(QWidget):
    def __init__(self, parent: Optional[QWidget] = None, lang: str = "en"):
        super().__init__(parent)
        self.setWindowTitle("TP-SL Planner")
        self.settings = QSettings("tpsl_planner", "tpsl_app")
        self.state = DEFAULTS.copy()
        self._load_settings()
        self.state["ui_lang"] = lang or self.state.get("ui_lang", "en")
        self._block_spin = False
        self._last_report = ""
        self.overlay = None

        self.build_ui()
        self.apply_theme()
        self.apply_font()
        self._init_overlay()

    # ------------------------------------------------------------------
    # Settings
    # ------------------------------------------------------------------
    def _load_settings(self):
        for k, v in DEFAULTS.items():
            self.state[k] = self.settings.value(k, v)

    def save_settings(self):
        for k, v in self.state.items():
            self.settings.setValue(k, v)
        self.settings.sync()
        QMessageBox.information(self, "Saved", "Settings saved.")

    def reset_defaults(self):
        self.state.update(DEFAULTS)
        self.txt_ticker.setText(self.state["ticker"])
        self.spn_entry.setValue(self.state["entry"])
        self.spn_curr.setValue(self.state["current"])
        self.spn_shares.setValue(self.state["shares"])
        self.spn_tick.setValue(self.state["tick"])
        self.spn_flat.setValue(self.state["flat"])
        self.spn_ps.setValue(self.state["ps"])
        self.sw_open.setChecked(self.state["open"])
        self.cmb_side.setCurrentText(self.state["side"])
        self.recalc()

    # ------------------------------------------------------------------
    # Overlay init
    # ------------------------------------------------------------------
    def _init_overlay(self):
        self.overlay = OverlayWindow(i18n=_UI_I18N[self.state["ui_lang"]])
        self.overlay.hide()
        self._overlay_timer = QTimer(self)
        self._overlay_timer.setInterval(80)
        self._overlay_timer.timeout.connect(self.push_to_overlay)
        self._overlay_timer.start()

        self.apply_always_on_top(self.state["always_on_top"])
        if self.state.get("compact_mode", False): self._toggle_compact(True)
        self.retranslate_ui()
        self.recalc()

    # ---------- UI ----------
    # ------------------------------------------------------------------
    # Debounced ticker input handlers
    # ------------------------------------------------------------------
    # inside class TPSLWidget
    def _ticker_looks_complete(self, raw: str) -> bool:
        s = (raw or "").strip().upper()
        if not s:
            return False
        # allow prefixes like US- / JP-
        if s.startswith("US-"):
            s = s[3:]
        if s.startswith("JP-"):
            s = s[3:]
        # JPX: 4 digits or 3 digits + letter (optionally already with .T)
        if re.fullmatch(r"(?:\d{4}|\d{3}[A-Z])(?:\.T)?", s):
            return True
        # US-ish: letters/dots/hyphens 1–5 chars (AAPL, BRK.B, RANI, NU-AI)
        if re.fullmatch(r"[A-Z][A-Z0-9\.\-]{0,4}", s):
            # require at least 2 chars to avoid 'A' or 'N' accidental hits
            return len(s) >= 2
        # already normalized with suffix
        if re.fullmatch(r".+\.[A-Z]{1,3}", s):
            return True
        return False

    def _on_ticker_text_changed(self, _text: str):
        """Called on every keystroke in ticker field."""
        # restart debounce timer
        self._ticker_timer.stop()
        self._ticker_timer.start()

    def _on_ticker_finished(self):
        """Called only after user pauses typing for 2s."""
        ticker_raw = self.txt_ticker.text().strip()
        try:
            if self._ticker_looks_complete(ticker_raw):
                ticker_norm = normalize_ticker(ticker_raw)
                company_name = get_company_name(ticker_norm)
            else:
                ticker_norm = ticker_raw or "-"
                company_name = ""
            self.out_company.setText(f"{company_name} ({ticker_norm})" if company_name else ticker_norm)
            self.recalc()
        except Exception as e:
            print("[ticker debounce] recalc error:", e)

    def build_ui(self):
        t = _I18N[self.state["ui_lang"]]
        grid = QGridLayout(self); grid.setContentsMargins(14, 12, 14, 12)
        grid.setHorizontalSpacing(10); grid.setVerticalSpacing(8)

        # Header
        self.title_lbl = QLabel(t["title"]); self.title_lbl.setFont(QFont("Yu Gothic U", 12, QFont.Bold))
        self.btn_copy = QPushButton(t["btn_copy"])
        self.btn_save = QPushButton(t["btn_save"])
        self.btn_reset = QPushButton(t["btn_reset"])
        self.btn_overlay = QPushButton(t["btn_overlay"])
        self.btn_push = QPushButton(t["btn_push"])
        self.btn_settings = QPushButton("⚙"); self.btn_settings.setFixedWidth(36)
        for b in (self.btn_copy, self.btn_overlay, self.btn_save, self.btn_reset, self.btn_push): b.setFixedWidth(90)
        self.btn_copy.clicked.connect(self.copy_to_clipboard)
        self.btn_save.clicked.connect(self.save_settings)
        self.btn_reset.clicked.connect(self.reset_defaults)
        self.btn_overlay.clicked.connect(self.toggle_overlay)
        self.btn_push.clicked.connect(self.push_to_notion_clicked)
        self.btn_push.setContextMenuPolicy(Qt.CustomContextMenu)
        self.btn_push.customContextMenuRequested.connect(self._show_env_context_menu)
        self._update_push_button_state()
        self.btn_settings.clicked.connect(self.show_settings)

        header = QHBoxLayout(); header.setSpacing(6)
        header.addWidget(self.title_lbl); header.addStretch(1)
        for b in (self.btn_copy, self.btn_overlay, self.btn_save, self.btn_reset, self.btn_push, self.btn_settings):
            header.addWidget(b)

        # --- Inputs ---------------------------------------------------------------
        self.inputs_box = QGroupBox(t["inputs"])
        inputs = QGridLayout(self.inputs_box)
        r = 0

        # Ticker + Side
        self.lbl_ticker = QLabel(t.get("ticker", "Ticker"))
        self.txt_ticker = QLineEdit(self.state["ticker"])
        self.txt_ticker.setPlaceholderText("e.g., US-AAPL, JP-7013")
        inputs.addWidget(self.lbl_ticker, r, 0)
        inputs.addWidget(self.txt_ticker, r, 1)
        # --- Debounce ticker input ---
        self._ticker_timer = QTimer()
        self._ticker_timer.setSingleShot(True)
        self._ticker_timer.setInterval(2000)  # wait 700ms after typing stops
        self._ticker_timer.timeout.connect(self._on_ticker_finished)

        # Instead of direct connect:
        # self.txt_ticker.textChanged.connect(self.recalc)
        # use this:
        self.txt_ticker.textChanged.connect(self._on_ticker_text_changed)

        self.lbl_side = QLabel(t.get("side", "Side"))
        self.cmb_side = QComboBox()
        self.cmb_side.addItems(["Long", "Short"])
        self.cmb_side.setCurrentText(self.state["side"])
        inputs.addWidget(self.lbl_side, r, 2)
        inputs.addWidget(self.cmb_side, r, 3)
        r += 1

        # Entry / Current
        self.lbl_entry = QLabel(t.get("entry", "Entry"))
        self.spn_entry = self._spin(3, 0.0, 1_000_000.0, float(self.state["entry"]))
        inputs.addWidget(self.lbl_entry, r, 0)
        inputs.addWidget(self.spn_entry, r, 1)

        self.lbl_curr = QLabel(t.get("current", "Current"))
        self.spn_curr = self._spin(3, 0.0, 1_000_000.0, float(self.state["current"]))
        inputs.addWidget(self.lbl_curr, r, 2)
        inputs.addWidget(self.spn_curr, r, 3)
        r += 1

        # Shares / Tick
        self.lbl_shares = QLabel(t.get("shares", "Shares"))
        self.spn_shares = QSpinBox(); self.spn_shares.setRange(1, 10_000_000)
        self.spn_shares.setValue(int(self.state["shares"])); self.spn_shares.setSingleStep(100)
        inputs.addWidget(self.lbl_shares, r, 0)
        inputs.addWidget(self.spn_shares, r, 1)

        self.lbl_tick = QLabel(t.get("tick", "Tick"))
        self.spn_tick = self._spin(3, 0.0001, 10_000.0, float(self.state["tick"]))
        inputs.addWidget(self.lbl_tick, r, 2)
        inputs.addWidget(self.spn_tick, r, 3)
        r += 1

        # Fees
        self.lbl_flat = QLabel(t.get("flat", "Flat fee"))
        self.spn_flat = self._spin(2, 0.0, 1_000_000.0, float(self.state["flat"]))
        inputs.addWidget(self.lbl_flat, r, 0)
        inputs.addWidget(self.spn_flat, r, 1)

        self.lbl_ps = QLabel(t.get("ps", "Per-share fee"))
        self.spn_ps = self._spin(4, 0.0, 10_000.0, float(self.state["ps"]))
        inputs.addWidget(self.lbl_ps, r, 2)
        inputs.addWidget(self.spn_ps, r, 3)
        r += 1

        self.sw_open = Switch()
        self.sw_open.setChecked(bool(self.state["open"]))
        self.lbl_open = QLabel(t.get("open", "Open trade?"))
        inputs.addWidget(self.lbl_open, r, 0)
        inputs.addWidget(self.sw_open, r, 1)

        # Sliders
        self.sliders_box = QGroupBox(t["sliders"])
        sliders = QGridLayout(self.sliders_box)
        r = 0

        self.lbl_stop = QLabel(t["stop"])
        self.sld_stop = QSlider(Qt.Horizontal); self.sld_stop.setRange(-5000, 0)
        self.sld_stop.setValue(int(self.state["stop_pct"] * 100))
        sliders.addWidget(self.lbl_stop, r, 0)
        sliders.addWidget(self.sld_stop, r, 1)

        self.lbl_tgt = QLabel(t["target"])
        self.sld_tgt = QSlider(Qt.Horizontal); self.sld_tgt.setRange(0, 5000)
        self.sld_tgt.setValue(int(self.state["target_pct"] * 100))
        sliders.addWidget(self.lbl_tgt, r, 2)
        sliders.addWidget(self.sld_tgt, r, 3)
        r += 1

        self.spn_stop_pct = self._spin(2, -50.0, 0.0, float(self.state["stop_pct"]), "%", 80)
        self.spn_tgt_pct = self._spin(2, 0.0, 200.0, float(self.state["target_pct"]), "%", 80)
        sliders.addWidget(self.spn_stop_pct, r, 1)
        sliders.addWidget(self.spn_tgt_pct, r, 3)

        # Outputs
        self.outputs_box = QGroupBox(t["outputs"])
        outputs = QGridLayout(self.outputs_box)
        r = 0

        # Ticker / company
        self.out_company = QLabel("-"); outputs.addWidget(self.out_company, r, 0, 1, 4); r += 1

        # Prices
        self.price_box = QGroupBox(t["price_box"])
        price_layout = QGridLayout(self.price_box)
        self.lbl_stop_price = QLabel("Stop: -")
        self.lbl_tgt_price = QLabel("Target: -")
        price_layout.addWidget(self.lbl_stop_price, 0, 0)
        price_layout.addWidget(self.lbl_tgt_price, 0, 1)

        outputs.addWidget(self.price_box, r, 0, 1, 4); r += 1

        # Risk / Reward
        self.rr_box = QGroupBox(t["risk_box"])
        rr_layout = QGridLayout(self.rr_box)
        self.lbl_rr = QLabel("-")
        rr_layout.addWidget(self.lbl_rr, 0, 0)
        outputs.addWidget(self.rr_box, r, 0, 1, 4); r += 1

        # UPL
        self.upl_box = QGroupBox(t["upl_box"])
        upl_layout = QGridLayout(self.upl_box)
        self.lbl_upl = QLabel("-")
        upl_layout.addWidget(self.lbl_upl, 0, 0)
        outputs.addWidget(self.upl_box, r, 0, 1, 4); r += 1

        # Note area with toggle
        self.btn_note = QToolButton()
        self.btn_note.setText(t["note"])
        self.btn_note.setCheckable(True)
        self.btn_note.setChecked(not self.state.get("note_folded", True))
        self.btn_note.setArrowType(Qt.DownArrow if self.btn_note.isChecked() else Qt.RightArrow)
        self.btn_note.clicked.connect(lambda checked: self._on_note_toggled(checked))

        self.txt_note = QPlainTextEdit()
        self.txt_note.setPlaceholderText("Optional notes...")
        self.txt_note.setVisible(self.btn_note.isChecked())

        note_layout = QVBoxLayout()
        note_layout.addWidget(self.btn_note)
        note_layout.addWidget(self.txt_note)
        outputs.addLayout(note_layout, r, 0, 1, 4); r += 1

        # Layout assembly
        grid.addLayout(header, 0, 0)
        grid.addWidget(self.inputs_box, 1, 0)
        grid.addWidget(self._hline(), 2, 0)
        grid.addWidget(self.sliders_box, 3, 0)
        grid.addWidget(self._hline(), 4, 0)
        grid.addWidget(self.outputs_box, 5, 0)

        # --- recompute triggers -----------------------
        for w in [self.spn_tick, self.spn_entry, self.spn_curr, self.spn_shares, self.spn_flat, self.spn_ps]:
            w.valueChanged.connect(self.recalc)
        self.cmb_side.currentIndexChanged.connect(self.recalc)
        self.sld_stop.valueChanged.connect(lambda *_: (self._sync_price_from_pct(), self.recalc()))
        self.sld_tgt.valueChanged.connect(lambda *_: (self._sync_price_from_pct(), self.recalc()))
        self.spn_stop_pct.valueChanged.connect(lambda val: self.sld_stop.setValue(int(round(val * 100))))
        self.spn_tgt_pct.valueChanged.connect(lambda val: self.sld_tgt.setValue(int(round(val * 100))))
        self.sld_stop.valueChanged.connect(lambda v: self._set_spin_blocked(self.spn_stop_pct, self.spn_stop_pct.setValue, v/100.0))
        self.sld_tgt.valueChanged.connect(lambda v: self._set_spin_blocked(self.spn_tgt_pct, self.spn_tgt_pct.setValue, v/100.0))

    # ------------------------------------------------------------------
    # Core calculations
    # ------------------------------------------------------------------
    def _set_spin_blocked(self, spin, setter, value):
        self._block_spin = True
        try:
            setter(value)
        finally:
            self._block_spin = False

    def _is_long(self) -> bool:
        return self.cmb_side.currentText().lower().startswith("l")

    def stop_price_and_risk(self, entry: float, stop_pct: float, long_side: bool, tick: float):
        if long_side:
            stop_price = entry * (1.0 + stop_pct / 100.0)
            per_share_risk = entry - stop_price
        else:
            stop_price = entry * (1.0 - stop_pct / 100.0)
            per_share_risk = stop_price - entry
        # snap to tick
        stop_price = round(stop_price / tick) * tick
        return stop_price, per_share_risk

    def target_price(self, entry: float, tgt_pct: float, long_side: bool, tick: float):
        if long_side:
            tgt_price = entry * (1.0 + tgt_pct / 100.0)
        else:
            tgt_price = entry * (1.0 - tgt_pct / 100.0)
        tgt_price = round(tgt_price / tick) * tick
        return tgt_price

    def recalc(self):
        entry = self.spn_entry.value()
        curr = self.spn_curr.value()
        shares = self.spn_shares.value()
        tick = self.spn_tick.value()
        flat = self.spn_flat.value()
        ps = self.spn_ps.value()
        long_side = self._is_long()

        stop_pct = self.spn_stop_pct.value()
        tgt_pct = self.spn_tgt_pct.value()

        stop_price, per_risk = self.stop_price_and_risk(entry, stop_pct, long_side, tick)
        tgt_price = self.target_price(entry, tgt_pct, long_side, tick)

        reward_ps = (tgt_price - entry) if long_side else (entry - tgt_price)
        R = (reward_ps / per_risk) if per_risk else 0.0

        # risk/reward in cash (including fees)
        gross_risk = per_risk * shares
        gross_reward = reward_ps * shares

        total_fee = flat + ps * shares
        net_risk = gross_risk + total_fee
        net_reward = gross_reward - total_fee

        # Unrealized P/L
        curr_diff = (curr - entry) if long_side else (entry - curr)
        upl = curr_diff * shares - total_fee

        breakeven = entry + (total_fee / shares) if long_side else entry - (total_fee / shares)

        lang = self.state["ui_lang"]
        ui_str = _UI_I18N[lang]

        self.lbl_stop_price.setText(ui_str["stop_ui"].format(
            stop=fmt2(stop_price),
            spct=f"{stop_pct:.2f} %",
        ))
        self.lbl_tgt_price.setText(ui_str["tgt_ui"].format(
            tgt=fmt2(tgt_price),
            tpct=f"{tgt_pct:.2f} %",
        ))
        self.lbl_rr.setText(ui_str["rr_ui"].format(
            risk=fmt2(net_risk),
            reward=fmt2(net_reward),
            R=f"{R:.2f}",
            RR=f"{net_reward/abs(net_risk):.2f}" if net_risk else "∞",
        ))
        self.lbl_upl.setText(ui_str["upl_ui"].format(
            upl=fmt2(upl),
            be=fmt2(breakeven),
        ))

        self._build_markdown_report(entry, curr, stop_price, tgt_price,
                                    net_risk, net_reward, upl, breakeven, R)

    def _build_markdown_report(self, entry, curr, stop, tgt, net_risk, net_reward, upl, be, R):
        lang = self.state["ui_lang"]
        m = _MD_I18N[lang]

        ticker_raw = (self.txt_ticker.text().strip() or "-").upper()
        side = "Long" if self._is_long() else "Short"
        note_txt = self.txt_note.toPlainText().strip()

        report_lines = [
            m["hdr"].format(title="TP-SL Plan"),
            m["ticker"].format(ticker=ticker_raw, side=side),
            m["entry"].format(entry=fmt2(entry)),
            m["curr"].format(curr=fmt2(curr)),
            m["stop"].format(stop=fmt2(stop), spct=f"{self.spn_stop_pct.value():.2f}%"),
            m["tgt"].format(tgt=fmt2(tgt), tpct=f"{self.spn_tgt_pct.value():.2f}%"),
            m["risk"].format(risk=fmt2(net_risk), reward=fmt2(net_reward)),
            m["R"].format(R=f"{R:.2f}", RR=f"{net_reward/abs(net_risk):.2f}" if net_risk else "∞"),
            m["upl"].format(upl=fmt2(upl), be=fmt2(be)),
        ]
        if note_txt:
            report_lines.append("")
            report_lines.append(m["notes"].format(notes=note_txt))

        self._last_report = "\n".join(report_lines)

    def copy_to_clipboard(self):
        if not self._last_report:
            self.recalc()
        QApplication.clipboard().setText(self._last_report)
        old = self.btn_copy.text()
        self.btn_copy.setText("Copied ✅")
        QTimer.singleShot(1200, lambda: self.btn_copy.setText(old))

    def apply_theme(self):
        _theme(self)

    def apply_font(self):
        # You can customize fonts here if needed
        pass

    def apply_always_on_top(self, on: bool):
        flags = self.windowFlags()
        if on:
            flags |= Qt.WindowStaysOnTopHint
        else:
            flags &= ~Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.show()

    def toggle_overlay(self):
        if self.overlay.isVisible(): self.overlay.hide()
        else:
            geo = self.geometry(); self.overlay.move(geo.right() + 12, geo.top())
            self.push_to_overlay(); self.overlay.show()

    def push_to_overlay(self):
        if not getattr(self, "overlay", None) or not self.overlay.isVisible():
            return
        entry, tick = self.spn_entry.value(), self.spn_tick.value()
        long_side = self._is_long()
        stop_pct, tgt_pct = self.sld_stop.value()/10000.0, self.sld_tgt.value()/10000.0
        stop_price, _ = self.stop_price_and_risk(entry, stop_pct, long_side, tick)
        tgt_price = self.target_price(entry, tgt_pct, long_side, tick)
        curr = self.spn_curr.value(); open_ = self.sw_open.isChecked()
        self.overlay.update_values(entry, stop_price, tgt_price, curr, long_side, open_)

    # ---------- .env helpers ----------
    def _update_push_button_state(self):
        """Enable/disable the Push button based on .env / Notion config."""
        ok = has_valid_env()
        self.btn_push.setEnabled(ok)
        if ok:
            self.btn_push.setToolTip("")
        else:
            self.btn_push.setToolTip(
                "Notion push disabled: set NOTION_TOKEN and NOTION_TRADE_DB in your .env\n"
                "(Right-click the Push button for .env options.)",
            )

    # ---------- .env menu ----------
    def _show_env_context_menu(self, pos):
        menu = QMenu(self)
        add_action    = menu.addAction("Add .env")
        edit_action   = menu.addAction("Edit .env")
        reload_action = menu.addAction("Reload .env")
        action = menu.exec(self.btn_push.mapToGlobal(pos))
        if action == add_action:   self._add_env_file()
        elif action == edit_action:self._edit_env_file()
        elif action == reload_action: self._reload_env()

    def _add_env_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select .env file", "", "ENV files (*.env);;All Files (*.*)")
        if not path: return
        target = env_file_path()
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
        load_env()
        self._update_push_button_state()
        QMessageBox.information(self, "Installed", f".env added:\n{target}")

    def _edit_env_file(self):
        p = env_file_path()
        if not p.exists(): ensure_env_template()
        try:
            if os.name == "nt": os.startfile(str(p))  # type: ignore[attr-defined]
            elif sys.platform == "darwin": os.system(f'open "{p}"')
            else: os.system(f'xdg-open "{p}"')
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not open editor:\n{e}")

    def _reload_env(self):
        load_env()
        self._update_push_button_state()
        QMessageBox.information(self, "Reloaded", "Environment variables reloaded.")

    def _on_note_toggled(self, expanded: bool):
        # Update arrow and visibility
        self.btn_note.setArrowType(Qt.DownArrow if expanded else Qt.RightArrow)
        self.txt_note.setVisible(expanded)
        # Persist folded state in memory (saved on save_settings)
        self.state["note_folded"] = not expanded

    def _collect_trade_dict(self):
        entry = self.spn_entry.value()
        curr  = self.spn_curr.value()
        shares = self.spn_shares.value()
        tick = self.spn_tick.value()
        long_side = self._is_long()
        note_txt = self.txt_note.toPlainText().strip()
        stop_pct = self.spn_stop_pct.value()
        tgt_pct  = self.sld_tgt.value()/10000.0
        status = "Open" if self.sw_open.isChecked() else "Idea"

        stop_price, per_risk = self.stop_price_and_risk(entry, stop_pct, long_side, tick)
        tgt_price = self.target_price(entry, tgt_pct, long_side, tick)
        reward_ps = (tgt_price - entry) if long_side else (entry - tgt_price)
        R = (reward_ps / per_risk) if per_risk else 0.0

        return {
            "ticker": (self.txt_ticker.text().strip() or "-").upper(),
            "side": "Long" if long_side else "Short",
            "entry": entry, "stop": stop_price, "target": tgt_price, "shares": shares,
            "r": R, "notes": note_txt , "status": status,
        }

    def push_to_notion_clicked(self):
        # Check env first
        if not has_valid_env():
            QMessageBox.warning(
                self,
                "Notion not configured",
                "Notion push is disabled because NOTION_TOKEN or NOTION_TRADE_DB "
                "is not set in your .env.\n\n"
                "Right-click the Push button to add or edit a .env file.",
            )
            self._update_push_button_state()
            return

        # Lazy-import Notion client so missing env doesn't crash app at import time
        try:
            from tpsl_planner.io.notion_client import send_trade_to_notion
        except Exception as e:
            QMessageBox.warning(
                self,
                "Notion module error",
                f"Could not load Notion integration:\n{e}",
            )
            return

        trade = self._collect_trade_dict()
        report_text = self._last_report
        try:
            send_trade_to_notion(trade, report_text=report_text)
            old = self.btn_push.text()
            self.btn_push.setText("Pushed ✅")
            QTimer.singleShot(1200, lambda: self.btn_push.setText(old))
        except Exception as e:
            old = self.btn_push.text()
            self.btn_push.setText("Failed ❌")
            QTimer.singleShot(1500, lambda: self.btn_push.setText(old))
            print("Notion push error:", e)

    # ---------- Helpers ----------
    def _spin(self, decimals, rmin, rmax, val, suffix="", width=120):
        s = QDoubleSpinBox(); s.setDecimals(decimals); s.setRange(rmin, rmax); s.setValue(val)
        if suffix: s.setSuffix(" "+suffix); s.setFixedWidth(width)
        return s

    def _hline(self):
        f = QFrame(); f.setFrameShape(QFrame.HLine); f.setFrameShadow(QFrame.Sunken)
        is_dark = (self.state.get("ui_theme", "dark") == "dark")
        f.setStyleSheet("color: #3a3f5a;" if is_dark else "color: #C9CEDA;")
        return f


class MainWindow(QMainWindow):
    def __init__(self, lang: str = "en"):
        super().__init__()
        self.widget = TPSLWidget(lang=lang)
        self.setCentralWidget(self.widget)
        self.setWindowTitle("TP-SL Planner")
        self.resize(720, 540)


def main():
    load_env()  # initial load
    app = QApplication(sys.argv)
    lang = "en"
    w = MainWindow(lang=lang)
    w.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
