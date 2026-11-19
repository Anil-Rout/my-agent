# scheduler_tool.py — Reminders and scheduled tasks

import schedule
import time
import threading
import os
from datetime import datetime

reminders = []

def add_reminder(message: str, time_str: str) -> str:
    """
    Set a reminder at specific time
    time_str format: HH:MM e.g. 14:30
    """
    try:
        def job():
            os.system(f'msg * "REMINDER: {message}"')
            print(f"\n🔔 REMINDER: {message}")

        schedule.every().day.at(time_str).do(job)
        reminders.append({"message": message, "time": time_str})
        return f"✅ Reminder set: '{message}' at {time_str}"
    except Exception as e:
        return f"❌ Error: {str(e)}"

def add_reminder_in_minutes(message: str, minutes: int) -> str:
    """Set a reminder after X minutes from now — fires exactly once"""
    try:
        def job():
            os.system(f'msg * "REMINDER: {message}"')
            print(f"\n🔔 REMINDER: {message}")
            return schedule.CancelJob

        schedule.every(minutes).minutes.do(job)
        reminders.append({
            "message": message,
            "time": f"in {minutes} minutes"
        })
        return f"✅ Reminder set: '{message}' in {minutes} minutes"
    except Exception as e:
        return f"❌ Error: {str(e)}"

def list_reminders() -> str:
    """List all active reminders"""
    if not reminders:
        return "📅 No reminders set"
    result = "📅 Active Reminders:\n"
    for i, r in enumerate(reminders, 1):
        result += f"  {i}. '{r['message']}' at {r['time']}\n"
    return result

def clear_reminders() -> str:
    """Clear all reminders"""
    schedule.clear()
    reminders.clear()
    return "✅ All reminders cleared"

def start_scheduler():
    """Start scheduler in background thread"""
    def run():
        while True:
            schedule.run_pending()
            time.sleep(30)
    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    return "✅ Scheduler running"