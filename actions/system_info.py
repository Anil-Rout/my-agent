# system_info.py — Get PC system information

import psutil
import platform
import os

def get_cpu_usage() -> str:
    """Get current CPU usage percentage"""
    return f"CPU Usage: {psutil.cpu_percent(interval=1)}%"

def get_ram_usage() -> str:
    """Get current RAM usage"""
    ram = psutil.virtual_memory()
    used = round(ram.used / (1024**3), 2)
    total = round(ram.total / (1024**3), 2)
    percent = ram.percent
    return f"RAM: {used}GB used out of {total}GB ({percent}%)"

def get_running_processes() -> list:
    """Get list of running processes"""
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
        try:
            processes.append(proc.info)
        except:
            pass
    return sorted(processes, key=lambda x: x['cpu_percent'], reverse=True)[:10]

def get_disk_usage() -> str:
    """Get disk usage"""
    disk = psutil.disk_usage('/')
    used = round(disk.used / (1024**3), 2)
    total = round(disk.total / (1024**3), 2)
    percent = disk.percent
    return f"Disk: {used}GB used out of {total}GB ({percent}%)"

def get_system_summary() -> str:
    """Get full system summary"""
    return f"""
System: {platform.system()} {platform.release()}
{get_cpu_usage()}
{get_ram_usage()}
{get_disk_usage()}
    """.strip()
