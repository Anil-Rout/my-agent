# pc_profile.py — Collect and cache complete PC information
# Runs once at startup, stores profile, injects into agent context

import json
import os
import platform
import socket
import subprocess
from datetime import datetime
from pathlib import Path

import psutil

from config.paths import BACKEND_DIR

PROFILE_FILE = BACKEND_DIR / "pc_profile.json"


def _run_cmd(cmd: str) -> str:
    """Run a shell command and return output."""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True,
            text=True, timeout=5
        )
        return result.stdout.strip()
    except Exception:
        return ""


def _get_cpu_name() -> str:
    try:
        out = _run_cmd(
            'wmic cpu get Name /value'
        )
        for line in out.splitlines():
            if "Name=" in line:
                return line.split("=", 1)[1].strip()
    except Exception:
        pass
    return platform.processor()


def _get_gpu() -> str:
    try:
        out = _run_cmd(
            'wmic path win32_VideoController get Name /value'
        )
        gpus = []
        for line in out.splitlines():
            if "Name=" in line:
                name = line.split("=", 1)[1].strip()
                if name:
                    gpus.append(name)
        return ", ".join(gpus) if gpus else "Unknown"
    except Exception:
        return "Unknown"


def _get_installed_apps() -> list:
    """Get list of major installed applications."""
    try:
        out = _run_cmd(
            'wmic product get Name /value'
        )
        apps = []
        for line in out.splitlines():
            if "Name=" in line:
                name = line.split("=", 1)[1].strip()
                if name:
                    apps.append(name)
        return sorted(apps[:50])  # Limit to 50
    except Exception:
        return []


def _get_drives() -> list:
    """Get all disk drives info."""
    drives = []
    for disk in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(disk.mountpoint)
            drives.append({
                "drive": disk.mountpoint,
                "filesystem": disk.fstype,
                "total_gb": round(usage.total / (1024**3), 1),
                "free_gb": round(usage.free / (1024**3), 1),
                "used_gb": round(usage.used / (1024**3), 1),
                "percent_used": usage.percent,
            })
        except Exception:
            pass
    return drives


def _get_network_info() -> dict:
    """Get network adapters and IPs."""
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        adapters = {}
        for name, addrs in psutil.net_if_addrs().items():
            for addr in addrs:
                if addr.family == socket.AF_INET and not addr.address.startswith('127'):
                    adapters[name] = addr.address
        return {
            "hostname": hostname,
            "local_ip": local_ip,
            "adapters": adapters,
        }
    except Exception:
        return {}


def _get_display_info() -> str:
    """Get screen resolution."""
    try:
        out = _run_cmd(
            'wmic path Win32_VideoController get CurrentHorizontalResolution,CurrentVerticalResolution /value'
        )
        h, v = "", ""
        for line in out.splitlines():
            if "CurrentHorizontalResolution=" in line:
                h = line.split("=", 1)[1].strip()
            if "CurrentVerticalResolution=" in line:
                v = line.split("=", 1)[1].strip()
        if h and v:
            return f"{h}x{v}"
    except Exception:
        pass
    return "Unknown"


def _get_windows_version() -> str:
    try:
        out = _run_cmd('winver 2>nul || ver')
        version = platform.version()
        release = platform.release()
        return f"Windows {release} (Build {version})"
    except Exception:
        return platform.platform()


def build_pc_profile() -> dict:
    """Collect comprehensive PC profile."""
    ram = psutil.virtual_memory()
    battery = psutil.sensors_battery()
    cpu_freq = psutil.cpu_freq()

    profile = {
        "collected_at": datetime.now().isoformat(),

        # Identity
        "computer_name": os.environ.get("COMPUTERNAME", socket.gethostname()),
        "username": os.environ.get("USERNAME", os.environ.get("USER", "unknown")),
        "user_home": str(Path.home()),

        # OS
        "os": _get_windows_version(),
        "os_architecture": platform.machine(),
        "python_version": platform.python_version(),

        # CPU
        "cpu_name": _get_cpu_name(),
        "cpu_cores_physical": psutil.cpu_count(logical=False),
        "cpu_cores_logical": psutil.cpu_count(logical=True),
        "cpu_max_freq_mhz": round(cpu_freq.max, 0) if cpu_freq else "Unknown",

        # RAM
        "ram_total_gb": round(ram.total / (1024**3), 1),

        # GPU
        "gpu": _get_gpu(),

        # Display
        "display_resolution": _get_display_info(),

        # Storage
        "drives": _get_drives(),

        # Battery
        "has_battery": battery is not None,
        "battery_percent": round(battery.percent, 1) if battery else None,
        "on_ac_power": battery.power_plugged if battery else True,

        # Network
        "network": _get_network_info(),

        # Common paths
        "paths": {
            "desktop": str(Path.home() / "OneDrive" / "Desktop"),
            "documents": str(Path.home() / "Documents"),
            "downloads": str(Path.home() / "Downloads"),
            "pictures": str(Path.home() / "Pictures"),
            "videos": str(Path.home() / "Videos"),
            "music": str(Path.home() / "Music"),
        },
    }

    return profile


def save_profile(profile: dict) -> None:
    PROFILE_FILE.write_text(
        json.dumps(profile, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )


def load_profile() -> dict | None:
    if not PROFILE_FILE.exists():
        return None
    try:
        return json.loads(PROFILE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return None


def get_or_build_profile() -> dict:
    """Load cached profile or build fresh one."""
    profile = load_profile()
    if profile:
        # Refresh if older than 24 hours
        try:
            collected = datetime.fromisoformat(profile["collected_at"])
            age_hours = (datetime.now() - collected).total_seconds() / 3600
            if age_hours < 24:
                return profile
        except Exception:
            pass
    profile = build_pc_profile()
    save_profile(profile)
    return profile


def format_profile_for_prompt(profile: dict) -> str:
    """Format PC profile as a clean context string for the agent."""
    drives_text = ""
    for d in profile.get("drives", []):
        drives_text += (
            f"    {d['drive']} — {d['total_gb']}GB total, "
            f"{d['free_gb']}GB free ({d['percent_used']}% used)\n"
        )

    network = profile.get("network", {})
    adapters = network.get("adapters", {})
    adapters_text = ", ".join(
        f"{name}: {ip}" for name, ip in adapters.items()
    ) if adapters else "Unknown"

    paths = profile.get("paths", {})

    battery_text = ""
    if profile.get("has_battery"):
        status = "plugged in" if profile.get("on_ac_power") else "on battery"
        battery_text = f"\nBattery:     {profile.get('battery_percent')}% ({status})"

    return f"""
━━ MY PC DETAILS ━━
Computer:    {profile.get('computer_name')}
User:        {profile.get('username')}
OS:          {profile.get('os')}
Architecture:{profile.get('os_architecture')}

CPU:         {profile.get('cpu_name')}
             {profile.get('cpu_cores_physical')} physical cores, {profile.get('cpu_cores_logical')} logical cores
             Max {profile.get('cpu_max_freq_mhz')} MHz

RAM:         {profile.get('ram_total_gb')} GB total
GPU:         {profile.get('gpu')}
Display:     {profile.get('display_resolution')}{battery_text}

Storage:
{drives_text}
Network:
    Hostname: {network.get('hostname')}
    Local IP: {network.get('local_ip')}
    Adapters: {adapters_text}

Common paths:
    Desktop:   {paths.get('desktop')}
    Documents: {paths.get('documents')}
    Downloads: {paths.get('downloads')}
    Pictures:  {paths.get('pictures')}
━━━━━━━━━━━━━━━━━━
""".strip()