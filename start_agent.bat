@echo off
title My Agent
echo Starting My Agent...

cd /d C:\Users\anilr\OneDrive\Documents\my-agent\backend
start "My Agent Backend" /min cmd /k "python run.py"

timeout /t 4 /nobreak >nul

start "Cloudflare Tunnel" /min cmd /k "cd /d C:\Users\anilr\OneDrive\Documents\my-agent && .\cloudflared.exe tunnel --url http://localhost:8000"

echo My Agent is running!
echo Local:  http://localhost:8000/ui
echo Remote: Check Tunnel window for URL
exit