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
    QMainWindow, QFrame, QDialog, QDialogButtonBox, QSizePolicy, QPlainTextEdit, QToolButton, QInputDialog,
    QFontComboBox, QShortcut
)
from tpsl_planner.charts.theme import apply_theme as _theme

# ---- Price fetch module ----
from tpsl_planner.core.price import get_last_price, PriceError
from tpsl_planner.io.company_lookup import normalize_ticker, get_company_name,display_label,infer_market
# ---- Env / Notion ----
from tpsl_planner.io.env_tools import (
    load_env,
    ensure_env_template,
    env_file_path,
    has_valid_env,
)

# ---------------- Engine / deps ----------------
from tpsl_planner.core.engine import fmt2
from tpsl_planner.io.env_tools import load_env, ensure_env_template, env_file_path
from tpsl_planner.io.company_lookup import normalize_ticker, get_company_name
APP_ORG = "Cless"
APP_NAME = "TPSL-Plannerr"

# Canonical English section keys (used for backend / Notion mapping)
SECTIONS_EN = [
    "Tech",
    "Financials",
    "Energy",
    "Industrials",
    "Materials",
    "Consumer",
    "Healthcare",
    "Utilities",
    "Real Estate",
    "Transportation",
    "Defense",
    "Other",
]

# ---------------- UI i18n (EN/JA) ----------------
_I18N = {
    "en": {
        "title": "TP-SL",
        "inputs": "Inputs",
        "targets": "Targets & Stop",
        "outputs": "Outputs",
        "ticker": "Ticker",
        "side": "Side",
        "tick": "Tick",
        "entry": "Entry",
        "current": "Current",
        "shares": "Shares",
        "fees": "Fees",
        "dynamic": "volatility/levels-aware",
        "open": "Open",
        "idea": "Idea",
        "stop_pct": "Stop%",
        "tgt_pct": "Target%",
        "stop_price": "Stop💲",
        "tgt_price": "Target💲",
        "btn_copy": "Copy",
        "btn_overlay": "Overlay",
        "btn_save": "Save",
        "btn_reset": "Reset",
        "btn_push": "Push",
        "settings": "Settings",
        "lock_r": "Lock R =",
        "lang": "Language",
        "theme": "Theme",
        "dark": "Dark",
        "light": "Light",
        "always_on_top": "Always on top",
        "compact_mode": "Compact mode",
        "enable_lock_r": "Enable Lock-R",
        "lock_r_value": "R multiple",
        "ok": "OK",
        "cancel": "Cancel",
        "overlay_title": "Profit Overlay",
        "side_long_lbl": "Long",
        "side_short_lbl": "Short",
        "contact_support": "❓Contact Support",
        "contact_tooltip": "Send feedback or report an issue",
        "apply": "Apply",
        "tooltip_current": "Click to fetch the latest price from Yahoo Finance",
        "note": "Note",
        "note_ph": "Notes (plan, catalyst, risk, rules…)",
        "note_line": "📝 Note: {note}",
        "setup_rating": "Setup rating",
        "levels": "Levels",
        "rating_none": "None",
        "section": "Section",
        "shortcut_save": "Ctrl+S",
        "shortcut_push": "Ctrl+P",
        "shortcut_levels": "Alt+L",
        "sections": [
            "Tech",
            "Financials",
            "Energy",
            "Industrials",
            "Materials",
            "Consumer",
            "Healthcare",
            "Utilities",
            "Real Estate",
            "Transportation",
            "Defense",
            "Other",
        ],
    },
    "ja": {
        "title": "TP-SL",
        "inputs": "入力",
        "targets": "ターゲット & 損切り",
        "outputs": "結果",
        "ticker": "銘柄",
        "side": "方向",
        "tick": "ティック",
        "entry": "エントリー",
        "current": "現在値",
        "shares": "株数",
        "fees": "手数料",
        "dynamic": "ボラ・レベル対応",
        "open": "エントリー済み",
        "idea": "アイデア",
        "stop_pct": "損切り%",
        "tgt_pct": "利食い%",
        "stop_price": "損切り💲",
        "tgt_price": "利食い💲",
        "btn_copy": "コピー",
        "btn_overlay": "オーバーレイ",
        "btn_save": "保存",
        "btn_reset": "リセット",
        "btn_push": "プッシュ",
        "settings": "設定",
        "lock_r": "R固定 =",
        "lang": "言語",
        "theme": "テーマ",
        "dark": "ダーク",
        "light": "ライト",
        "always_on_top": "常に手前に表示",
        "compact_mode": "コンパクト表示",
        "enable_lock_r": "R固定を有効",
        "lock_r_value": "R 値",
        "ok": "OK",
        "cancel": "キャンセル",
        "overlay_title": "損益オーバーレイ",
        "side_long_lbl": "買い",
        "side_short_lbl": "売り",
        "contact_support": "❓お問い合わせ",
        "contact_tooltip": "フィードバックや不具合報告を送信",
        "apply": "適用",
        "tooltip_current": "Yahooファイナンスから最新価格を取得します",
        "note": "メモ",
        "note_ph": "メモ（計画・材料・リスク・ルールなど）",
        "note_line": "📝 メモ: {note}",
        "setup_rating": "セットアップ評価",
        "levels": "レベル",
        "rating_none": "なし",
        "section": "セクション",
        "shortcut_save": "Ctrl+S",
        "shortcut_push": "Ctrl+P",
        "shortcut_levels": "Alt+L",
        "sections": [
            "テクノロジー",
            "金融",
            "エネルギー",
            "工業",
            "素材",
            "消費財",
            "ヘルスケア",
            "公益事業",
            "不動産",
            "輸送",
            "防衛",
            "その他",
        ]
    }
}

# ---------------- Outputs UI i18n ----------------
_OUT_I18N = {
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
        "summary": "🧭 --Trade Setup Summary--",
        "ticker_side": "🎯 Ticker: {ticker} | Side: {side}",
        "entry_line": "💰 Entry: {entry} | 📈 Current: {curr} | 🤏Shares: {shares}",
        "stop_line": "🛑 Stop: {stop} ({spct}) | 🎯 Target: {tgt} ({tpct})",
        "rr_line": "⚖️ Risk: {risk} | 🏆 Reward: {reward}",
        "r_line": "📐 R-Multiple: {R} | RR Ratio: {RR}",
        "unreal_line": "📊 Unrealized P/L: {upl} | 💎 Breakeven: {be}",
        "section_line": "📂 Section: {section}",
        "rating_line": "⭐ Setup rating: {rating}",
        "fee_line": "💸 Fees: Flat {flat} + Per-share {ps}",
        "status_open": "✅ Open",
        "status_idea": "✅ Idea",
        "side_long": "🟩 **Long**",
        "side_short": "🟥 **Short**",
    },
    "ja": {
        "hdr": "##   {title}",
        "summary": "🧭 --トレードプランー--",
        "ticker_side": "🎯 銘柄: {ticker} | サイド: {side}",
        "entry_line": "💰 エントリー: {entry} | 📈 現在値: {curr} | 🤏株数: {shares}",
        "stop_line": "🛑 損切り: {stop} ({spct}) | 🎯 目標: {tgt} ({tpct})",
        "rr_line": "⚖️ リスク: {risk} | 🏆 リワード: {reward}",
        "r_line": "📐 R倍数: {R} | RR比: {RR}",
        "unreal_line": "📊 含み損益: {upl} | 💎 損益分岐点: {be}",
        "section_line": "📂 セクション: {section}",
        "rating_line": "⭐ セットアップ評価: {rating}",
        "fee_line": "💸 手数料: 定額 {flat} + 株単価 {ps}",
        "status_open": "✅ エントリー済み",
        "status_idea": "💡 アイディア",
        "side_long": "🟩 買い",
        "side_short": "🟥 売り",
    }
}




DEFAULTS = {
    "ticker": "",
    "entry": 1.38,
    "current": 1.36,
    "shares": 100,
    "tick": 0.01,
    "side": "Long",
    "stop_pct": -3.0,
    "target_pct": 10.0,
    "flat_fee": 0.0,
    "per_share_fee": 0.0,
    "always_on_top": False,
    "open": False,
    "ui_lang": "en",
    "ui_theme": "dark",
    "font_family": "Yu Gothic UI",
    "font_size": 10,
    "lockR_enabled": False,
    "lockR_value": 2.0,
    "compact_mode": False,
    "note": "",
    "note_folded": True,  
    "setup_rating": 0,
    "section": "",
    "hand_size": 100,

}

# ===== Switch =====
class Switch(QCheckBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._position = 1.0 if self.isChecked() else 0.0
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
        self._dark = bool(dark); self.update()

    def nextCheckState(self):
        new_state = not self.isChecked()
        super().setChecked(new_state)
        self._anim.stop()
        self._anim.setStartValue(self._position)
        self._anim.setEndValue(1.0 if new_state else 0.0)
        self._anim.start()
        self.update()

    def setChecked(self, checked: bool):
        super().setChecked(checked)
        self._position = 1.0 if checked else 0.0
        self.update()

    def paintEvent(self, event):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        rect = self.rect().adjusted(3, 3, -3, -3)
        bg = self._bg_on if self.isChecked() else (self._bg_off_dark if self._dark else self._bg_off_light)
        p.setPen(Qt.NoPen); p.setBrush(QBrush(bg))
        p.drawRoundedRect(rect, rect.height()/2, rect.height()/2)
        d = rect.height() - 4
        x = rect.left() + self._position * (rect.width() - d)
        p.setBrush(QBrush(self._knob)); p.setPen(QPen(self._knob_border))
        p.drawEllipse(QRectF(x, rect.top()+2, d, d))
        p.end()

    def get_position(self): return self._position
    def set_position(self, pos): self._position = pos; self.update()
    position = pyqtProperty(float, fget=get_position, fset=set_position)

# ===== ProfitBar =====
class ProfitBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(64, 240)
        self.entry = self.stop = self.target = self.current = 0.0
        self.is_long = True
        self.open_ = True
        self.dark = True   # track current theme
        self._font_lbl = QFont("Segoe UI", 9); self._font_lbl.setBold(True)
        self.setTheme(True)

    def setTheme(self, dark=True):
        """Switch bar colors for dark/light themes."""
        self.dark = bool(dark)
        if self.dark:
            self.bg_col = QColor(40, 40, 40)
            self._pen_entry = QPen(QColor("#F1FA8C"), 2)
            self._pen_current = QPen(QColor(140, 200, 255), 2)
            self.col_stop = "#FF5555"
            self.col_tp = "#50FA7B"
        else:
            self.bg_col = QColor(230, 230, 230)
            self._pen_entry = QPen(QColor("#222"), 2)
            self._pen_current = QPen(QColor("#1A73E8"), 2)
            self.col_stop = "#F28B82"  # light red
            self.col_tp = "#81C995"    # light green
        self.update()

    def setValues(self, entry, stop, target, current, is_long, open_=True):
        self.entry, self.stop, self.target, self.current = map(float, (entry, stop, target, current))
        self.is_long = bool(is_long)
        self.open_ = bool(open_)
        self.update()

    def paintEvent(self, e):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        rect = self.rect().adjusted(10, 10, -10, -10)
        p.setPen(Qt.NoPen); p.setBrush(self.bg_col)
        p.drawRoundedRect(rect, 10, 10)
        if self.entry == 0:
            p.end(); return

        lo, hi = min(self.stop, self.target), max(self.stop, self.target)
        rng = hi - lo if hi != lo else 1.0
        bar = rect.adjusted(18, 12, -36, -12)

        def y_for(price): return bar.top() + (1 - (price - lo) / rng) * bar.height()
        def zc(hex_): c = QColor(hex_); c.setAlpha(255 if self.open_ else 110); return c
        def band(y1, y2, col):
            top, h = min(y1, y2), abs(y2 - y1)
            if h > 0: p.fillRect(QRectF(bar.left(), top, bar.width(), h), col)

        y_stop, y_entry, y_target = map(y_for, (self.stop, self.entry, self.target))
        band(y_stop, y_entry, zc(self.col_stop))
        band(y_entry, y_target, zc(self.col_tp))

        p.setPen(self._pen_entry); p.drawLine(QLineF(bar.left(), y_entry, bar.right(), y_entry))
        cur_val = max(min(self.current, hi), lo)
        y_cur = y_for(cur_val)
        mid = None
        if self.is_long:
            if cur_val >= self.entry: mid = zc("#9AED97")
            elif cur_val > self.stop: mid = zc("#F1FA8C")
        else:
            if cur_val <= self.entry: mid = zc("#9AED97")
            elif cur_val < self.stop:  mid = zc("#F1FA8C")
        if mid is not None and abs(y_entry - y_cur) > 0.5:
            band(y_entry, y_cur, mid)
        p.setPen(self._pen_current); p.drawLine(QLineF(bar.left()-4, y_cur, bar.right()+4, y_cur))

        p.setFont(self._font_lbl)
        p.setPen(QColor("#640E0E")); p.drawText(bar.left()+4, int(y_stop)-2, f"SL {self.stop:.2f}")
        p.setPen(QColor("#110F49")); p.drawText(bar.left()+4, int(y_entry)-2, f"EN {self.entry:.2f}")
        p.setPen(QColor("#2FE659")); p.drawText(bar.left()+4, int(y_target)-2, f"TP {self.target:.2f}")

        per_risk = abs(self.entry - self.stop)
        if per_risk > 0:
            p.setPen(QPen(QColor("#777"), 1)); p.setFont(QFont("Segoe UI", 8))
            sign = 1 if self.is_long else -1
            for n in (0, 1, 2, 3):
                y_n = y_for(self.entry + sign * n * per_risk)
                if bar.top()-2 <= y_n <= bar.bottom()+2:
                    p.drawLine(QLineF(bar.right()+4, y_n, bar.right()+10, y_n))
                    p.drawText(bar.right()+12, int(y_n+3), f"{n}R")
        p.end()

# ===== Settings dialog =====
class SettingsDialog(QDialog):
    def __init__(self, parent, i18n):
        super().__init__(parent)
        self.i18n = i18n
        self.setWindowTitle(i18n["settings"])
        lay = QVBoxLayout(self)

        # UI options
        grp_ui = QGroupBox(i18n["settings"])
        g = QGridLayout(grp_ui)
        self.chk_ontop   = QCheckBox(i18n["always_on_top"])
        self.chk_compact = QCheckBox(i18n["compact_mode"])
        g.addWidget(self.chk_ontop,   0, 0, 1, 2)
        g.addWidget(self.chk_compact, 1, 0, 1, 2)

        # Lock-R
        grp_lock = QGroupBox(i18n["lock_r"])
        h = QHBoxLayout(grp_lock)
        self.chk_lockr = QCheckBox(i18n["enable_lock_r"])
        self.spn_lockr = QDoubleSpinBox(); self.spn_lockr.setRange(0.1, 10.0); self.spn_lockr.setSingleStep(0.1)
        h.addWidget(self.chk_lockr); h.addWidget(QLabel(i18n["lock_r_value"])); h.addWidget(self.spn_lockr); h.addStretch(1)

        # Language / Theme
        grp_misc = QGroupBox(i18n["settings"])
        m = QGridLayout(grp_misc)
        self.cmb_lang  = QComboBox(); self.cmb_lang.addItems(["English", "日本語"])
        self.cmb_theme = QComboBox(); self.cmb_theme.addItems([i18n["dark"], i18n["light"]])
        m.addWidget(QLabel(i18n["lang"]),  0, 0); m.addWidget(self.cmb_lang,  0, 1)
        m.addWidget(QLabel(i18n["theme"]), 1, 0); m.addWidget(self.cmb_theme, 1, 1)
        # Font family + size
        self.cmb_font = QFontComboBox()
        self.spn_font_size = QSpinBox(); self.spn_font_size.setRange(6, 36); self.spn_font_size.setSingleStep(1)
        m.addWidget(QLabel("Font"), 2, 0); m.addWidget(self.cmb_font, 2, 1)
        m.addWidget(QLabel("Size"), 3, 0); m.addWidget(self.spn_font_size, 3, 1)

        lay.addWidget(grp_ui); lay.addWidget(grp_lock); lay.addWidget(grp_misc)

        # Contact Support
        from PyQt5.QtGui import QDesktopServices
        from PyQt5.QtCore import QUrl
        self.btn_contact = QPushButton(i18n["contact_support"])
        self.btn_contact.setToolTip(i18n["contact_tooltip"])
        self.btn_contact.clicked.connect(
            lambda: QDesktopServices.openUrl(
                QUrl("mailto:negicless@gmail.com?subject=TPSL%20Planner%20Feedback")
            )
        )
        lay.addWidget(self.btn_contact)

        # OK / Cancel
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.Apply)
        btns.button(QDialogButtonBox.Ok).setText(i18n["ok"])
        btns.button(QDialogButtonBox.Cancel).setText(i18n["cancel"])
        # Apply button (not localized in i18n dictionary)
        try:
            # keep a reference so we can retranslate later
            self.btn_apply = btns.button(QDialogButtonBox.Apply)
            self.btn_apply.setText(i18n.get("apply", "Apply"))
        except Exception:
            self.btn_apply = None
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        # Connect Apply to handler
        try:
            if self.btn_apply:
                self.btn_apply.clicked.connect(self._on_apply)
        except Exception:
            pass
        lay.addWidget(btns)

        self.retranslate(self.i18n)
        self.cmb_lang.currentIndexChanged.connect(self._on_lang_changed)

    def _on_lang_changed(self, *_):
        code = "en" if "English" in self.cmb_lang.currentText() else "ja"
        self.retranslate(_I18N[code])

    def load_from_state(self, s):
        self.chk_ontop.setChecked(bool(s.get("always_on_top", False)))
        self.chk_compact.setChecked(bool(s.get("compact_mode", False)))
        self.chk_lockr.setChecked(bool(s.get("lockR_enabled", False)))
        self.spn_lockr.setValue(float(s.get("lockR_value", 2.0)))
        self.cmb_lang.setCurrentIndex(0 if s.get("ui_lang", "en") == "en" else 1)
        self.cmb_theme.setCurrentIndex(0 if s.get("ui_theme", "dark") == "dark" else 1)
        # font
        try:
            self.cmb_font.setCurrentFont(QFont(s.get("font_family", "Yu Gothic UI")))
        except Exception:
            pass
        try:
            self.spn_font_size.setValue(int(s.get("font_size", 10)))
        except Exception:
            self.spn_font_size.setValue(10)

    def dump_to_state(self, s):
        s["always_on_top"] = self.chk_ontop.isChecked()
        s["compact_mode"]  = self.chk_compact.isChecked()
        s["lockR_enabled"] = self.chk_lockr.isChecked()
        s["lockR_value"]   = self.spn_lockr.value()
        s["ui_lang"]       = "en" if self.cmb_lang.currentIndex() == 0 else "ja"
        s["ui_theme"]      = "dark" if self.cmb_theme.currentIndex() == 0 else "light"
        # font
        try:
            s["font_family"] = self.cmb_font.currentFont().family()
        except Exception:
            s["font_family"] = s.get("font_family", "Yu Gothic UI")
        try:
            s["font_size"] = int(self.spn_font_size.value())
        except Exception:
            s["font_size"] = int(s.get("font_size", 10))
        return s

    def _on_apply(self):
        """Apply current dialog settings immediately without closing."""
        try:
            parent = self.parent()
            if parent is None:
                return
            # dump dialog values into parent's state
            self.dump_to_state(parent.state)
            
            # Apply theme immediately
            try:
                _theme(QApplication.instance(), parent.state.get("ui_theme", "dark"))
            except Exception:
                pass
            
            # Apply font immediately
            try:
                fam = parent.state.get("font_family", "Yu Gothic UI")
                sz = int(parent.state.get("font_size", 10))
                QApplication.instance().setFont(QFont(fam, sz))
            except Exception:
                pass
            
            # Apply always-on-top
            try:
                parent.apply_always_on_top(parent.state.get("always_on_top", False))
            except Exception:
                pass
            
            # Apply compact mode
            try:
                parent._toggle_compact(parent.state.get("compact_mode", False))
            except Exception:
                pass
            
            # Persist all settings to QSettings
            try:
                parent.save_settings()
            except Exception:
                pass
            
            # Update UI after all changes
            try:
                parent.retranslate_ui()
            except Exception:
                pass
            try:
                parent.overlay.retranslate(_I18N[parent.state.get("ui_lang","en")])
            except Exception:
                pass
        except Exception:
            pass

    def retranslate(self, i18n: dict):
        self.i18n = i18n
        self.setWindowTitle(i18n["settings"])
        self.btn_contact.setText(i18n["contact_support"])
        self.btn_contact.setToolTip(i18n["contact_tooltip"])
        # apply button text
        try:
            if getattr(self, "btn_apply", None) is not None:
                self.btn_apply.setText(i18n.get("apply", "Apply"))
        except Exception:
            pass

# ===== Overlay =====
class OverlayWindow(QWidget):
    def __init__(self, parent=None, i18n=None):
        super().__init__(parent)
        self._i18n = i18n or _I18N["en"]
        self.setWindowTitle(self._i18n["overlay_title"])
        self.setWindowFlags(self.windowFlags() | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.bar = ProfitBar()
        # Track whether the user manually moved the overlay; if True,
        # avoid programmatically re-positioning it so the overlay isn't "locked".
        self.user_moved = False
        # Internal flag to ignore move events triggered by programmatic moves
        self._ignore_move_event = False
        lay = QVBoxLayout(self); lay.setContentsMargins(6, 6, 6, 6); lay.addWidget(self.bar)
        self.resize(120, 320)

    def update_values(self, entry, stop, target, current, is_long, open_):
        self.bar.setValues(entry, stop, target, current, is_long, open_)

    def retranslate(self, i18n):
        self._i18n = i18n
        self.setWindowTitle(self._i18n["overlay_title"])

    def moveEvent(self, event):
        """Detect user moves: if the move wasn't initiated programmatically,
        mark the overlay as user_moved so we stop auto-repositioning it."""
        try:
            super().moveEvent(event)
        except Exception:
            pass
        if getattr(self, "_ignore_move_event", False):
            return
        self.user_moved = True

# ===== Main widget =====
class TPSLWidget(QWidget):
    def __init__(self, parent=None):
        from PyQt5.QtCore import QTimer
        super().__init__(parent)
        self.settings = QSettings(APP_ORG, APP_NAME)
        self.state = DEFAULTS.copy()
        self.load_settings()
        # section flags: track whether the user manually edited the section
        # during this session and whether the current text was auto-filled.
        # Start as not user-modified so changes to the ticker will update
        # the section unless the user edits it now.
        self._section_user_modified = False
        self._section_auto_filled = False

        try: _theme(QApplication.instance(), self.state.get("ui_theme","dark"))
        except Exception: pass

    
        self._last_report = ""

        self.build_ui()

        # Overlay before first recalc
        self.overlay = OverlayWindow(i18n=_I18N[self.state["ui_lang"]])
        self.overlay.hide()
        self._overlay_timer = QTimer(self)
        self._overlay_timer.setInterval(80)
        self._overlay_timer.timeout.connect(self.push_to_overlay)
        self._overlay_timer.start()

        self.apply_always_on_top(self.state["always_on_top"])
        if self.state.get("compact_mode", False): self._toggle_compact(True)
        self.retranslate_ui()
        self.recalc()
        
        # Setup keyboard shortcuts (will be initialized after build_ui())
        self._setup_shortcuts()
    
    def _rating_to_stars(self, rating_text: str) -> str:
        """Convert setup rating text (A+, A, B, C, D) to star emoji count."""
        rating_text = (rating_text or "").strip()
        if rating_text == "A+":
            return "⭐⭐⭐⭐⭐"  # 5 stars
        elif rating_text == "A":
            return "⭐⭐⭐⭐"  # 4 stars
        elif rating_text == "B":
            return "⭐⭐⭐"  # 3 stars
        elif rating_text == "C":
            return "⭐⭐"  # 2 stars
        elif rating_text == "D":
            return "⭐"  # 1 star
        else:
            return ""  # no rating

    def _setup_shortcuts(self):
        """Setup keyboard shortcuts: Ctrl+S (Save), Ctrl+P (Push), Alt+L (Levels)."""
        try:
            QShortcut(Qt.CTRL + Qt.Key_S, self, self.save_settings)
            QShortcut(Qt.CTRL + Qt.Key_P, self, self.push_to_notion_clicked)
            QShortcut(Qt.ALT + Qt.Key_L, self, self._on_levels_shortcut)
        except Exception as e:
            print(f"[shortcuts] setup error: {e}")

    def _on_levels_shortcut(self):
        """Handle Alt+L shortcut to show/toggle Levels dialog."""
        try:
            self._open_pull_levels()
        except Exception as e:
            print(f"[shortcuts] levels error: {e}")

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

        # JPX cash equities:
        # - 4 digits: 7203
        # - 3 digits + 1 letter: 147A
        # optional ".T" suffix is allowed
        if re.fullmatch(r"(?:\d{4}|\d{3}[A-Z])(?:\.T)?", s):
            return True

        # US-ish: letters/dots/hyphens 1–5 chars (AAPL, BRK.B, RANI, NU-AI)
        if re.fullmatch(r"[A-Z][A-Z0-9\.\-]{0,4}", s):
            # require at least 2 chars to avoid 'A' or 'N' accidental hits
            return len(s) >= 2

        # already normalized with suffix (e.g. AAPL.US, 7203.T)
        if re.fullmatch(r".+\.[A-Z]{1,3}", s):
            return True

        return False


    def _on_ticker_text_changed(self, _text: str):
        """Called on every keystroke in ticker field."""
        # restart the debounce timer (defined in build_ui)
        if hasattr(self, "_ticker_timer"):
            # mark that a ticker change happened — allow auto-fill to overwrite
            # previous auto-filled value when ticker changes, unless the user
            # has manually edited the section in this session.
            try:
                if not getattr(self, "_section_user_modified", False):
                    self._section_auto_filled = True
            except Exception:
                pass
            self._ticker_timer.start()

    def _on_ticker_finished(self):
        """Called when user stops typing for 700 ms."""
        try:
            # safely trigger recalculation (fetches only once)
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
        self.btn_copy.clicked.connect(self.copy_to_clipboard)
        self.btn_save = QPushButton(t["btn_save"])
        self.btn_save.clicked.connect(self.save_settings)
        self.btn_save.setToolTip(f"{t['btn_save']} ({t['shortcut_save']})")
        self.btn_reset = QPushButton(t["btn_reset"])
        self.btn_reset.clicked.connect(self.reset_defaults)
        self.btn_overlay = QPushButton(t["btn_overlay"])
        self.btn_overlay.clicked.connect(self.toggle_overlay)
        
        # Notion push button
        self.btn_push = QPushButton(t["btn_push"])
        self.btn_push.clicked.connect(self.push_to_notion_clicked)
        self.btn_push.setToolTip(f"{t['btn_push']} ({t['shortcut_push']})")
        self.btn_push.setEnabled(has_valid_env())
             # env-aware state
        self._update_push_button_state()
        # right-click context menu for .env management
        self.btn_push.setContextMenuPolicy(Qt.CustomContextMenu)
        self.btn_push.customContextMenuRequested.connect(self._show_env_context_menu)
        
        # Settings button
        self.btn_settings = QPushButton("⚙"); self.btn_settings.setFixedWidth(36)
        for b in (self.btn_copy, self.btn_overlay, self.btn_save, self.btn_reset, self.btn_push): b.setFixedWidth(90)
        self.btn_settings.clicked.connect(self.show_settings)

        # Header layout
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
        self._ticker_timer.setInterval(20000)  # wait 20000ms after typing stops
        self._ticker_timer.timeout.connect(self._on_ticker_finished)

      
        # use this:
        self.txt_ticker.textChanged.connect(self._on_ticker_text_changed)


        self.lbl_side = QLabel(t.get("side", "Side"))
        self.cmb_side = QComboBox()
        self.cmb_side.addItems(["Long", "Short"])
        self.cmb_side.setCurrentText(self.state["side"])
        inputs.addWidget(self.lbl_side, r, 2)
        inputs.addWidget(self.cmb_side, r, 3)
        r += 1

        # Tick + Entry
        self.lbl_tick = QLabel(t.get("tick", "Tick"))
        self.spn_tick = QDoubleSpinBox()
        self.spn_tick.setDecimals(3)
        self.spn_tick.setRange(0.00001, 10000)
        self.spn_tick.setSingleStep(0.001)
        self.spn_tick.setValue(self.state["tick"])
        inputs.addWidget(self.lbl_tick, r, 0)
        inputs.addWidget(self.spn_tick, r, 1)

        # Entry button (click to copy current price into entry)
        self.btn_entry = QPushButton("💲 Entry")
        self.btn_entry.setFlat(True)
        self.btn_entry.setCursor(QtCore.Qt.PointingHandCursor)
        self.btn_entry.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.btn_entry.setStyleSheet("""
            QPushButton { background: transparent; border: none; font-weight: 600;; }
            QPushButton:hover { text-decoration: underline; }
        """)
        self.btn_entry.clicked.connect(self._on_entry_from_current_clicked)

        self.spn_entry = QDoubleSpinBox()
        self.spn_entry.setDecimals(2)
        self.spn_entry.setRange(0, 1e12)
        self.spn_entry.setSingleStep(0.01)
        self.spn_entry.setValue(self.state["entry"])
        inputs.addWidget(self.btn_entry, r, 2)
        inputs.addWidget(self.spn_entry, r, 3)
        r += 1

        # $ Current (button as label) + current spinner
        self.btn_current = QPushButton("💲 Current")
        self.btn_current.setFlat(True)
        self.btn_current.setCursor(QtCore.Qt.PointingHandCursor)
        self.btn_current.setToolTip(t["tooltip_current"])
        self.btn_current.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.btn_current.setStyleSheet("""
            QPushButton { background: transparent; border: none; font-weight: 600;; }
            QPushButton:hover { text-decoration: underline; }
        """)
        self.btn_current.clicked.connect(self._on_fetch_current_clicked)

        self.spn_curr = QDoubleSpinBox()
        self.spn_curr.setDecimals(2)
        self.spn_curr.setRange(0, 1e12)
        self.spn_curr.setSingleStep(0.01)
        self.spn_curr.setValue(self.state["current"])

        # Current price + Levels button
        self.btn_levels = QPushButton("📊 Levels")
        self.btn_levels.setFlat(True)
        self.btn_levels.setCheckable(True)
        self.btn_levels.setCursor(QtCore.Qt.PointingHandCursor)
        self.btn_levels.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.btn_levels.setStyleSheet("""
            QPushButton { background: transparent; border: none; font-weight: 600;; }
            QPushButton:hover { text-decoration: underline; }
        """)
        self.btn_levels.clicked.connect(self._open_pull_levels)
        self.btn_levels.setToolTip(f"Levels ({t['shortcut_levels']})")
        # Visual cue when pull window is open: checked state styles
        self.btn_levels.setStyleSheet(self.btn_levels.styleSheet() + "\nQPushButton:checked { color: #50fa7b; font-weight: 700; }")

        cur_wrap = QWidget(); cur_h = QHBoxLayout(); cur_h.setContentsMargins(0,0,0,0)
        cur_h.addWidget(self.btn_current); cur_h.addStretch(1)
        cur_wrap.setLayout(cur_h)

        inputs.addWidget(cur_wrap, r, 0, Qt.AlignVCenter | Qt.AlignLeft)
        inputs.addWidget(self.spn_curr,  r, 1)

        # Shares
        # Shares button (click to set hand size) + shares spinner
        self.btn_shares = QPushButton(t.get("shares", "Shares"))
        self.btn_shares.setFlat(True)
        self.btn_shares.setCursor(QtCore.Qt.PointingHandCursor)
        self.btn_shares.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.btn_shares.setStyleSheet("""
            QPushButton { background: transparent; border: none; font-weight: 600;; }
            QPushButton:hover { text-decoration: underline; }
        """)
        self.btn_shares.clicked.connect(self._on_set_hand_size_clicked)

        self.spn_shares = QSpinBox()
        self.spn_shares.setRange(0, 10_000_000)
        self.spn_shares.setValue(self.state["shares"])
        # restore hand size (spinner increment)
        try:
            hs = int(self.state.get("hand_size", 100) or 100)
            self.spn_shares.setSingleStep(max(1, hs))
            # align current shares to multiple of hand size
            v = int(self.spn_shares.value())
            if hs > 1 and v % hs != 0:
                newv = int(round(v / hs) * hs)
                self._set_blocked(self.spn_shares, self.spn_shares.setValue, newv)
        except Exception:
            pass
        # initialize single step from saved hand_size
        try:
            step = int(self.state.get("hand_size", 100) or 100)
        except Exception:
            step = 100
        self.spn_shares.setSingleStep(max(1, step))
        inputs.addWidget(self.btn_shares, r, 2)
        inputs.addWidget(self.spn_shares, r, 3)
        r += 1

        # Fees
        self.lbl_fees = QLabel(t.get("fees", "Fees"))
        self.spn_flat = self._spin(2, 0, 1e6, self.state["flat_fee"])
        self.spn_ps   = self._spin(4, 0, 1e3, self.state["per_share_fee"])
        fee_row = QHBoxLayout()
        fee_row.addWidget(self.spn_flat)
        fee_row.addWidget(self.spn_ps)
        fee_wrap = QWidget()
        fee_wrap.setLayout(fee_row)
        inputs.addWidget(self.lbl_fees, r, 0)
        inputs.addWidget(fee_wrap, r, 1, 1, 3)
        r += 1

        # Setup rating (A+, A, B, C, D) + Section dropdown on same row
        self.lbl_setup_rating = QLabel(t.get("setup_rating", "Setup rating"))
        self.cmb_setup_rating = QComboBox()
        # rating tiers
        self.cmb_setup_rating.addItems(["A+", "A", "B", "C", "D"])
        try:
            self.cmb_setup_rating.setCurrentIndex(int(self.state.get("setup_rating", 0)))
        except Exception:
            self.cmb_setup_rating.setCurrentIndex(0)
        # Connect rating change to recalc so output updates immediately
        self.cmb_setup_rating.currentIndexChanged.connect(self.recalc)

        # Section text input (free-form). Previously a dropdown.
        self.lbl_section = QLabel(t.get("section", "Section"))
        self.txt_section = QLineEdit(self.state.get("section", ""))
        # user edit handler: mark as user-modified and clear auto-filled flag
        def _on_section_edited(_):
            self._section_user_modified = True
            self._section_auto_filled = False
        self.txt_section.textEdited.connect(_on_section_edited)

        # Place both controls on the same row, keep them compact
        self.cmb_setup_rating.setFixedWidth(110)
        self.txt_section.setFixedWidth(160)
        inputs.addWidget(self.lbl_setup_rating, r, 0)
        inputs.addWidget(self.cmb_setup_rating, r, 1)
        inputs.addWidget(self.lbl_section, r, 2)
        inputs.addWidget(self.txt_section, r, 3)
        r += 1

        # Open/Idea + Dynamic toggle
        row = QHBoxLayout()
        self.sw_open = Switch()
        self.sw_open.setChecked(bool(self.state["open"]))
        self.sw_open.setTheme(self.state.get("ui_theme", "dark") == "dark")
        self.lbl_open = QLabel(t.get("open", "Open"))
        self.sw_open.toggled.connect(self._on_open_toggled)
        row.addWidget(self.sw_open)
        row.addWidget(self.lbl_open)
        row.addStretch(1)
        inputs.addLayout(row, r, 0, 1, 2)

        self.chk_dynamic = QCheckBox(t["dynamic"])
        self.chk_dynamic.toggled.connect(self._on_dynamic_mode)
        inputs.addWidget(self.chk_dynamic, r, 2, 1, 2)
        r += 1
        # Note (multiline)
        self.btn_note = QToolButton()
        self.btn_note.setText(t["note"])
        self.btn_note.setCheckable(True)
        self.btn_note.setChecked(not self.state.get("note_folded", False))  # checked = expanded
        self.btn_note.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.btn_note.setArrowType(Qt.DownArrow if self.btn_note.isChecked() else Qt.RightArrow)
        self.btn_note.setStyleSheet("QToolButton { border: none; font-weight: 600; }")
        self.btn_note.toggled.connect(self._on_note_toggled)

        # Place the Note button and Levels button together on the same row
        note_wrap = QWidget(); note_h = QHBoxLayout(); note_h.setContentsMargins(0,0,0,0)
        note_h.addWidget(self.btn_note)
        note_h.addWidget(self.btn_levels)
        note_h.addStretch(1)
        note_wrap.setLayout(note_h)
        inputs.addWidget(note_wrap, r, 0, 1, 4, Qt.AlignLeft); r += 1

        self.txt_note = QPlainTextEdit(self.state.get("note", ""))
        self.txt_note.setPlaceholderText(t["note_ph"])
        self.txt_note.setFixedHeight(80)
        self.txt_note.setLineWrapMode(QPlainTextEdit.WidgetWidth)
        inputs.addWidget(self.txt_note, r, 0, 1, 4)
        self.txt_note.setVisible(self.btn_note.isChecked())
        r += 1

        # --- Targets --------------------------------------------------------------
        self.sliders_box = QGroupBox(t["targets"])
        sliders = QGridLayout()
        rr = 0

        self.lbl_stop_pct = QLabel(t.get("stop_pct", "Stop %"))
        self.sld_stop = QSlider(Qt.Horizontal)
        self.sld_stop.setRange(-5000, 5000)
        self.sld_stop.setSingleStep(30)
        self.sld_stop.setValue(int(self.state["stop_pct"] * 100))
        self.spn_stop_pct = self._spin(2, -500, 500, self.state["stop_pct"], "%", 80)
        sliders.addWidget(self.lbl_stop_pct, rr, 0)
        sliders.addWidget(self.sld_stop, rr, 1)
        sliders.addWidget(self.spn_stop_pct, rr, 2)
        rr += 1

        self.lbl_tgt_pct = QLabel(t.get("tgt_pct", "Target %"))
        self.sld_tgt = QSlider(Qt.Horizontal)
        self.sld_tgt.setRange(-5000, 10000)
        self.sld_tgt.setSingleStep(30)
        self.sld_tgt.setValue(int(self.state["target_pct"] * 100))
        self.spn_tgt_pct = self._spin(2, -500, 1000, self.state["target_pct"], "%", 80)
        sliders.addWidget(self.lbl_tgt_pct, rr, 0)
        sliders.addWidget(self.sld_tgt, rr, 1)
        sliders.addWidget(self.spn_tgt_pct, rr, 2)
        rr += 1

        # Stop/Target price inputs (respect tick decimals)
        price_grid = QGridLayout()
        pr = 0
        self.spn_sl_price = QDoubleSpinBox()
        self.spn_tp_price = QDoubleSpinBox()
        for spn in (self.spn_sl_price, self.spn_tp_price):
            spn.setRange(0, 1e12)
            dec = self._decimals_for_tick(self.spn_tick.value() or 0.01)
            spn.setDecimals(dec)
            spn.setSingleStep(self.spn_tick.value() or 0.01)

        self.lbl_stop_price = QLabel(t.get("stop_price", "Stop price"))
        self.lbl_tgt_price  = QLabel(t.get("tgt_price", "Target price"))
        price_grid.addWidget(self.lbl_stop_price, pr, 0)
        price_grid.addWidget(self.spn_sl_price, pr, 1)
        pr += 1
        price_grid.addWidget(self.lbl_tgt_price, pr, 0)
        price_grid.addWidget(self.spn_tp_price, pr, 1)

        sliders.addLayout(price_grid, rr, 0, 1, 3)

        quick = QHBoxLayout()
        for label, R in (("TP = 1R", 1), ("TP = 2R", 2), ("TP = 3R", 3)):
            b = QPushButton(label)
            b.clicked.connect(lambda _, r=R: self.set_tp_R(r))
            quick.addWidget(b)

        self.sliders_box.setLayout(QVBoxLayout())
        self.sliders_box.layout().addLayout(sliders)
        self.sliders_box.layout().addLayout(quick)

        # --- Outputs --------------------------------------------------------------
        self.outputs_box = QGroupBox(t["outputs"])
        outputs = QGridLayout(self.outputs_box)
        ro = 0
        self.out_company = QLabel("—")
        self.out_section = QLabel("—")
        self.out_rating  = QLabel("—")
        self.out_stop    = QLabel("Stop: — | % —")
        self.out_tgt     = QLabel("Target: — | % —")
        self.out_rr      = QLabel("Risk $ — | Reward $ — | R — | RR —")
        self.out_pl      = QLabel("Unrealized P/L: — | Breakeven: —")
        self.preview_bar = ProfitBar()

        outputs.addWidget(self.out_company, ro, 0); ro += 1
        outputs.addWidget(self.out_section, ro, 0); ro += 1
        outputs.addWidget(self.out_rating,  ro, 0); ro += 1
        outputs.addWidget(self.out_stop,    ro, 0)
        outputs.addWidget(self.preview_bar, ro, 1, 4, 1)
        ro += 1
        outputs.addWidget(self.out_tgt, ro, 0); ro += 1
        outputs.addWidget(self.out_rr,  ro, 0); ro += 1
        outputs.addWidget(self.out_pl,  ro, 0)

        # ---- Place sections on the main grid ---------
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
        self.txt_ticker.textChanged.connect(self.recalc)
        self.sld_stop.valueChanged.connect(lambda *_: (self._sync_price_from_pct(), self.recalc()))
        self.sld_tgt.valueChanged.connect(lambda *_: (self._sync_price_from_pct(), self.recalc()))
        self.spn_stop_pct.valueChanged.connect(lambda val: self.sld_stop.setValue(int(round(val * 100))))
        self.spn_tgt_pct.valueChanged.connect(lambda val: self.sld_tgt.setValue(int(round(val * 100))))
        self.sld_stop.valueChanged.connect(lambda v: self._set_blocked(self.spn_stop_pct, self.spn_stop_pct.setValue, v/100.0))
        self.sld_tgt.valueChanged.connect(lambda v: self._set_blocked(self.spn_tgt_pct,  self.spn_tgt_pct.setValue,  v/100.0))
        self.spn_sl_price.valueChanged.connect(lambda *_: (self._enforce_tp_sl_bounds(), self._sync_pct_from_price("sl"), self._auto_lockR(), self.recalc()))
        self.spn_tp_price.valueChanged.connect(lambda *_: (self._enforce_tp_sl_bounds(), self._sync_pct_from_price("tp"), self.recalc()))
        self.spn_tick.valueChanged.connect(lambda *_: self._retune_price_spinners())

    # ---------- Pull Levels integration ----------
    def _open_pull_levels(self):
        """Open the Pull Levels window and supply callbacks."""
        try:
            from tpsl_planner.app.pull_levels_window import PullLevelsWindow
        except Exception as e:
            QMessageBox.warning(self, "Module error", f"Could not open Pull Levels window:\n{e}")
            return

        # If already open, bring to front
        if getattr(self, "pull_levels_win", None) and self.pull_levels_win.isVisible():
            try:
                self.pull_levels_win.raise_(); self.pull_levels_win.activateWindow()
            except Exception:
                pass
            return

        # Create non-modal tool window so user can interact with both windows.
        self.pull_levels_win = PullLevelsWindow(
            parent=self,
            get_current_ticker=lambda: (self.txt_ticker.text() or "").strip(),
            apply_level_callback=self._apply_level_from_pull,
            lang=self.state.get("ui_lang", "en"),
        )
        try:
            self.pull_levels_win.setWindowModality(Qt.NonModal)
        except Exception:
            pass
        # Mark button checked while window is open
        try:
            self.btn_levels.setChecked(True)
        except Exception:
            pass
        # When the pull window is closed/destroyed, clear the indicator
        try:
            self.pull_levels_win.destroyed.connect(lambda *_: self.btn_levels.setChecked(False))
        except Exception:
            pass
        try:
            # QDialog emits finished(int)
            self.pull_levels_win.finished.connect(lambda *_: self.btn_levels.setChecked(False))
        except Exception:
            pass

        self.pull_levels_win.show()
        try:
            self.pull_levels_win.raise_(); self.pull_levels_win.activateWindow()
        except Exception:
            pass

    def _apply_level_from_pull(self, price: float, role: str):
        """Apply a pulled level price as either 'sl', 'tp', or 'entry'."""
        try:
            tick = float(self.spn_tick.value() or 0.01)
            price = self.round_tick(float(price), tick)
            if role.lower() == "entry":
                self._set_blocked(self.spn_entry, self.spn_entry.setValue, price)
            elif role.lower() == "sl":
                self._set_blocked(self.spn_sl_price, self.spn_sl_price.setValue, price)
                self._enforce_tp_sl_bounds()
                self._sync_pct_from_price("sl")
            elif role.lower() == "tp":
                self._set_blocked(self.spn_tp_price, self.spn_tp_price.setValue, price)
                self._enforce_tp_sl_bounds()
                self._sync_pct_from_price("tp")
            self.recalc()
        except Exception:
            pass

    def _on_set_hand_size_clicked(self):
        """Open a small dialog to set the hand size (shares increment)."""
        try:
            cur = int(self.state.get("hand_size", 100) or 100)
            val, ok = QInputDialog.getInt(self, "Hand Size", "Hand size (shares):", cur, 1, 10_000_000, 1)
            if not ok:
                return
            self.state["hand_size"] = int(val)
            self.spn_shares.setSingleStep(max(1, int(val)))
            # align current shares to multiple of hand size
            try:
                v = int(self.spn_shares.value())
                hs = int(val)
                if hs > 1 and v % hs != 0:
                    newv = int(round(v / hs) * hs)
                    self._set_blocked(self.spn_shares, self.spn_shares.setValue, newv)
            except Exception:
                pass
            self.save_settings()
        except Exception:
            pass

    # ---------- Fetch button ----------
    def _on_fetch_current_clicked(self):
        from tpsl_planner.core.price import get_last_price, PriceError

        # re-entry guard
        if getattr(self, "_price_fetching", False):
            return
        self._price_fetching = True

        old_txt = self.btn_current.text()
        self.btn_current.setText("↻ Fetching…")
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QApplication.processEvents()  # paint immediately

        try:
            ticker_text = self.txt_ticker.text().strip() or self.state.get("ticker", "")
            res = get_last_price(ticker_text)
            self.spn_curr.setValue(round(res.price, self.spn_curr.decimals()))
            if hasattr(self, "recalc"):
                self.recalc()
        except PriceError as e:
            QMessageBox.warning(self, "Price fetch failed", str(e))
        finally:
            QApplication.restoreOverrideCursor()
            self.btn_current.setText(old_txt)      # always restore
            self._price_fetching = False

    def _on_entry_from_current_clicked(self):
        """Copy the current price into the Entry spinner and recalc."""
        try:
            val = self.spn_curr.value()
            # preserve decimals of entry spinner
            dec = self.spn_entry.decimals()
            self.spn_entry.setValue(round(val, dec))
            self.recalc()
        except Exception:
            pass


    # ---------- Retranslation ----------
    def retranslate_ui(self):
        lang = self.state.get("ui_lang", "en")
        t = _I18N[lang]
        self.setWindowTitle(t["title"]); self.title_lbl.setText(t["title"])
        self.inputs_box.setTitle(t["inputs"]); self.sliders_box.setTitle(t["targets"]); self.outputs_box.setTitle(t["outputs"])

        # labels
        self.lbl_ticker.setText("🏷️" + t["ticker"])
        self.lbl_side.setText("🚦" + t["side"])
        self.lbl_tick.setText("🔢" + t["tick"])
        # Entry button text (localized)
        try:
            self.btn_entry.setText("💲" + t["entry"])
        except Exception:
            self.btn_entry.setText("💲Entry")
        self.btn_current.setText("💲" + t["current"])
        try:
            self.btn_levels.setText("📊 " + t.get("levels", "Levels"))
        except Exception:
            self.btn_levels.setText("📊 Levels")
        # Shares button text (localized)
        try:
            self.btn_shares.setText("🤏" + t["shares"])
        except Exception:
            self.btn_shares.setText("🤏" + t.get("shares", "Shares"))
        self.lbl_fees.setText("💸" + t["fees"])
        self.lbl_stop_pct.setText("🚫" + t["stop_pct"])
        self.lbl_tgt_pct.setText("🎯" + t["tgt_pct"])
        self.lbl_stop_price.setText("🚫" + t["stop_price"])
        self.lbl_tgt_price.setText("🎯" + t["tgt_price"])
        self.chk_dynamic.setText("🌦️" + t["dynamic"])
        self.btn_note.setText("📝" + t["note"])
        self.txt_note.setPlaceholderText(t["note_ph"])


        # buttons
        self.btn_copy.setText(t["btn_copy"])
        self.btn_overlay.setText(t["btn_overlay"])
        self.btn_save.setText(t["btn_save"])
        self.btn_save.setToolTip(f"{t['btn_save']} ({t['shortcut_save']})")
        self.btn_reset.setText(t["btn_reset"])
        self.btn_push.setText(t["btn_push"])
        self.btn_push.setToolTip(f"{t['btn_push']} ({t['shortcut_push']})")
        self.btn_current.setToolTip(t["tooltip_current"])
        self.btn_levels.setToolTip(f"Levels ({t['shortcut_levels']})")
        # re-populate Side values per language, preserve choice
        was_long = self._is_long()
        self.cmb_side.blockSignals(True)
        self.cmb_side.clear()
        self.cmb_side.addItems([t["side_long_lbl"], t["side_short_lbl"]])
        self.cmb_side.setCurrentIndex(0 if was_long else 1)
        self.cmb_side.blockSignals(False)

        # Setup rating label + items (preserve selection)
        try:
            idx = self.cmb_setup_rating.currentIndex()
        except Exception:
            idx = 0
        self.cmb_setup_rating.blockSignals(True)
        self.cmb_setup_rating.clear()
        self.cmb_setup_rating.addItems(["A+", "A", "B", "C", "D"])
        idx = max(0, min(idx, self.cmb_setup_rating.count()-1))
        self.cmb_setup_rating.setCurrentIndex(idx)
        self.cmb_setup_rating.blockSignals(False)
        self.lbl_setup_rating.setText("⭐" + t.get("setup_rating", "Setup Rating"))

        # Section label (free-form text input). Preserve current text.
        try:
            cur_txt = self.txt_section.text()
        except Exception:
            cur_txt = ""
        # update label only (localized)
        self.lbl_section.setText("📂" + t.get("section", "Section"))
        # preserve existing user-entered text
        try:
            if cur_txt:
                self.txt_section.setText(cur_txt)
        except Exception:
            pass

        self._update_open_label(self.sw_open.isChecked())

    # ---------- Settings ----------
    def show_settings(self):
        lang = self.state.get("ui_lang","en")
        dlg = SettingsDialog(self, _I18N[lang])
        prime = {
            "always_on_top": self.state.get("always_on_top", False),
            "compact_mode":  self.state.get("compact_mode", False),
            "lockR_enabled": self.state.get("lockR_enabled", False),
            "lockR_value":   self.state.get("lockR_value", 2.0),
            "ui_lang":       self.state.get("ui_lang", "en"),
            "ui_theme":      self.state.get("ui_theme", "dark"),
            "font_family":   self.state.get("font_family", "Yu Gothic UI"),
            "font_size":     int(self.state.get("font_size", 10)),
        }
        dlg.load_from_state(prime)
        if dlg.exec_() == QDialog.Accepted:
            dlg.dump_to_state(self.state)
            # persist and apply settings (including font)
            try:
                self.save_settings()
            except Exception:
                pass
            try: _theme(QApplication.instance(), self.state["ui_theme"])
            except Exception: pass
            self.apply_always_on_top(self.state["always_on_top"])
            self._toggle_compact(self.state["compact_mode"])
            self.retranslate_ui()
            try:
                self.overlay.retranslate(_I18N[self.state["ui_lang"]])
            except Exception:
                pass
            
            if getattr(self, "dyn_dock", None):
                try:
                    self.dyn_dock.retranslate(self.state["ui_lang"])
                except Exception:
                    pass
            
            self.recalc()
            self.save_settings()
            try: _theme(QApplication.instance(), self.state["ui_theme"])
            except Exception: pass
            # push theme to switch + charts
            dark = (self.state["ui_theme"] == "dark")
            self.sw_open.setTheme(dark)
            self.preview_bar.setTheme(dark)
            self.retranslate_ui()

            if getattr(self, "overlay", None):
                try:
                    self.overlay.retranslate(_I18N[self.state["ui_lang"]])
                except Exception:
                    pass
            if getattr(self, "overlay", None):
                self.overlay.bar.setTheme(dark)

    # ---------- Side helper ----------
    def _is_long(self) -> bool:
        txt = (self.cmb_side.currentText() or "").strip()
        return txt in ("Long", "買い")

    def _map_section_to_canonical(self, raw: str) -> str:
        """Map a free-form section text (possibly localized) to canonical English section name.
        Falls back to the raw string when mapping isn't possible.
        """
        s = (raw or "").strip()
        if not s:
            return ""
        lang = self.state.get("ui_lang", "en")
        localized = _I18N.get(lang, {}).get("sections", SECTIONS_EN)
        # exact match against localized labels
        for i, name in enumerate(localized):
            if s.lower() == (name or "").lower():
                return SECTIONS_EN[i] if i < len(SECTIONS_EN) else s
        # exact match against canonical names
        for name in SECTIONS_EN:
            if s.lower() == name.lower():
                return name
        # heuristic keyword mapping
        k = s.lower()
        # Japanese keyword matching (common COMPANY name fragments)
        try:
            if any(x in s for x in ("電力", "電気", "電")):
                return "Utilities"
            if any(x in s for x in ("銀行", "証券", "フィナンシャル", "金融", "信託")):
                return "Financials"
            if any(x in s for x in ("石油", "ガス", "エネルギー")):
                return "Energy"
            if any(x in s for x in ("製造", "工業", "工業所", "工業株")):
                return "Industrials"
            if any(x in s for x in ("素材", "化学", "金属", "鉱業")):
                return "Materials"
            if any(x in s for x in ("食品", "飲料", "小売", "チェーン")):
                return "Consumer"
            if any(x in s for x in ("医薬", "製薬", "ヘルス", "病院", "医療")):
                return "Healthcare"
            if any(x in s for x in ("不動産", "リート", "プロパティ")):
                return "Real Estate"
            if any(x in s for x in ("運輸", "輸送", "海運", "物流")):
                return "Transportation"
        except Exception:
            pass

        # English / international keyword matching
        # More extensive keyword lists to detect large tech/consumer companies
        if any(x in k for x in ("tech", "software", "semiconductor", "chip", "cloud", "internet", "apple", "amazon", "google", "alphabet", "microsoft", "msft", "nvidia", "intel", "amd", "tesla", "meta", "facebook", "oracle", "sap", "salesforce", "adobe", "it", "ai", "machine learning", "semiconductor")): return "Tech"
        if any(x in k for x in ("bank", "financial", "finance", "broker")): return "Financials"
        if any(x in k for x in ("energy", "oil", "gas", "petro")): return "Energy"
        if any(x in k for x in ("industrial", "manufactur")): return "Industrials"
        if any(x in k for x in ("material", "metal", "mining")): return "Materials"
        if any(x in k for x in ("consumer", "retail", "food", "beverage")): return "Consumer"
        if any(x in k for x in ("health", "pharma", "pharmaceutical", "medical")): return "Healthcare"
        if any(x in k for x in ("utility", "utilities")): return "Utilities"
        if any(x in k for x in ("real", "estate", "property")): return "Real Estate"
        if any(x in k for x in ("transport", "air", "rail", "logistics", "shipping")): return "Transportation"
        if any(x in k for x in ("defense", "aerospace", "military")): return "Defense"
        return s

    # ---------- Notion push ----------
    def _collect_trade_dict(self):
        note_txt = self.txt_note.toPlainText().strip()
        entry  = self.spn_entry.value()
        curr   = self.spn_curr.value()
        shares = self.spn_shares.value()
        tick   = self.spn_tick.value()
        long_side = self._is_long()
        stop_pct = self.sld_stop.value()/10000.0
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
            "setup_rating": self.cmb_setup_rating.currentText(),
            "setup_rating_value": int(self.cmb_setup_rating.currentIndex()),
            # Section: free-form text. Try to map localized label back to canonical English.
            "section_raw": self.txt_section.text().strip(),
            "section_display": self.txt_section.text().strip(),
            "section": self._map_section_to_canonical(self.txt_section.text().strip()),
            "section_value": self.txt_section.text().strip(),
        }

    def push_to_notion_clicked(self):
        # Check env first
        if not has_valid_env():
            QMessageBox.warning(
                self,
                "Notion not configured",
                "Notion push is disabled because NOTION_TOKEN or NOTION_TRADE_DB "
                "is not set in your .env.\n\n"
                "Right-click the Push button to add or edit a .env file."
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
                f"Could not load Notion integration:\n{e}"
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


    def _retune_price_spinners(self):
        step = self.spn_tick.value() or 0.01
        dec  = self._decimals_for_tick(step)
        for spn in (self.spn_sl_price, self.spn_tp_price):
            spn.setSingleStep(step); spn.setDecimals(dec)

    def _on_open_toggled(self, checked):
        self._update_open_label(checked)
        self.recalc()

    def _update_open_label(self, checked: bool):
        t = _I18N[self.state.get("ui_lang","en")]
        self.lbl_open.setText(("🔵" + t["open"] if checked else "💡" + t["idea"]))

    def _set_blocked(self, w, setter, *args):
        w.blockSignals(True); setter(*args); w.blockSignals(False)

    @staticmethod
    def _decimals_for_tick(tick: float) -> int:
        try:
            if tick <= 0: return 2
            s = f"{tick:.10f}".rstrip("0").rstrip(".")
            return max(0, len(s.split(".")[1]) if "." in s else 0)
        except Exception:
            return 2

    @staticmethod
    def _fmt_price(v: float, dec: int, ccy: str) -> str:
        return f"{ccy}{v:,.{dec}f}"

    @staticmethod
    def _fmt_signed_pct(v: float) -> str:
        return f"{v:+.2f}%"

    def round_tick(self, price, tick): return round(price / tick) * tick if tick > 0 else price

    def stop_price_and_risk(self, entry, stop_pct, long_side, tick):
        sp = entry * (1.0 + stop_pct) if long_side else entry * (1.0 - stop_pct)
        return self.round_tick(sp, tick), abs(entry - sp)

    def target_price(self, entry, tgt_pct, long_side, tick):
        tp = entry * (1.0 + tgt_pct) if long_side else entry * (1.0 - tgt_pct)
        return self.round_tick(tp, tick)

    def set_tp_R(self, R):
        entry, tick = self.spn_entry.value(), self.spn_tick.value()
        long_side = self._is_long()
        stop_pct = self.sld_stop.value() / 10000.0
        stop_price, per_risk = self.stop_price_and_risk(entry, stop_pct, long_side, tick)
        if per_risk <= 0: return
        sign = 1 if long_side else -1
        tgt_price = entry + sign * R * per_risk
        tgt_pct = (tgt_price / entry - 1.0) * 100
        self.sld_tgt.setValue(int(round(tgt_pct * 100)))  # % -> bp

    # ---------- Settings storage ----------
    def load_settings(self):
        for k, v in DEFAULTS.items():
            self.state[k] = self.settings.value(k, v, type=type(v))
        # Backwards-compat: older versions stored `section` as an index (int).
        # If we detect a numeric legacy value, convert it to the localized
        # section label so the new free-form `txt_section` shows a human name.
        try:
            sec = self.state.get("section", "")
            # QSettings with type=str may have converted ints to strings like '0'
            if isinstance(sec, (int,)) or (isinstance(sec, str) and sec.isdigit()):
                idx = int(sec)
                lang = self.settings.value("ui_lang", self.state.get("ui_lang", "en")) or self.state.get("ui_lang", "en")
                localized = _I18N.get(lang, {}).get("sections", SECTIONS_EN)
                if 0 <= idx < len(localized):
                    self.state["section"] = localized[idx]
                else:
                    self.state["section"] = ""
        except Exception:
            pass
        self.state.setdefault("ui_lang", "en"); self.state.setdefault("ui_theme", "dark")
        self.state.setdefault("lockR_enabled", False); self.state.setdefault("lockR_value", 2.0)
        self.state.setdefault("compact_mode", False)

    def save_settings(self):
        self.settings.setValue("ticker", self.txt_ticker.text())
        self.settings.setValue("entry", self.spn_entry.value())
        self.settings.setValue("current", self.spn_curr.value())
        self.settings.setValue("shares", self.spn_shares.value())
        self.settings.setValue("tick", self.spn_tick.value())
        self.settings.setValue("side", self.cmb_side.currentText())
        self.settings.setValue("stop_pct", self.sld_stop.value()/100.0)
        self.settings.setValue("target_pct", self.sld_tgt.value()/100.0)
        self.settings.setValue("flat_fee", self.spn_flat.value())
        self.settings.setValue("per_share_fee", self.spn_ps.value())
        self.settings.setValue("always_on_top", self.state["always_on_top"])
        self.settings.setValue("open", self.sw_open.isChecked())
        self.settings.setValue("ui_lang", self.state["ui_lang"])
        self.settings.setValue("ui_theme", self.state["ui_theme"])
        self.settings.setValue("lockR_enabled", self.state["lockR_enabled"])
        self.settings.setValue("lockR_value", self.state["lockR_value"])
        self.settings.setValue("compact_mode", self.state.get("compact_mode", False))
        self.settings.setValue("note", self.txt_note.toPlainText())
        self.settings.setValue("note_folded", self.state.get("note_folded", True))
        # Setup rating (0 = None, 1-5 = rating)
        try:
            self.settings.setValue("setup_rating", int(self.cmb_setup_rating.currentIndex()))
        except Exception:
            self.settings.setValue("setup_rating", 0)
        # Section text
        try:
            self.settings.setValue("section", self.txt_section.text())
        except Exception:
            self.settings.setValue("section", "")
        # Font settings (persist from state)
        try:
            self.settings.setValue("font_family", self.state.get("font_family", "Yu Gothic UI"))
        except Exception:
            pass
        try:
            self.settings.setValue("font_size", int(self.state.get("font_size", 10)))
        except Exception:
            pass
        # Hand size (shares increment)
        try:
            self.settings.setValue("hand_size", int(self.state.get("hand_size", 100)))
        except Exception:
            self.settings.setValue("hand_size", 100)
        # Apply font immediately
        try:
            from PyQt5.QtGui import QFont
            fam = self.settings.value("font_family", self.state.get("font_family", "Yu Gothic UI"))
            sz = int(self.settings.value("font_size", int(self.state.get("font_size", 10))))
            QApplication.instance().setFont(QFont(fam, sz))
        except Exception:
            pass



    # ---------- Enforcement / sync ----------
    def _sync_price_from_pct(self):
        entry = self.spn_entry.value(); tick = self.spn_tick.value()
        long_side = self._is_long()
        stop_pct = self.sld_stop.value()/10000.0; tgt_pct = self.sld_tgt.value()/10000.0
        stop_price, _ = self.stop_price_and_risk(entry, stop_pct, long_side, tick)
        tgt_price     = self.target_price(entry, tgt_pct, long_side, tick)
        self._set_blocked(self.spn_sl_price, self.spn_sl_price.setValue, stop_price)
        self._set_blocked(self.spn_tp_price, self.spn_tp_price.setValue, tgt_price)

    def _sync_pct_from_price(self, which: str):
        entry = self.spn_entry.value()
        if entry <= 0: return
        long_side = self._is_long()
        if which == "sl":
            p = self.spn_sl_price.value()
            pct = (p/entry - 1.0) * (100 if long_side else -100)
            self._set_blocked(self.sld_stop, self.sld_stop.setValue, int(round(pct*100)))
            self._set_blocked(self.spn_stop_pct, self.spn_stop_pct.setValue, pct)
        else:
            p = self.spn_tp_price.value()
            pct = (p/entry - 1.0) * (100 if long_side else -100)
            self._set_blocked(self.sld_tgt, self.sld_tgt.setValue, int(round(pct*100)))
            self._set_blocked(self.spn_tgt_pct, self.spn_tgt_pct.setValue, pct)

    def _enforce_tp_sl_bounds(self):
        entry = self.spn_entry.value(); tick = self.spn_tick.value()
        if entry <= 0 or tick <= 0: return
        long_side = self._is_long()
        sl = self.spn_sl_price.value(); tp = self.spn_tp_price.value()
        if long_side:
            if sl >= entry: self._set_blocked(self.spn_sl_price, self.spn_sl_price.setValue, max(0.0, entry - tick))
            if tp <= entry: self._set_blocked(self.spn_tp_price, self.spn_tp_price.setValue, entry + tick)
        else:
            if sl <= entry: self._set_blocked(self.spn_sl_price, self.spn_sl_price.setValue, entry + tick)
            if tp >= entry: self._set_blocked(self.spn_tp_price, self.spn_tp_price.setValue, max(0.0, entry - tick))
        self._sync_pct_from_price("sl"); self._sync_pct_from_price("tp")

    def _toggle_compact(self, on: Optional[bool] = None):
        if on is None:
            on = not getattr(self, "_compact_cached", False)
        self._compact_cached = bool(on)
        self.state["compact_mode"] = bool(on)
        show = not self.state["compact_mode"]
        self.preview_bar.setVisible(show); self.out_rr.setVisible(show); self.out_pl.setVisible(show)

    def _auto_lockR(self):
        if not self.state.get("lockR_enabled", False): return
        R = float(self.state.get("lockR_value", 2.0))
        entry = self.spn_entry.value(); sl = self.spn_sl_price.value(); tick = self.spn_tick.value()
        long_side = self._is_long()
        per_risk = abs(entry - sl)
        if per_risk <= 0: return
        tgt = entry + (per_risk * (1 if long_side else -1) * R)
        tgt = self.round_tick(tgt, tick)
        self._set_blocked(self.spn_tp_price, self.spn_tp_price.setValue, tgt)
        self._sync_pct_from_price("tp")

    # ---------- Recalc & Markdown ----------
    def recalc(self):
        try:
            entry  = self.spn_entry.value(); curr = self.spn_curr.value(); shares = self.spn_shares.value()
            tick   = self.spn_tick.value(); long_side = self._is_long()
            stop_pct = self.sld_stop.value() / 10000.0; tgt_pct  = self.sld_tgt.value() / 10000.0
            flat_fee, ps_fee = self.spn_flat.value(), self.spn_ps.value()
            open_ = self.sw_open.isChecked()

            stop_price, per_risk = self.stop_price_and_risk(entry, stop_pct, long_side, tick)
            tgt_price = self.target_price(entry, tgt_pct, long_side, tick)

            # Only push computed prices to the price spinners when the user is
            # not actively editing them. This allows two-way adjustment: the
            # user can change the stop/target prices via the spinners and the
            # percent sliders/labels will update accordingly.
            try:
                if not self.spn_sl_price.hasFocus() and abs(self.spn_sl_price.value() - stop_price) > 1e-12:
                    self._set_blocked(self.spn_sl_price, self.spn_sl_price.setValue, stop_price)
            except Exception:
                # conservative fallback: set value if focus check fails
                if abs(self.spn_sl_price.value() - stop_price) > 1e-12:
                    self._set_blocked(self.spn_sl_price, self.spn_sl_price.setValue, stop_price)

            try:
                if not self.spn_tp_price.hasFocus() and abs(self.spn_tp_price.value() - tgt_price) > 1e-12:
                    self._set_blocked(self.spn_tp_price, self.spn_tp_price.setValue, tgt_price)
            except Exception:
                if abs(self.spn_tp_price.value() - tgt_price) > 1e-12:
                    self._set_blocked(self.spn_tp_price, self.spn_tp_price.setValue, tgt_price)

            risk_amt = per_risk * shares
            reward_ps = (tgt_price - entry) if long_side else (entry - tgt_price)
            reward_amt = reward_ps * shares
            R = (reward_ps / per_risk) if per_risk else 0.0
            RR = (reward_amt / risk_amt) if risk_amt else 0.0
            unreal_ps = (curr - entry) if long_side else (entry - curr)
            unreal_amt = unreal_ps * shares
            fees = flat_fee + ps_fee * shares
            unreal_net = unreal_amt - fees
            be_shift = fees / shares if shares > 0 else 0.0
            be_price = self.round_tick(entry + (be_shift if long_side else -be_shift), tick)

            if entry:
                if long_side:
                    spct = (stop_price / entry - 1.0) * 100.0
                    tpct = (tgt_price  / entry - 1.0) * 100.0
                else:
                    spct = (entry / stop_price - 1.0) * 100.0
                    tpct = (entry / tgt_price  - 1.0) * 100.0
            else:
                spct = tpct = 0.0

            ticker_raw = (self.txt_ticker.text() or "").strip()
            company_name = ""
            if self._ticker_looks_complete(ticker_raw):
                ticker_norm = normalize_ticker(ticker_raw)
                try:
                    company_name = get_company_name(ticker_norm) or ""
                except Exception:
                    company_name = ""
            else:
                # don’t normalize/append .T while user is still typing
                ticker_norm = ticker_raw or "-"


            is_jp = ticker_norm.endswith(".T")
            ccy = "¥" if is_jp else "$"
            p_dec = self._decimals_for_tick(tick if tick else 0.01)

            ui = _OUT_I18N[self.state.get("ui_lang","en")]
            self.out_company.setText(f"{company_name} ({ticker_norm})" if company_name else ticker_norm)
            
            # Display section and setup rating
            section_txt = (self.txt_section.text() or "").strip()
            rating_txt = self.cmb_setup_rating.currentText() if self.cmb_setup_rating.currentIndex() >= 0 else ""
            rating_stars = self._rating_to_stars(rating_txt)
            self.out_section.setText(f"📂 Section: {section_txt}" if section_txt else "📂 Section: —")
            self.out_rating.setText(f"{rating_stars} {rating_txt}" if rating_stars else "⭐ Rating: —")

            # Auto-fill section text from company name when available.
            # Behavior:
            # - Do not override if the user manually edited the field.
            # - Otherwise, overwrite when the field is empty or was previously
            #   auto-filled by the app (so changing tickers updates the value).
            try:
                if company_name:
                    if getattr(self, "_section_user_modified", False):
                        # user edited -> do not auto-overwrite
                        pass
                    else:
                        inferred = self._map_section_to_canonical(company_name)
                        # Prefer canonical sector mapped from company name
                        display_label = None
                        # 1) try mapping from company name
                        mapped = self._map_section_to_canonical(company_name)
                        if mapped and mapped in SECTIONS_EN:
                            lang = self.state.get("ui_lang", "en")
                            localized = _I18N.get(lang, {}).get("sections", SECTIONS_EN)
                            try:
                                idx = SECTIONS_EN.index(mapped)
                                display_label = localized[idx] if idx < len(localized) else mapped
                            except Exception:
                                display_label = mapped

                        # 2) if mapping failed, try yfinance sector lookup (via company_lookup)
                        if not display_label:
                            try:
                                from tpsl_planner.io.company_lookup import get_company_sector
                                sec = get_company_sector(ticker_norm)
                                if sec:
                                    mapped2 = self._map_section_to_canonical(sec)
                                    if mapped2 and mapped2 in SECTIONS_EN:
                                        lang = self.state.get("ui_lang", "en")
                                        localized = _I18N.get(lang, {}).get("sections", SECTIONS_EN)
                                        try:
                                            idx = SECTIONS_EN.index(mapped2)
                                            display_label = localized[idx] if idx < len(localized) else mapped2
                                        except Exception:
                                            display_label = mapped2
                            except Exception:
                                display_label = None

                        # Only set the field when we have a canonical sector label.
                        cur_txt = (self.txt_section.text() or "").strip()
                        was_auto = getattr(self, "_section_auto_filled", False)
                        if display_label and (not cur_txt or was_auto):
                            self.txt_section.setText(display_label)
                            self._section_auto_filled = True
                            self._section_user_modified = False
            except Exception:
                pass
            self.out_stop.setText(ui["stop_ui"].format(
                stop=self._fmt_price(stop_price, p_dec, ccy),
                spct=self._fmt_signed_pct(spct),
            ))
            self.out_tgt.setText(ui["tgt_ui"].format(
                tgt=self._fmt_price(tgt_price, p_dec, ccy),
                tpct=self._fmt_signed_pct(tpct),
            ))
            self.out_rr.setText(ui["rr_ui"].format(
                risk=self._fmt_price(risk_amt, 0, ccy),
                reward=self._fmt_price(reward_amt, 0, ccy),
                R=f"{R:.2f}",
                RR=f"{RR:.2f}",
            ))
            self.out_pl.setText(ui["upl_ui"].format(
                upl=self._fmt_price(unreal_net, 0, ccy),
                be=self._fmt_price(be_price, p_dec, ccy),
            ))

            # Markdown follows UI language
            lang = self.state.get("ui_lang","en"); md = _MD_I18N[lang]
            side_md = md["side_long"] if long_side else md["side_short"]
            title_line = f"{ticker_norm} — {company_name}" if company_name else f"{ticker_norm}"

            entry_s  = f"{entry:.{p_dec}f}"
            curr_s   = f"{curr:.{p_dec}f}"
            stop_s   = f"{stop_price:.{p_dec}f}"
            tgt_s    = f"{tgt_price:.{p_dec}f}"
            spct_s   = f"{spct:.2f}%"
            tpct_s   = f"{tpct:.2f}%"
            risk_s   = self._fmt_price(risk_amt, 0, ccy)
            reward_s = self._fmt_price(reward_amt, 0, ccy)
            upl_s    = self._fmt_price(unreal_net, 0, ccy)
            be_s     = self._fmt_price(be_price, p_dec, ccy)

            # Build rating display with stars for the markdown report
            rating_lbl = (self.cmb_setup_rating.currentText() or "").strip()
            _rating_to_stars = {"A+": 5, "A": 4, "B": 3, "C": 2, "D": 1}
            stars = ""
            try:
                stars_count = _rating_to_stars.get(rating_lbl.upper(), 0)
                if stars_count > 0:
                    stars = " " + ("⭐" * stars_count)
            except Exception:
                stars = ""

            lines = [
                md["hdr"].format(title=title_line),
                "",
                md["summary"],
                "",
                md["ticker_side"].format(ticker=ticker_norm, side=side_md),
                "",
                # include section and setup rating (localized display)
                md.get("section_line", "Section: {section}").format(section=self.txt_section.text()),
                md.get("rating_line", "Setup rating: {rating}").format(rating=(rating_lbl + stars)),
                "",
                md["entry_line"].format(entry=entry_s, curr=curr_s, shares=shares),
                "",
                md["stop_line"].format(stop=stop_s, spct=spct_s, tgt=tgt_s, tpct=tpct_s),
                "",
                md["rr_line"].format(risk=risk_s, reward=reward_s),
                md["r_line"].format(R=f"{R:.2f}", RR=f"{RR:.2f}"),
                "",
                md["unreal_line"].format(upl=upl_s, be=be_s),
                "",
                md["fee_line"].format(flat=f"{flat_fee:.0f}", ps=f"{ps_fee:.4f}"),
                md["status_open"] if open_ else md["status_idea"],
            ]
        
            note_txt = (self.txt_note.toPlainText() or "").strip()
            if note_txt:
                lines.append("")
                note_tpl = _MD_I18N[lang].get("note_line") or "{note}"
                lines.append(note_tpl.format(note=note_txt))
            

            self._last_report = "\n".join(lines)
            self.preview_bar.setTheme(self.state.get("ui_theme", "dark") == "dark")
            self.preview_bar.setValues(entry, stop_price, tgt_price, curr, long_side, open_)
            self.push_to_overlay()
        except Exception as e:
            # In EXE this prevents a silent crash
            print("Recalc error:", e, file=sys.stderr)
            QMessageBox.warning(self, "Recalc error", str(e))
    # ---------- Actions ----------
    def copy_to_clipboard(self):
        QApplication.clipboard().setText(self._last_report or "")
        old = self.btn_copy.text(); self.btn_copy.setText("Copied!")
        QTimer.singleShot(900, lambda: self.btn_copy.setText(old))

    def reset_defaults(self):
        for k, v in DEFAULTS.items():
            self.state[k] = v
        self.txt_ticker.setText(self.state["ticker"])
        self.spn_entry.setValue(self.state["entry"])
        self.spn_curr.setValue(self.state["current"])
        self.spn_shares.setValue(self.state["shares"])
        self.spn_tick.setValue(self.state["tick"])
        self.cmb_side.setCurrentIndex(0 if self.state["side"] == "Long" else 1)
        self.sld_stop.setValue(int(self.state["stop_pct"] * 90))
        self.sld_tgt.setValue(int(self.state["target_pct"] * 90))
        self.spn_flat.setValue(self.state["flat_fee"])
        self.spn_ps.setValue(self.state["per_share_fee"])
        self.sw_open.setChecked(self.state["open"])
        self.apply_always_on_top(self.state["always_on_top"])
        self.txt_note.setPlainText(self.state["note"])
        expanded = not self.state.get("note_folded", True)
        self.btn_note.setChecked(expanded)
        self._on_note_toggled(expanded)

        # restore setup rating
        try:
            self.cmb_setup_rating.setCurrentIndex(int(self.state.get("setup_rating", 0)))
        except Exception:
            self.cmb_setup_rating.setCurrentIndex(0)

        # restore section (free-form text)
        try:
            self.txt_section.setText(self.state.get("section", ""))
        except Exception:
            self.txt_section.setText("")


        try: _theme(QApplication.instance(), self.state["ui_theme"])
        except Exception: pass
        self.retranslate_ui(); self.recalc()

    def apply_always_on_top(self, on: bool):
        self.state["always_on_top"] = bool(on)
        flags = self.windowFlags()
        flags = flags | Qt.WindowStaysOnTopHint if on else flags & ~Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags); self.show()

    def toggle_overlay(self):
        if not getattr(self, "overlay", None):
            # create overlay without making it a child of the main widget;
            # we'll position it relative to the main window when showing
            self.overlay = OverlayWindow(i18n=_I18N[self.state["ui_lang"]])
            self.overlay.hide()
        if self.overlay.isVisible():
            self.overlay.hide()
        else:
            # Show overlay first (so size is known), then position it adjacent
            try:
                self.overlay.show()
                # Only auto-position if the user hasn't manually moved the overlay
                try:
                    if not getattr(self.overlay, "user_moved", False):
                        # avoid treating this programmatic move as a user move
                        try:
                            self.overlay._ignore_move_event = True
                        except Exception:
                            pass
                        self._position_overlay()
                        # clear the ignore flag on next event loop turn
                        try:
                            QTimer.singleShot(0, lambda: setattr(self.overlay, "_ignore_move_event", False))
                        except Exception:
                            pass
                except Exception:
                    try:
                        self._position_overlay()
                    except Exception:
                        pass
            except Exception:
                try:
                    geo = self.window().frameGeometry() if self.window() is not None else self.geometry()
                    self.overlay.move(geo.right() + 12, geo.top())
                except Exception:
                    pass
            self.push_to_overlay()

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
        # keep overlay adjacent to main window while visible
        try:
            # reposition after updating values
            self._position_overlay()
        except Exception:
            pass

    def _position_overlay(self):
        """Move overlay to sit adjacent to the main window without going off-screen."""
        if not getattr(self, "overlay", None):
            return
        try:
            # Get the main window's on-screen geometry (frameGeometry gives global coords)
            main_win = self.window() or self
            try:
                geo = main_win.frameGeometry()
            except Exception:
                geo = main_win.geometry()
            ow = self.overlay.width() or self.overlay.sizeHint().width(); oh = self.overlay.height() or self.overlay.sizeHint().height()
            screen = QApplication.primaryScreen().availableGeometry()
            x = geo.right() + 12
            y = geo.top()
            # If overlay would go off right edge, place it to the left of main window
            if x + ow > screen.right():
                x = geo.left() - 12 - ow
            # Clamp vertically to screen
            if y + oh > screen.bottom():
                y = max(screen.top(), screen.bottom() - oh)
            if y < screen.top():
                y = screen.top()
            self.overlay.move(int(x), int(y))
        except Exception:
            pass

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
    
    
    # ============================================================
    #  Dynamic Planner Dock Integration
    # ============================================================

    def _ensure_dyn_dock(self):
        """Create or return the dynamic planner floating window."""
        if getattr(self, "dyn_dock", None):
            return self.dyn_dock

        from tpsl_planner.app.dynamic_planner_dock import DynamicPlannerDock
        lang = self.state.get("ui_lang", "en")

        # Independent floating window (no resizing issues)
        self.dyn_dock = DynamicPlannerDock(None, lang=lang)
        self.dyn_dock.setWindowFlags(Qt.Tool | Qt.Window)
        self.dyn_dock.setWindowModality(Qt.NonModal)
        self.dyn_dock.setMinimumSize(300, 400)

        # Place it near the main window
        mw = self.window()
        try:
            geo = mw.geometry()
            self.dyn_dock.move(geo.right() + 20, geo.top() + 40)
        except Exception:
            pass

        self.dyn_dock.planned.connect(self._apply_dynamic_plan)
        return self.dyn_dock

    def _prime_dyn_context(self):
        """Send current TPSL parameters to the dock before planning."""
        side = "long" if self._is_long() else "short"
        levels = {
            "4h": {"support": [], "resistance": []},
            "d":  {"support": [], "resistance": []},
            "w":  {"support": [], "resistance": []},
        }
        equity   = 2_000_000.0   # temporary defaults
        risk_pct = 0.01
        tick = float(self.spn_tick.value() or 0.01)
        lot  = 1

        dock = self._ensure_dyn_dock()
        dock.set_context(
            entry=float(self.spn_entry.value()),
            side=side,
            levels=levels,
            equity=equity,
            risk_pct=risk_pct,
            tick=tick,
            lot=lot,
        )

    def _apply_dynamic_plan(self, plan: dict):
        """Receive plan from dock and update main UI accordingly."""
        if not plan:
            return
        if plan.get("stop") is not None:
            self._set_blocked(self.spn_sl_price, self.spn_sl_price.setValue, float(plan["stop"]))
            self._sync_pct_from_price("sl")
        tgt = plan.get("t1") if plan.get("t1") is not None else plan.get("t2")
        if tgt is not None:
            self._set_blocked(self.spn_tp_price, self.spn_tp_price.setValue, float(tgt))
            self._sync_pct_from_price("tp")
        if plan.get("shares") is not None:
            self.spn_shares.setValue(int(plan["shares"]))
        self.recalc()

    def _on_dynamic_mode(self, on: bool):
        """Toggle the Dynamic Planner floating window."""
        dock = self._ensure_dyn_dock()
        if on:
            self._prime_dyn_context()
            dock.show()
            dock.raise_()
        else:
            dock.hide()
    # ---------- Notion push button state ----------
    def _update_push_button_state(self):
        """Enable/disable the Push button based on .env / Notion config."""
        ok = has_valid_env()
        self.btn_push.setEnabled(ok)
        if ok:
            # normal tooltip
            self.btn_push.setToolTip("")
        else:
            # explain why it's disabled
            self.btn_push.setToolTip(
                "Notion push disabled: set NOTION_TOKEN and NOTION_TRADE_DB "
                "in your .env (right-click for .env options)."
            )

# Demo harness
if __name__ == "__main__":
    app = QApplication(sys.argv)
    try: _theme(app, DEFAULTS["ui_theme"])
    except Exception: pass
    win = QMainWindow(); w = TPSLWidget(win); win.setCentralWidget(w)
    win.resize(620, 620); win.show()
    sys.exit(app.exec())
