# system_tool.py — Complete PC system information
# Agent can check CPU, RAM, disk, battery, processes

import psutil
import platform
import os
from datetime import datetime

def get_cpu_info() -> str:
    """Get detailed CPU information"""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count   = psutil.cpu_count()
        cpu_freq    = psutil.cpu_freq()
        freq        = round(cpu_freq.current, 2) if cpu_freq else "N/A"
        return f"""🖥️ CPU Info:
  Usage:      {cpu_percent}%
  Cores:      {cpu_count}
  Frequency:  {freq} MHz"""
    except Exception as e:
        return f"❌ Error: {str(e)}"

def get_ram_info() -> str:
    """Get detailed RAM information"""
    try:
        ram     = psutil.virtual_memory()
        used    = round(ram.used    / (1024**3), 2)
        total   = round(ram.total   / (1024**3), 2)
        free    = round(ram.available / (1024**3), 2)
        percent = ram.percent
        return f"""🧠 RAM Info:
  Used:       {used} GB
  Free:       {free} GB
  Total:      {total} GB
  Usage:      {percent}%"""
    except Exception as e:
        return f"❌ Error: {str(e)}"

def get_disk_info() -> str:
    """Get disk usage information"""
    try:
        disk    = psutil.disk_usage('/')
        used    = round(disk.used  / (1024**3), 2)
        total   = round(disk.total / (1024**3), 2)
        free    = round(disk.free  / (1024**3), 2)
        percent = disk.percent
        return f"""💾 Disk Info:
  Used:       {used} GB
  Free:       {free} GB
  Total:      {total} GB
  Usage:      {percent}%"""
    except Exception as e:
        return f"❌ Error: {str(e)}"

def get_battery_info() -> str:
    """Get battery status"""
    try:
        battery = psutil.sensors_battery()
        if not battery:
            return "🔌 No battery found — desktop PC"
        percent   = battery.percent
        plugged   = "Plugged in" if battery.power_plugged else "On battery"
        time_left = ""
        if battery.secsleft > 0:
            mins = battery.secsleft // 60
            hrs  = mins // 60
            mins = mins % 60
            time_left = f"\n  Time left:  {hrs}h {mins}m"
        return f"""🔋 Battery Info:
  Level:      {percent}%
  Status:     {plugged}{time_left}"""
    except Exception as e:
        return f"❌ Error: {str(e)}"

def get_running_processes(top: int = 10) -> str:
    """Get top running processes by CPU usage"""
    try:
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                processes.append(proc.info)
            except:
                pass
        processes = sorted(
            processes,
            key=lambda x: x['cpu_percent'] or 0,
            reverse=True
        )[:top]
        result = f"⚙️ Top {top} Processes:\n"
        for p in processes:
            result += f"  {p['name'][:25]:<25} CPU: {p['cpu_percent']}%  RAM: {round(p['memory_percent'] or 0, 1)}%\n"
        return result
    except Exception as e:
        return f"❌ Error: {str(e)}"

def get_network_info() -> str:
    """Get network information"""
    try:
        hostname  = platform.node()
        net_io    = psutil.net_io_counters()
        sent      = round(net_io.bytes_sent     / (1024**2), 2)
        received  = round(net_io.bytes_recv     / (1024**2), 2)
        return f"""🌐 Network Info:
  Hostname:   {hostname}
  Sent:       {sent} MB
  Received:   {received} MB"""
    except Exception as e:
        return f"❌ Error: {str(e)}"

def get_system_summary() -> dict:
    """Get complete system summary"""
    try:
        summary_text = f"""
{'='*40}
SYSTEM SUMMARY - {datetime.now().strftime('%Y-%m-%d %H:%M')}
{'='*40}
{get_cpu_info()}

{get_ram_info()}

{get_disk_info()}

{get_battery_info()}

{get_network_info()}
{'='*40}
"""

        return {
            "success": True,
            "action": "get_system_summary",
            "message": "System summary retrieved successfully.",
            "data": {
                "summary": summary_text
            },
        }

    except Exception as e:
        return {
            "success": False,
            "action": "get_system_summary",
            "message": f"Failed to get system summary: {e}",
            "data": {},
        }


def kill_process(name: str) -> str:
    """Kill a process by name"""
    try:
        killed = 0
        for proc in psutil.process_iter(['name']):
            if name.lower() in proc.info['name'].lower():
                proc.kill()
                killed += 1
        if killed:
            return f"✅ Killed {killed} process(es) named: {name}"
        return f"❌ No process found named: {name}"
    except Exception as e:
        return f"❌ Error: {str(e)}"