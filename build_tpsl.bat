@echo off
rem === Build TP-SL Planner EXE ===
setlocal
call .venv\Scripts\activate.bat
pyinstaller --noconsole --onefile --name tpsl_planner ^
  --icon "tpsl_planner\assets\app.ico" ^
  --add-data "tpsl_planner\assets;assets" ^
  --collect-all PyQt5 ^
  --collect-all matplotlib ^
  tpsl_planner\__main__.py
endlocal
pause
