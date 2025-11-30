# tpsl_planner/app/pull_levels_window.py

from __future__ import annotations

from typing import Callable, Optional, List
from pathlib import Path
import sys

from PyQt5.QtWidgets import (
    QDialog,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QCheckBox,
    QSpinBox,
    QComboBox,
    QTableWidget,
    QTableWidgetItem,
    QGroupBox,
    QMessageBox,
    QApplication,
)
from PyQt5.QtCore import Qt

# QSettings for persistence
from PyQt5.QtCore import QSettings
APP_ORG = "Cless"
APP_NAME = "TPSL-Plannerr"

# ---------------------------------------------
# Imports
# ---------------------------------------------
from tpsl_planner.core.levels import pull_levels_for_ticker, Level, LevelsConfig
from tpsl_planner.core.auto_plan import compute_auto_plan
from tpsl_planner.core.trend import compute_trend, trend_comment
# from tpsl_planner.core.trend import compute_trend, TrendConfig


# ---------------------------------------------
# Helper: Normalize JP tickers for yfinance
# ---------------------------------------------
def normalize_symbol(ticker: str) -> str:
    t = ticker.strip().upper()
    if t.isdigit() and (4 <= len(t) <= 5):   # JP stock code
        return t + ".T"
    return t


# ---------------------------------------------
# MAIN WINDOW
# ---------------------------------------------
class PullLevelsWindow(QDialog):
    def __init__(
        self,
        parent: Optional[QWidget] = None,
        get_current_ticker: Optional[Callable[[], str]] = None,
        apply_level_callback: Optional[Callable[[float, str], None]] = None,
        lang: str = "en",
    ):
        super().__init__(parent)
        self.lang = lang if lang in ("en", "ja") else "en"
        self._i18n = {
            "en": {
                "title": "Pull Levels",
                "request": "Request",
                "ticker": "Ticker:",
                "timeframes": "Timeframes:",
                "max_levels": "Max levels:",
                "current_price": "Current price:",
                "long_side": "Long side",
                "pull": "Pull Levels",
                "auto": "Auto Plan",
                "time_window": "Time Window",
                "duration": "Lookback Duration",
                "bars": "Lookback Bars",
                "months": "Months",
                "years": "Years",
                "send_sl": "Send as SL",
                "send_tp": "Send as TP",
                "send_entry": "Send as Entry",
                "close": "Close",
                "no_ticker": "Please enter a ticker.",
                "pull_error": "Pull error",
                "no_ticker": "Please enter a ticker.",
                "cannot_load_price": "Cannot load price: {err}",
                "trend": "Trend",
                "please_enter_ticker_first": "Please enter a ticker first.",
                "auto_no_levels": "No levels – pull levels first.",
            },
            "ja": {
                "title": "レベル取得",
                "request": "リクエスト",
                "ticker": "銘柄:",
                "timeframes": "時間軸:",
                "max_levels": "最大レベル:",
                "current_price": "現在値:",
                "long_side": "買いサイド",
                "pull": "レベルを取得",
                "auto": "自動プラン",
                "time_window": "時間ウィンドウ",
                "duration": "ルックバック期間",
                "bars": "ルックバックバー数",
                "months": "月",
                "years": "年",
                "send_sl": "SLとして送信",
                "send_tp": "TPとして送信",
                "send_entry": "エントリーとして送信",
                "close": "閉じる",
                "no_ticker": "銘柄を入力してください。",
                "pull_error": "取得エラー",
                "no_ticker": "銘柄を入力してください。",
                "cannot_load_price": "価格を取得できません: {err}",
                "trend": "トレンド",
                "please_enter_ticker_first": "まず銘柄を入力してください。",
                "auto_no_levels": "レベルがありません — まず取得してください。",
            }
        }
        self.setWindowTitle(self._i18n[self.lang]["title"])
        self.resize(750, 520)

        self.get_current_ticker = get_current_ticker
        self.apply_level_callback = apply_level_callback

        self._rows: List[Level] = []
        self._last_synced_ticker = ""  # Track ticker to detect changes
        self._ticker_sync_timer = None  # Timer for live ticker sync
        self.settings = QSettings(APP_ORG, APP_NAME)

        self._build_ui()
        self.sync_ticker_from_main()

    # ---------------------------------------------
    # UI
    # ---------------------------------------------
    def _build_ui(self):
        main = QVBoxLayout(self)

        # --- Controls ---
        controls_box = QGroupBox(self._i18n[self.lang]["request"])
        controls_layout = QGridLayout(controls_box)

        r = 0
        controls_layout.addWidget(QLabel(self._i18n[self.lang]["ticker"]), r, 0)
        self.txt_ticker = QLineEdit()
        controls_layout.addWidget(self.txt_ticker, r, 1, 1, 3)
        r += 1

        # Timeframes
        controls_layout.addWidget(QLabel(self._i18n[self.lang]["timeframes"]), r, 0, Qt.AlignTop)
        tf_layout = QVBoxLayout()

        self.chk_tf_w = QCheckBox("W")
        self.chk_tf_d = QCheckBox("D")
        self.chk_tf_4h = QCheckBox("4H")
        self.chk_tf_1h = QCheckBox("1H")
        self.chk_tf_30m = QCheckBox("30m")

        for c in (self.chk_tf_w, self.chk_tf_d, self.chk_tf_4h, self.chk_tf_1h, self.chk_tf_30m):
            c.setChecked(True)
            tf_layout.addWidget(c)

        controls_layout.addLayout(tf_layout, r, 1)

        controls_layout.addWidget(QLabel(self._i18n[self.lang]["max_levels"]), r, 2)
        self.spn_max = QSpinBox()
        self.spn_max.setRange(1, 500)
        self.spn_max.setValue(80)
        controls_layout.addWidget(self.spn_max, r, 3)
        r += 1

        # Current price
        controls_layout.addWidget(QLabel(self._i18n[self.lang]["current_price"]), r, 0)
        self.txt_curr = QLineEdit()
        controls_layout.addWidget(self.txt_curr, r, 1)

        self.chk_long = QCheckBox(self._i18n[self.lang]["long_side"])
        self.chk_long.setChecked(True)
        controls_layout.addWidget(self.chk_long, r, 2, 1, 2)
        r += 1

        # Time Window
        controls_layout.addWidget(QLabel(self._i18n[self.lang]["time_window"]), r, 0)
        self.cmb_time_window = QComboBox()
        self.cmb_time_window.addItems([self._i18n[self.lang]["duration"], self._i18n[self.lang]["bars"]])
        controls_layout.addWidget(self.cmb_time_window, r, 1)

        self.lbl_time_param = QLabel(self._i18n[self.lang]["months"])
        controls_layout.addWidget(self.lbl_time_param, r, 2)

        self.spn_time_param = QSpinBox()
        self.spn_time_param.setRange(1, 120)
        self.spn_time_param.setValue(12)
        controls_layout.addWidget(self.spn_time_param, r, 3)
        r += 1

        # Wire time window mode change to update label
        self.cmb_time_window.currentIndexChanged.connect(self._on_time_window_mode_changed)

        # Load saved time window settings
        self._load_time_window_settings()

        # Buttons
        btn_layout = QHBoxLayout()
        self.btn_pull = QPushButton(self._i18n[self.lang]["pull"])
        self.btn_auto = QPushButton(self._i18n[self.lang]["auto"])
        self.btn_use_as_sl = QPushButton(self._i18n[self.lang]["send_sl"])
        self.btn_use_as_tp = QPushButton(self._i18n[self.lang]["send_tp"])
        self.btn_send_entry = QPushButton(self._i18n[self.lang]["send_entry"])
        self.btn_close = QPushButton(self._i18n[self.lang]["close"])

        btn_layout.addWidget(self.btn_pull)
        btn_layout.addWidget(self.btn_auto)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_use_as_sl)
        btn_layout.addWidget(self.btn_use_as_tp)
        btn_layout.addWidget(self.btn_send_entry)
        btn_layout.addWidget(self.btn_close)
        controls_layout.addLayout(btn_layout, r, 0, 1, 4)

        main.addWidget(controls_box)

        # Levels table
        self.tbl = QTableWidget()
        self.tbl.setColumnCount(5)
        self.tbl.setHorizontalHeaderLabels(["TF", "Price", "Type", "Score", "Label"])
        self.tbl.setSelectionBehavior(self.tbl.SelectRows)
        self.tbl.setSelectionMode(self.tbl.SingleSelection)
        self.tbl.setEditTriggers(self.tbl.NoEditTriggers)
        self.tbl.horizontalHeader().setStretchLastSection(True)
        main.addWidget(self.tbl)

        # Signals
        self.btn_pull.clicked.connect(self._on_pull_clicked)
        self.btn_auto.clicked.connect(self._on_auto_plan_clicked)
        self.btn_use_as_sl.clicked.connect(lambda: self._apply_selected("sl"))
        self.btn_use_as_tp.clicked.connect(lambda: self._apply_selected("tp"))
        self.btn_send_entry.clicked.connect(lambda: self._apply_selected("entry"))
        self.btn_close.clicked.connect(self.close)

    # ---------------------------------------------
    # Sync ticker
    # ---------------------------------------------
    def sync_ticker_from_main(self):
        """Sync ticker from main window (called once at init or manually)."""
        if not self.get_current_ticker:
            return
        t = (self.get_current_ticker() or "").strip()
        if t:
            self.txt_ticker.setText(t)
            self._last_synced_ticker = t

    def _start_ticker_sync(self):
        """Start a timer to periodically sync ticker from main window."""
        if not self.get_current_ticker:
            return
        from PyQt5.QtCore import QTimer
        if self._ticker_sync_timer is None:
            self._ticker_sync_timer = QTimer(self)
            self._ticker_sync_timer.timeout.connect(self._check_ticker_changed)
            self._ticker_sync_timer.setInterval(500)  # Check every 500ms
        self._ticker_sync_timer.start()

    def _stop_ticker_sync(self):
        """Stop the ticker sync timer."""
        if self._ticker_sync_timer is not None:
            self._ticker_sync_timer.stop()

    def _check_ticker_changed(self):
        """Check if main window ticker has changed and update Pull window."""
        if not self.get_current_ticker:
            return
        current = (self.get_current_ticker() or "").strip()
        if current and current != self._last_synced_ticker:
            self.txt_ticker.setText(current)
            self._last_synced_ticker = current

    def showEvent(self, event):
        """Start ticker sync when window is shown."""
        super().showEvent(event)
        self._start_ticker_sync()

    def hideEvent(self, event):
        """Stop ticker sync when window is hidden."""
        super().hideEvent(event)
        self._stop_ticker_sync()

    def _on_time_window_mode_changed(self, index):
        """Update label and range when time window mode changes."""
        if index == 0:  # Duration
            self.lbl_time_param.setText(self._i18n[self.lang]["months"])
            self.spn_time_param.setRange(1, 120)
            self.spn_time_param.setValue(12)
        else:  # Bars
            self.lbl_time_param.setText(self._i18n[self.lang]["bars"])
            self.spn_time_param.setRange(10, 5000)
            self.spn_time_param.setValue(500)

    def _apply_time_window(self, df, mode: str, param: int):
        """Apply a time window to trim the dataframe before level finding.
        
        Args:
            df: DataFrame with datetime index and OHLC columns.
            mode: "duration" (months lookback) or "bars" (count lookback).
            param: int – either months (1–120) or bars count (10–5000).
        
        Returns:
            Trimmed DataFrame.
        """
        if df.empty:
            return df
        
        try:
            import pandas as pd
            from dateutil.relativedelta import relativedelta
            if mode == "duration":
                # Lookback by calendar months
                cutoff = pd.Timestamp.now() - relativedelta(months=param)
                return df[df.index >= cutoff]
            elif mode == "bars":
                # Lookback by bar count
                return df.iloc[-param:] if len(df) > param else df
            else:
                return df
        except Exception:
            return df

    def _on_time_window_mode_changed(self, index):
        """Update label and range when time window mode changes."""
        if index == 0:  # Duration
            self.lbl_time_param.setText(self._i18n[self.lang]["months"])
            self.spn_time_param.setRange(1, 120)
            self.spn_time_param.setValue(12)
        else:  # Bars
            self.lbl_time_param.setText(self._i18n[self.lang]["bars"])
            self.spn_time_param.setRange(10, 5000)
            self.spn_time_param.setValue(500)
        # Save settings whenever mode changes
        self._save_time_window_settings()

    def _load_time_window_settings(self):
        """Load time window settings from QSettings."""
        try:
            mode_idx = int(self.settings.value("pull_levels_window_mode", 0))
            param_val = int(self.settings.value("pull_levels_window_param", 12))
            
            self.cmb_time_window.blockSignals(True)
            self.cmb_time_window.setCurrentIndex(max(0, min(mode_idx, 1)))
            self.cmb_time_window.blockSignals(False)
            
            # Set range and value based on mode
            if mode_idx == 0:  # Duration
                self.spn_time_param.setRange(1, 120)
                self.spn_time_param.setValue(max(1, min(param_val, 120)))
            else:  # Bars
                self.spn_time_param.setRange(10, 5000)
                self.spn_time_param.setValue(max(10, min(param_val, 5000)))
            
            self.lbl_time_param.setText(self._i18n[self.lang]["months"] if mode_idx == 0 else self._i18n[self.lang]["bars"])
        except Exception:
            pass

    def _save_time_window_settings(self):
        """Save time window settings to QSettings."""
        try:
            self.settings.setValue("pull_levels_window_mode", int(self.cmb_time_window.currentIndex()))
            self.settings.setValue("pull_levels_window_param", int(self.spn_time_param.value()))
        except Exception:
            pass

    # ---------------------------------------------
    # Helpers
    # ---------------------------------------------
    def _selected_timeframes(self):
        out = []
        if self.chk_tf_w.isChecked(): out.append("W")
        if self.chk_tf_d.isChecked(): out.append("D")
        if self.chk_tf_4h.isChecked(): out.append("4H")
        if self.chk_tf_1h.isChecked(): out.append("1H")
        if self.chk_tf_30m.isChecked(): out.append("30m")
        return out

    def _load_current_price(self, ticker: str) -> float:
        import yfinance as yf
        symbol = normalize_symbol(ticker)
        tk = yf.Ticker(symbol)

        # fast_info sometimes behaves like a pandas object; avoid "if fi"
        try:
            fi = tk.fast_info
            if fi is not None and "last_price" in fi:
                return float(fi["last_price"])
        except Exception:
            pass

        # fallback: 1m history
        hist = tk.history(period="1d", interval="1m")
        if not hist.empty:
            # yfinance uses 'Close' capitalised
            return float(hist["Close"].iloc[-1])

        raise RuntimeError(f"Could not fetch price for {ticker}")


    def _load_trend_ohlcv(self, ticker: str):
        import yfinance as yf
        symbol = normalize_symbol(ticker)

        df = yf.download(
            symbol,
            period="5y",  # Increased to support larger lookback windows
            interval="1d",
            auto_adjust=True,   # explicit -> no FutureWarning
            progress=False,
        )

        if df.empty:
            raise RuntimeError(f"No OHLC data for {ticker}")

        # standardize column names
        df = df.rename(
            columns={
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
            }
        )

        # For now we only need close; keeping OHLC for future features is fine
        return df[["open", "high", "low", "close"]].dropna()

    # ---------------------------------------------
    # Pull levels
    # ---------------------------------------------
    def _on_pull_clicked(self):
        ticker = self.txt_ticker.text().strip()
        if not ticker:
            QMessageBox.warning(self, self._i18n[self.lang]["pull_error"], self._i18n[self.lang]["no_ticker"])
            return

        tfs = self._selected_timeframes() or ["W", "D", "4H", "1H", "30m"]
        max_levels = self.spn_max.value()

        tf_core = [tf for tf in tfs if tf.lower() != "30m"]
        include_m30 = any(tf.lower() == "30m" for tf in tfs)

        cfg = LevelsConfig(
            tfs=tuple(tf_core) if tf_core else ("W", "D", "4H"),
            include_m30=include_m30
        )

        # Get time window settings
        window_mode = "duration" if self.cmb_time_window.currentIndex() == 0 else "bars"
        window_param = self.spn_time_param.value()

        try:
            # For now, pull_levels_for_ticker doesn't support time window directly,
            # so we'll fetch full data and apply the window before passing to levels
            levels = pull_levels_for_ticker(
                ticker,
                tfs,
                max_levels=max_levels,
                df=None,
                config=cfg,
                symbol=ticker,
            )
        except Exception as e:
            QMessageBox.warning(self, self._i18n[self.lang]["pull_error"], str(e))
            return

        self._populate_table(levels)

    # ---------------------------------------------
    # Auto Plan
    # ---------------------------------------------
    def _on_auto_plan_clicked(self):
        if not self._rows:
            QMessageBox.warning(self, self._i18n[self.lang]["auto"], self._i18n[self.lang].get("auto_no_levels", "No levels – pull levels first."))
            return

        ticker = self.txt_ticker.text().strip()
        if not ticker:
            QMessageBox.warning(self, self._i18n[self.lang]["auto"], self._i18n[self.lang].get("please_enter_ticker_first", self._i18n[self.lang].get("no_ticker", "Please enter a ticker.")))
            return

        # --- AUTO PRICE ---
        try:
            current_price = self._load_current_price(ticker)
            self.txt_curr.setText(f"{current_price:.2f}")
        except Exception as e:
            QMessageBox.warning(self, self._i18n[self.lang]["auto"], self._i18n[self.lang]["cannot_load_price"].format(err=e))
            return

        long_side = self.chk_long.isChecked()

        # ----------------------------------------------------------
        # NEW: Call YOUR compute_auto_plan (returns 3 values)
        # ----------------------------------------------------------
        try:
            entry, sl, tp = compute_auto_plan(
                self._rows,
                current_price,
                long_side
            )
        except Exception as e:
            QMessageBox.warning(self, self._i18n[self.lang]["auto"], str(e))
            return

        # side string
        side = "LONG" if long_side else "SHORT"
        
        # ----------------------------------------------------------
        # TREND (daily OHLC via trend engine)
        # ----------------------------------------------------------
        try:
            df = self._load_trend_ohlcv(ticker)

            # full trend evaluation (EMA stack, slope, RSI/MACD/ADX if present)
            trend = compute_trend(df)

            # popup with detailed comment (includes EMA8/21/50 like your screenshot)
            msg = trend_comment(trend)
            QMessageBox.information(self, self._i18n[self.lang]["trend"], msg)

            # one-line summary for the Auto Plan message box
            trend_line = (
                f"Trend: {trend.label}  "
                f"(score {trend.score:.0f}, dir {trend.direction}, vol {trend.vol_state})"
            )

        except Exception as e:
            trend_line = f"Trend: n/a ({e})"

        # ----------------------------------------------------------
        # TREND
        # ----------------------------------------------------------
            try:
                trend = compute_trend(df)
            except ValueError as e:
                QMessageBox.warning(self, "Trend", f"Trend not available: {e}")
                return

            msg = trend_comment(trend)

            QMessageBox.information(self, "Trend", msg)
            
            trend_line = (
                f"Trend: {trend.label}  "
                f"(score {trend.score:.0f}, dir {trend.direction}, vol {trend.vol_state})"
            )
        except Exception as e:
            trend_line = f"Trend: n/a ({e})"

        # ----------------------------------------------------------
        # SHOW PLAN
        # ----------------------------------------------------------
        
        
        entry_text  = f"{entry:.2f}" if entry is not None else "N/A"
        sl_text     = f"{sl:.2f}" if sl is not None else "N/A"
        tp_text     = f"{tp:.2f}" if tp is not None else "N/A"

        QMessageBox.information(
            self,
            "Auto Plan",
            f"{trend_line}\n\n"
            f"Side  : {side}\n"
            f"Entry : {entry_text}\n"
            f"Stop  : {sl_text}\n"
            f"Target: {tp_text}"
        )


    # ---------------------------------------------
    # Populate table
    # ---------------------------------------------
    def _populate_table(self, levels: list[Level]):
        self.tbl.setRowCount(0)
        self._rows = []

        for lvl in levels:
            row = self.tbl.rowCount()
            self.tbl.insertRow(row)

            self.tbl.setItem(row, 0, QTableWidgetItem(str(lvl.timeframe)))
            self.tbl.setItem(row, 1, QTableWidgetItem(f"{lvl.price:.2f}"))
            self.tbl.setItem(row, 2, QTableWidgetItem(str(lvl.kind)))
            self.tbl.setItem(row, 3, QTableWidgetItem(f"{lvl.score:.3f}"))
            self.tbl.setItem(row, 4, QTableWidgetItem(str(lvl.label)))

            self._rows.append(lvl)

        self.tbl.resizeColumnsToContents()

    # ---------------------------------------------
    # Apply level
    # ---------------------------------------------
    def _apply_selected(self, role: str):
        idx = self.tbl.currentRow()
        if idx < 0 or idx >= len(self._rows):
            return

        lvl = self._rows[idx]

        if self.apply_level_callback:
            self.apply_level_callback(lvl.price, role)
        else:
            QMessageBox.information(
                self,
                "Apply level (test)",
                f"Would apply {role.upper()} = {lvl.price:.2f}\n"
                f"({lvl.timeframe} {lvl.kind}, {lvl.label})"
            )


# ---------------------------------------------
# STANDALONE TEST
# ---------------------------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = PullLevelsWindow(None, None, None)
    win.show()
    sys.exit(app.exec_())
