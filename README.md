📈 TPSL Planner

Advanced Trade Risk, TP/SL, and Position Planning Toolkit
A core module of the SenseiBot trading ecosystem

🧠 Overview

TPSL Planner is a modern, fast, and precise Take-Profit / Stop-Loss planning application designed for discretionary and systematic traders.
It provides real-time risk calculations, position sizing, multi-currency support, trade journaling output, and a clean UI built in PyQt5.

This app is part of the wider SenseiBot project, a modular trading assistant ecosystem that includes charting bots, Notion integration, and automated daily reporting tools.

The goal is simple:

Help traders make disciplined, repeatable, and high-quality trade decisions.

✨ Key Features
🔢 Real-time Trade Calculations

Stop-loss and target price auto-calculation

Risk per share / total risk / total reward

R and RR multiple

Unrealized P/L with fees

Break-even price calculation

🏛 Broker-friendly

Supports:

Japanese tick sizes (TSE)

U.S. tick sizes

Yen (¥) and USD ($) auto-switching

Share-based calculations (100-share TSE lots compatible)

🧩 Dynamic UI

Dark/Light theme

Multi-language (EN/JP)

Ticker auto-normalization (e.g., 7203 → 7203.T)

Company name lookup

Instant visual preview bar (entry → SL → TP)

📝 One-Click Markdown Output

Perfect for journals, Telegram bots, or Notion:

Format follows UI language

Includes all trade metrics

Includes optional trader notes

Compatible with SenseiBot’s push-to-Notion module

🎯 Trade Modeling Tools

Long/Short toggle

Live price override

Open vs. Idea status

Adjustable fees (flat + per-share)

Snap-to-tick enforcement

🛠 Technology Stack

Python 3.10+

PyQt5 (UI)

pandas / numpy (math utilities)

Requests (meta + name lookup)

PyInstaller (EXE builds)

Notion API (optional integration)

📦 Installation
1. Clone the repository
git clone https://github.com/YOUR-USERNAME/tpsl_planner.git
cd tpsl_planner

2. Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

3. Install dependencies
pip install -r requirements.txt

4. Run the app
python -m tpsl_app

5. Build EXE (optional)
pyinstaller --onefile --name tpsl_app launcher.py

📁 Project Structure
tpsl_planner/
│
├── tpsl_app/
│   ├── widgets.py        # Main UI logic
│   ├── dynamic_planner/  # Experimental dynamic TPSL module
│   ├── charts/           # UI preview logic
│   ├── i18n/             # Language dictionaries
│   ├── io/               # Env tools, Notion push, lookup utils
│   └── assets/           # Icons, images
│
├── launcher.py           # Entrypoint for EXE
├── requirements.txt
└── README.md

🧪 Development Notes

The app automatically recalculates on every input change.

All critical calculations are protected with exception handling to avoid EXE crashes.

Markdown report generation is modular and can be used by external bots or servers.

The UI is built with “enterprise style” structure: signals, slots, and calc pipelines.

🌐 SenseiBot Ecosystem (Optional Integrations)

TPSL Planner is compatible with:

SenseiBot Telegram Charting Bot

Notion Trade Journal Template

Daily/Weekly trade reporting modules

Dynamic TPSL engine (Alpha version)

📣 Future Roadmap

Live data plugin (polygon, stooq, yfinance)

Auto-detect institutional liquidity zones

Dynamic ATR-based stop suggestion

Cloud sync for plans + overlay

Mobile companion (Swift/Kotlin)

🧑‍💻 Contribution

Contributions are welcome!
If you’d like to extend the visuals, add new trade modules, or integrate new data sources, feel free to open issues or submit pull requests.

📜 License

This project currently uses a Proprietary License under the SenseiBot ecosystem (modifiable if open-source is desired).
If you wish to use components commercially, please contact the project owner.

⭐ Supporting the Project

If TPSL Planner helps you trade better, please consider starring ⭐ the repo.
It helps the project grow and signals interest for future features.
