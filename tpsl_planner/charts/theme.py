from PyQt5.QtWidgets import QApplication, QStyleFactory
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtCore import Qt

def _reset(app: QApplication) -> None:
    """Clear any previous stylesheet/palette so themes don't stack."""
    app.setStyleSheet("")                          # remove QSS
    app.setPalette(app.style().standardPalette())  # reset palette to style default
    try:
        app.setStyle(QStyleFactory.create("Fusion"))
    except Exception:
        pass

def enable_dracula(app: QApplication) -> None:
    _reset(app)
    pal = QPalette()

    bg        = QColor("#282A36")
    base      = QColor("#1E1F29")
    alt_base  = QColor("#343746")
    btn       = QColor("#44475A")
    text      = QColor("#F8F8F2")
    sel       = QColor("#6272A4")
    link      = QColor("#8BE9FD")
    visited   = QColor("#BD93F9")
    bright    = QColor("#FF5555")
    tooltip   = QColor("#44475A")
    disabled  = QColor("#7A7A7A")

    pal.setColor(QPalette.Window, bg)
    pal.setColor(QPalette.WindowText, text)
    pal.setColor(QPalette.Base, base)
    pal.setColor(QPalette.AlternateBase, alt_base)
    pal.setColor(QPalette.ToolTipBase, tooltip)
    pal.setColor(QPalette.ToolTipText, text)
    pal.setColor(QPalette.Text, text)
    pal.setColor(QPalette.Button, btn)
    pal.setColor(QPalette.ButtonText, text)
    pal.setColor(QPalette.BrightText, bright)
    pal.setColor(QPalette.Highlight, sel)
    pal.setColor(QPalette.HighlightedText, text)
    pal.setColor(QPalette.Link, link)
    pal.setColor(QPalette.LinkVisited, visited)

    pal.setColor(QPalette.Disabled, QPalette.WindowText, disabled)
    pal.setColor(QPalette.Disabled, QPalette.Text, disabled)
    pal.setColor(QPalette.Disabled, QPalette.ButtonText, disabled)
    pal.setColor(QPalette.Disabled, QPalette.Base, QColor("#2A2B36"))
    pal.setColor(QPalette.Disabled, QPalette.Window, QColor("#2C2D3A"))
    pal.setColor(QPalette.Disabled, QPalette.Highlight, QColor("#3E4255"))
    pal.setColor(QPalette.Disabled, QPalette.HighlightedText, QColor("#999AA4"))

    app.setPalette(pal)
    app.setStyleSheet("""
        QToolTip { color:#F8F8F2; background:#44475A; border:1px solid #6272A4; }
        QGroupBox { border:1px solid #3B3F51; border-radius:6px; margin-top:12px; padding-top:6px; }
        QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding:0 8px; color:#F8F8F2; }
        QPushButton:hover { background-color:#50546A; }
        QSlider::groove:horizontal { border:1px solid #3A3D4C; height:8px; background:#343746; border-radius:4px; }
        QSlider::handle:horizontal { background:#6272A4; border:1px solid #3A3D4C; width:16px; margin:-4px 0; border-radius:8px; }
    """)

def enable_light(app: QApplication) -> None:
    _reset(app)
    pal = QPalette()

    bg        = QColor("#F5F6FA")
    base      = QColor("#FFFFFF")
    alt_base  = QColor("#F0F2F7")
    btn       = QColor("#E2E6EF")
    text      = QColor("#1C1E26")
    sel       = QColor("#3D7DFF")
    link      = QColor("#0B70E7")
    visited   = QColor("#6E49CB")
    bright    = QColor("#D00000")
    tooltip   = QColor("#FFFFFF")
    disabled  = QColor("#8C9098")

    pal.setColor(QPalette.Window, bg)
    pal.setColor(QPalette.WindowText, text)
    pal.setColor(QPalette.Base, base)
    pal.setColor(QPalette.AlternateBase, alt_base)
    pal.setColor(QPalette.ToolTipBase, tooltip)
    pal.setColor(QPalette.ToolTipText, text)
    pal.setColor(QPalette.Text, text)
    pal.setColor(QPalette.Button, btn)
    pal.setColor(QPalette.ButtonText, text)
    pal.setColor(QPalette.BrightText, bright)
    pal.setColor(QPalette.Highlight, sel)
    pal.setColor(QPalette.HighlightedText, QColor("#FFFFFF"))
    pal.setColor(QPalette.Link, link)
    pal.setColor(QPalette.LinkVisited, visited)

    pal.setColor(QPalette.Disabled, QPalette.WindowText, disabled)
    pal.setColor(QPalette.Disabled, QPalette.Text, disabled)
    pal.setColor(QPalette.Disabled, QPalette.ButtonText, disabled)
    pal.setColor(QPalette.Disabled, QPalette.Base, QColor("#F3F4F8"))
    pal.setColor(QPalette.Disabled, QPalette.Window, QColor("#ECEEF4"))
    pal.setColor(QPalette.Disabled, QPalette.Highlight, QColor("#B8C9FF"))
    pal.setColor(QPalette.Disabled, QPalette.HighlightedText, QColor("#FFFFFF"))

    app.setPalette(pal)
    app.setStyleSheet("""
        QToolTip { color:#1C1E26; background:#FFFFFF; border:1px solid #C9CEDA; }
        QGroupBox { border:1px solid #D6DBE7; border-radius:6px; margin-top:12px; padding-top:6px; }
        QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding:0 8px; color:#1C1E26; }
        QPushButton:hover { background-color:#D7DBE6; }
        QSlider::groove:horizontal { border:1px solid #C9CEDA; height:8px; background:#F0F2F7; border-radius:4px; }
        QSlider::handle:horizontal { background:#3D7DFF; border:1px solid #3A68CC; width:16px; margin:-4px 0; border-radius:8px; }
    """)

def apply_theme(app: QApplication, theme_name: str = "dark") -> None:
    if theme_name and theme_name.lower() in ("dark", "dracula"):
        enable_dracula(app)
    else:
        enable_light(app)
