@echo off
echo Starting bots...

start .venv/Scripts/python.exe run_vk.py
start .venv/Scripts/python.exe run_tg.py

echo Both bots are running!
pause