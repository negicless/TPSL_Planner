# -*- coding: utf-8 -*-
# dynamic_planner_dock.py — Floating Dynamic Planner (no circular imports)

from __future__ import annotations
from PyQt5.QtCore import pyqtSignal as Signal, Qt
from PyQt5.QtWidgets import (
    QWidget, QFormLayout, QVBoxLayout, QHBoxLayout,
    QLabel, QDoubleSpinBox, QSpinBox, QComboBox, QCheckBox, QPushButton
)

# --- Localized strings for Dynamic Planner (self-contained) ---
_DYN_I18N = {
    "en": {
        "dynamic_planner_title": "Dynamic Trade Planner",
        "equity": "Equity",
        "risk_pct": "Risk %",
        "levels": "Levels",
        "apply_plan": "Apply Plan",
        "plan": "Plan",
        "apply_to_main": "Apply to Main",
        "missing_entry": "Missing entry in context.",
        "plan_preview_placeholder": "— Plan preview will appear here —",
        "regime": "Regime",
        "use_structure_first": "Use structure first",
        "cap_targets_at_structure": "Cap targets at structure",
        "ath": "ATH",
        "hi_52w": "52W High",
        "cap_t2_ath": "Cap T2 at ATH",
        "earn_days": "Earnings in (days)",
        "atr": "ATR",
        "atr_pct": "ATR%",
        "rvol": "RVOL",
        "auto": "Auto",
        "calm": "Calm",
        "normal": "Normal",
        "hot": "Hot",
        "wild": "Wild",
        "plan_failed": "Plan failed.",
    },
    "ja": {
        "dynamic_planner_title": "ダイナミック・トレードプランナー",
        "equity": "資金",
        "risk_pct": "リスク %",
        "levels": "レベル",
        "apply_plan": "プランを適用",
        "plan": "プラン作成",
        "apply_to_main": "メインに適用",
        "missing_entry": "エントリー値が未設定です。",
        "plan_preview_placeholder": "— ここにプランのプレビューが表示されます —",
        "regime": "レジーム",
        "use_structure_first": "構造を優先",
        "cap_targets_at_structure": "目標を構造で制限",
        "ath": "最高値 (ATH)",
        "hi_52w": "52週高値",
        "cap_t2_ath": "T2 を ATH で制限",
        "earn_days": "決算まで（日）",
        "atr": "ATR",
        "atr_pct": "ATR%",
        "rvol": "RVOL",
        "auto": "自動",
        "calm": "低ボラ",
        "normal": "通常",
        "hot": "高ボラ",
        "wild": "極高ボラ",
        "plan_failed": "プラン作成に失敗しました。",
    },
}

# 👇 keep these engine imports as you had
from tpsl_planner.core.engine import VolMetrics, LevelSet, Levels, MarketConfig, plan_dynamic_tpsl, fmt2


class DynamicPlannerDock(QWidget):
    planned = Signal(dict)

    def __init__(self, parent=None, lang: str = "en"):
        super().__init__(parent)
        self.lang = lang if lang in _DYN_I18N else "en"
        self.i18n = _DYN_I18N[self.lang]

        self.setWindowFlags(Qt.Tool | Qt.Window)
        self.setWindowModality(Qt.NonModal)
        self.setMinimumSize(300, 400)

        outer = QVBoxLayout(self)
        form = QFormLayout()

        # ---- keep label refs so we can retranslate later ----
        self.lbl_atr      = QLabel(self.i18n["atr"])
        self.lbl_atr_pct  = QLabel(self.i18n["atr_pct"])
        self.lbl_rvol     = QLabel(self.i18n["rvol"])
        self.spn_atr      = self._dspin(0, 1e9, 0.01, 4)
        self.spn_atr_pct  = self._dspin(0, 1.0, 0.0001, 4)
        self.spn_rvol     = self._dspin(0, 10.0, 0.01, 2); self.spn_rvol.setValue(1.0)
        form.addRow(self.lbl_atr,     self.spn_atr)
        form.addRow(self.lbl_atr_pct, self.spn_atr_pct)
        form.addRow(self.lbl_rvol,    self.spn_rvol)

        self.chk_structure_first = QCheckBox(); self.chk_structure_first.setChecked(True)
        self.chk_cap_targets_at_structure = QCheckBox(); self.chk_cap_targets_at_structure.setChecked(True)
        self.lbl_structure_first = QLabel(self.i18n["use_structure_first"])
        self.lbl_cap_targets     = QLabel(self.i18n["cap_targets_at_structure"])
        form.addRow(self.lbl_structure_first, self.chk_structure_first)
        form.addRow(self.lbl_cap_targets,     self.chk_cap_targets_at_structure)

        self.spn_ath       = self._dspin(0, 1e9, 1, 2)
        self.spn_52w       = self._dspin(0, 1e9, 1, 2)
        self.chk_cap_t2_ath = QCheckBox()
        self.spn_earn_days = QSpinBox(); self.spn_earn_days.setRange(0, 365)
        self.lbl_ath       = QLabel(self.i18n["ath"])
        self.lbl_52w       = QLabel(self.i18n["hi_52w"])
        self.lbl_cap_t2    = QLabel(self.i18n["cap_t2_ath"])
        self.lbl_earn_days = QLabel(self.i18n["earn_days"])
        form.addRow(self.lbl_ath,       self.spn_ath)
        form.addRow(self.lbl_52w,       self.spn_52w)
        form.addRow(self.lbl_cap_t2,    self.chk_cap_t2_ath)
        form.addRow(self.lbl_earn_days, self.spn_earn_days)

        self.cmb_regime = QComboBox()
        self._populate_regime_items()
        self.lbl_regime = QLabel(self.i18n["regime"])
        form.addRow(self.lbl_regime, self.cmb_regime)

        outer.addLayout(form)

        # Actions & preview
        btns = QHBoxLayout()
        self.btn_plan  = QPushButton(self.i18n["plan"])
        self.btn_apply = QPushButton(self.i18n["apply_to_main"])
        self.btn_apply.setEnabled(False)
        btns.addWidget(self.btn_plan); btns.addWidget(self.btn_apply)
        outer.addLayout(btns)

        self.lbl_preview = QLabel(self.i18n["plan_preview_placeholder"])
        self.lbl_preview.setWordWrap(True)
        outer.addWidget(self.lbl_preview)

        self.btn_plan.clicked.connect(self._on_plan_clicked)
        self.btn_apply.clicked.connect(self._on_apply_clicked)

        # Context
        self.context = {"entry": None, "side": "long", "levels": None, "equity": 2_000_000.0,
                        "risk_pct": 0.01, "tick": 1.0, "lot": 1}
        self._last_result = None

        # set title last (uses i18n)
        self.setWindowTitle(self.i18n["dynamic_planner_title"])
        
    def _populate_regime_items(self):
        """(Re)fill regime combo with localized labels, preserve selection."""
        idx = getattr(self, "cmb_regime", None).currentIndex() if hasattr(self, "cmb_regime") else 0
        self.cmb_regime.clear()
        self.cmb_regime.addItems([
            self.i18n["auto"], self.i18n["calm"], self.i18n["normal"],
            self.i18n["hot"],  self.i18n["wild"]
        ])
        self.cmb_regime.setCurrentIndex(max(0, idx))

    def retranslate(self, lang: str):
        """Live language switch."""
        self.lang = lang if lang in _DYN_I18N else "en"
        self.i18n = _DYN_I18N[self.lang]

        # window title
        self.setWindowTitle(self.i18n["dynamic_planner_title"])

        # field labels
        self.lbl_atr.setText(self.i18n["atr"])
        self.lbl_atr_pct.setText(self.i18n["atr_pct"])
        self.lbl_rvol.setText(self.i18n["rvol"])
        self.lbl_structure_first.setText(self.i18n["use_structure_first"])
        self.lbl_cap_targets.setText(self.i18n["cap_targets_at_structure"])
        self.lbl_ath.setText(self.i18n["ath"])
        self.lbl_52w.setText(self.i18n["hi_52w"])
        self.lbl_cap_t2.setText(self.i18n["cap_t2_ath"])
        self.lbl_earn_days.setText(self.i18n["earn_days"])
        self.lbl_regime.setText(self.i18n["regime"])

        # buttons + preview placeholder
        self.btn_plan.setText(self.i18n["plan"])
        self.btn_apply.setText(self.i18n["apply_to_main"])
        if not self._last_result:
            self.lbl_preview.setText(self.i18n["plan_preview_placeholder"])

        # regime items (preserve selection index)
        self._populate_regime_items()
    # --- utilities ---
    def _dspin(self, lo, hi, step, decimals):
        w = QDoubleSpinBox(); w.setRange(lo, hi); w.setSingleStep(step); w.setDecimals(decimals); return w

    # --- public API from TPSLWidget ---
    def set_context(self, *, entry: float, side: str, levels: dict | None, equity: float,
                    risk_pct: float, tick: float, lot: int):
        self.context.update(dict(entry=entry, side=side, levels=levels,
                                 equity=equity, risk_pct=risk_pct, tick=tick, lot=lot))

    # --- actions ---
    def _on_plan_clicked(self):
        ctx = self.context
        if not ctx["entry"]:
            self.lbl_preview.setText(self.i18n["missing_entry"])
            return

        # ---- Allow empty/None levels (ATR-only planning fallback) ----
        lvl = ctx.get("levels") or {
            "4h": {"support": [], "resistance": []},
            "d":  {"support": [], "resistance": []},
            "w":  {"support": [], "resistance": []},
        }

        vol = VolMetrics(
            atr=self.spn_atr.value(),
            atr_pct=self.spn_atr_pct.value(),
            rvol=self.spn_rvol.value(),
        )
        levels = Levels(
            h4=LevelSet(lvl["4h"]["support"], lvl["4h"]["resistance"]),
            d  =LevelSet(lvl["d"]["support"],   lvl["d"]["resistance"]),
            w  =LevelSet(lvl["w"]["support"],   lvl["w"]["resistance"]),
        )
        regime_text = self.cmb_regime.currentText()
        # map back to engine's expected values
        regime = None if regime_text in (self.i18n["auto"],) else regime_text.lower()
        mkt = MarketConfig(tick_size=ctx["tick"], lot_size=ctx["lot"])

        res = plan_dynamic_tpsl(
            entry=ctx["entry"], side=ctx["side"], vol=vol, levels=levels,
            account_equity=ctx["equity"], risk_pct=ctx["risk_pct"], mkt=mkt, regime=regime
        )

        # post-filters
        if res.ok and self.chk_cap_t2_ath.isChecked():
            ath = self.spn_ath.value()
            if ctx["side"] == "long" and ath > 0 and res.t2 is not None:
                res.t2 = min(res.t2, ath)
            if ctx["side"] == "short" and ath > 0 and res.t2 is not None:
                res.t2 = max(res.t2, ath)

        self._last_result = res
        self.btn_apply.setEnabled(bool(res.ok))

        if not res.ok:
            self.lbl_preview.setText(f"⚠️ {res.reason or self.i18n['plan_failed']}")
            return

        preview = (
            f"{self.i18n['regime']}: {res.regime}\n"
            f"Entry: {fmt2(res.entry)} | Stop: {fmt2(res.stop)}\n"
            f"T1: {fmt2(res.t1)} ({res.r1:.2f}R)  |  T2: {fmt2(res.t2)} ({res.r2:.2f}R)\n"
            f"Shares: {res.shares}  | Risk: {int(res.risk_amount)}\n"
            f"Scale: {res.scale_plan}"
        )
        self.lbl_preview.setText(preview)

    def _on_apply_clicked(self):
        if not (self._last_result and self._last_result.ok):
            return
        self.planned.emit({
            "stop": self._last_result.stop,
            "t1": self._last_result.t1,
            "t2": self._last_result.t2,
            "shares": self._last_result.shares,
            "r1": self._last_result.r1,
            "r2": self._last_result.r2,
            "regime": self._last_result.regime,
        })
