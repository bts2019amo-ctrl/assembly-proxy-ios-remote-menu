@echo off
title Layla Assembly Proxy + Remote Menu
cd /d "%~dp0"
echo.
echo  Installing deps (mitmproxy + lz4)...
py -m pip install -r requirements.txt -q
echo.
echo  Starting...
echo  - Assembly proxy : port 7777
echo  - Remote Menu UI : port 8080  (open in browser)
echo.
py run.py --host 0.0.0.0 --port 7777 --menu-port 8080
pause
