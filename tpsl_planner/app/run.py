# -*- coding: utf-8 -*-
import os, sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import QCoreApplication, Qt
from tpsl_planner.charts.theme import enable_dracula
from tpsl_planner.io.env_tools import ensure_env_file


def main():
    # --- High DPI scaling (must come before QApplication) ---
    try:
        QCoreApplication.setAttribute(QCoreApplication.AA_EnableHighDpiScaling, True)
        QCoreApplication.setAttribute(QCoreApplication.AA_UseHighDpiPixmaps, True)
    except Exception:
        pass

    # --- Windows app ID for taskbar grouping ---
    if sys.platform.startswith("win"):
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Cless.TPSLCalculator.1.1")
        except Exception:
            pass

    # --- Create the application ---
    app = QApplication(sys.argv)
    app.setFont(QFont("Yu Gothic UI", 10))

    # --- Ensure .env exists and load it ---
    ensure_env_file()

    # --- Apply theme ---
    try:
        enable_dracula(app)
    except Exception as e:
        print(f"[Theme] Failed to apply Dracula theme: {e}")

    # --- Set application icon if available ---
    icon_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),  # go up from app/ to tpsl_planner/
        "assets",
        "app.ico",
    )
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    else:
        print(f"[Icon] Icon not found: {icon_path}")

    # --- Build main window ---
    from tpsl_planner.app.widgets import TPSLWidget
    win = QMainWindow()
    win.setWindowTitle("TP-SL Planner")
    w = TPSLWidget(win)
    win.setCentralWidget(w)
    win.resize(680, 960)

    # Center window on screen
    try:
        geo = app.desktop().availableGeometry()
        win.move(
            geo.center().x() - win.width() // 2,
            geo.center().y() - win.height() // 2
        )
    except Exception:
        pass

    # --- Show and run ---
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
