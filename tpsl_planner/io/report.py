# -*- coding: utf-8 -*-
"""Simple TXT/PDF report generator."""
from pathlib import Path
import datetime

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    HAS_REPORTLAB = True
except Exception:
    HAS_REPORTLAB = False

def generate_trade_report(trade: dict, folder: str = "reports", make_pdf: bool = True) -> str:
    Path(folder).mkdir(exist_ok=True)
    date_str = datetime.date.today().strftime("%Y%m%d")
    base_name = f"{trade.get('ticker','-')}_{date_str}"
    txt_path = Path(folder) / f"{base_name}.txt"

    content = f"""🧭 --Trade Setup Summary--

🎯 Ticker: {trade.get('ticker','')}
📈 Side: {trade.get('side','')}

💰 Entry: {trade.get('entry','')}
🛑 Stop: {trade.get('stop','')}
🎯 Target: {trade.get('target','')}
📊 Shares: {trade.get('shares','')}
⚖️ R-Multiple: {trade.get('r','')}
🗒 Notes: {trade.get('notes','')}

📅 Date: {datetime.date.today().isoformat()}
"""
    txt_path.write_text(content, encoding="utf-8")

    if make_pdf and HAS_REPORTLAB:
        pdf_path = Path(folder) / f"{base_name}.pdf"
        c = canvas.Canvas(str(pdf_path), pagesize=A4)
        t = c.beginText(40, 800)
        t.setFont("Helvetica", 11)
        for line in content.splitlines():
            t.textLine(line)
        c.drawText(t)
        c.save()
        return str(pdf_path)
    return str(txt_path)
