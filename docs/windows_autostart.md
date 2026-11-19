# Windows Autostart

This project now includes Windows scripts to make the backend start automatically.

## What This Solves

- keeps the FastAPI backend available after reboot
- avoids manual `python run.py` every time the PC starts
- makes Tailscale remote access much more reliable

## Important Note

Your agent is not a purely headless server.
Some tools interact with your desktop session, open apps, or work with user folders.

Because of that:

- `Logon` trigger is the safest default for full PC control
- `Startup` trigger is supported for earlier backend launch, but desktop-interaction tools may still need a logged-in session

## Files

- `scripts/windows/start-backend.ps1`
- `scripts/windows/install-backend-autostart.ps1`
- `scripts/windows/uninstall-backend-autostart.ps1`

## Install Autostart

Recommended mode:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\install-backend-autostart.ps1
```

This installs a scheduled task named `MyAgentBackend` that starts on your Windows login.
It uses standard user permissions in this mode, which is usually enough for normal agent work.

If your Python executable is not on PATH, pass it explicitly:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\install-backend-autostart.ps1 -PythonExe "C:\Path\To\python.exe"
```

If you want startup before login:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\install-backend-autostart.ps1 -Trigger Startup
```

Use that mode only if you understand the tradeoff:

- API startup happens earlier
- interactive desktop tools may still require login

## Remove Autostart

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\uninstall-backend-autostart.ps1
```

## Logs

Autostart logs are written to:

- `backend/logs/autostart.log`
- `backend/logs/activity.log`
- `backend/logs/tool_activity.log`

## Verify It Works

1. Install the scheduled task.
2. Reboot or sign out/sign in.
3. Check `backend/logs/autostart.log`.
4. Open `http://localhost:8000/health` on the PC.
5. From your phone, test the Tailscale backend URL in the app.

## Why The Path Fixes Matter

The backend now resolves:

- `.env`
- logs
- SQLite database path

relative to the backend directory instead of the current working directory.

That makes scheduled startup much more reliable.
