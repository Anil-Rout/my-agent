# Remote Access With Tailscale

This project is designed to keep the real PC-control backend on your home Windows machine.
Do not move the PC executor to a public cloud host.

## Goal

Use Tailscale so your phone or laptop can reach your home PC over a private network.

Example flow:

```text
Phone / Laptop
    |
    v
Tailscale private network
    |
    v
Home PC running FastAPI on port 8000
```

## Why Tailscale

- Free for personal use
- Safer than exposing a public port
- Works behind NAT and home routers
- Gives your PC a stable private address
- Good fit for personal remote control

## Setup Steps

### 1. Install Tailscale

Install Tailscale on:

- your home PC
- your phone

Sign into the same Tailscale account on both devices.

### 2. Start the backend on the home PC

Run the backend on your home PC:

```bash
cd backend
python run.py
```

Make sure the API responds locally:

- `http://localhost:8000/health`
- `http://localhost:8000/docs`

### 3. Find your home PC Tailscale address

In the Tailscale app or admin page, look for your PC's private IP.

It will look something like:

- `100.x.y.z`

You may also have a MagicDNS hostname if enabled.

Examples:

- `http://100.x.y.z:8000`
- `http://your-pc-name.tailnet-name.ts.net:8000`

### 4. Configure the Flutter app

The Flutter app now supports a configurable backend URL.

You can set it in:

- the login screen
- the settings screen

Use your Tailscale address, for example:

```text
http://100.x.y.z:8000
```

Then use the built-in **Test Connection** button.

### 5. Log in and control the agent

Once the connection test passes:

- enter your agent password
- log in
- send chat/tool requests through the private Tailscale URL

## Android Notes

Android needs internet permission and cleartext HTTP support when using a private `http://` Tailscale URL.

This repo now enables:

- `android.permission.INTERNET`
- `android:usesCleartextTraffic="true"`

in the main Android manifest.

## Recommended Next Step

After Tailscale access works, make the backend run automatically on your home PC:

- use the Windows autostart scripts in `docs/windows_autostart.md`
- keep the backend available after reboot

That is the next step toward full remote control.
