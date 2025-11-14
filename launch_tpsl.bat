@echo off
rem === Launch TP-SL Planner ===
setlocal
call .venv\Scripts\activate.bat
python -m tpsl_planner
endlocal
