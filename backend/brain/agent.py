# agent.py - Full function-calling agent
# AI decides which tools to use automatically.

from typing import List, TypedDict
import os
import re

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.graph import END, StateGraph
from tools.voice_output_tool import speak, stop_speaking, set_speaking_rate, set_voice
from tools.pc_profile import get_or_build_profile, format_profile_for_prompt
from brain.llm import get_llm, mark_provider_failed, mark_provider_healthy
from brain.memory import get_relevant_context, save_memory, search_memory
from brain.prompts import DEFAULT_NAME, get_system_prompt
from config.paths import TOOL_ACTIVITY_LOG_PATH, ensure_runtime_dirs, load_backend_env
from database.queries import create_task_step
from tools.smart_router import get_options_for_task, get_all_available_apps_summary

from tools.app_tool import (
    APPS,
    cancel_shutdown,
    get_open_windows,
    open_application,
    open_folder,
    restart_pc,
    shutdown_pc,
    take_screenshot,
    lock_screen,
    sleep_pc,
    take_photo_with_camera,
)
from tools.base_tool import (
    DANGEROUS_TOOLS,
    execute_tool_call,
    format_tool_result,
    precheck_tool_call,
    tool_succeeded,
)
from tools.browser_tool import (
    calculate,
    get_current_time,
    get_news,
    get_weather,
    open_website,
    search_google,
    search_web,
    search_youtube,
)
from tools.clipboard_tool import (
    get_clipboard,
    set_clipboard,
    clear_clipboard,
    append_to_clipboard,
)
from tools.code_tool import (
    install_package,
    run_code,
    run_file,
    write_and_run_code,
    write_and_save_code,
)
from tools.file_tool import (
    COMMON_FOLDERS,
    create_file,
    create_folder,
    delete_file,
    list_files,
    read_file,
    resolve_existing_folder_path,
    search_files,
)
from tools.scheduler_tool import (
    add_reminder,
    add_reminder_in_minutes,
    clear_reminders,
    list_reminders,
    start_scheduler,
)
from tools.system_tool import (
    get_battery_info,
    get_cpu_info,
    get_disk_info,
    get_network_info,
    get_ram_info,
    get_running_processes,
    get_system_summary,
    kill_process,
)
from tools.screen_tool import (
    capture_and_describe,
    save_screenshot,
    capture_and_answer,
)
from tools.window_tool import (
    list_windows,
    minimize_window,
    maximize_window,
    restore_window,
    close_window,
    focus_window,
    minimize_all_windows,
)
from tools.whatsapp_tool import (
    send_whatsapp_message,
    open_whatsapp_chat,
    add_whatsapp_contact,
    list_whatsapp_contacts,
    remove_whatsapp_contact,
    send_whatsapp_image,
    record_voice_note,
    send_whatsapp_voice,
)


from tools.learning_system import (
    get_learning_summary,
    clear_all_lessons,
    add_lesson,
)

from tools.email_tool import (
    send_email,
    reply_to_email,
    forward_email,
    get_inbox,
    read_email,
    delete_email,
    search_emails,
    get_unread_count,
    mark_email_read,
    mark_email_unread,
    get_email_config_status,
)

from tools.notepad_tool import (
    open_notepad, new_tab, write_text, append_text,
    clear_notepad, save_file, save_as, open_file_in_notepad,
    find_text, find_and_replace, select_all, copy_all_text,
    undo, redo, go_to_line, insert_datetime, toggle_word_wrap,
    close_notepad_tab, zoom_in, zoom_out, zoom_reset, get_notepad_status,
)

load_backend_env()
start_scheduler()


@tool
def tool_create_folder(folder_name: str) -> str:
    """Create a new folder. Extract ONLY the folder name, ignore location words.
    Examples:
    - 'AgentTest on my desktop' → folder_name='AgentTest'
    - 'projects folder in documents' → folder_name='projects'
    - 'new folder called test' → folder_name='test'
    """
    import re
    # Strip location words from folder name
    clean_name = re.sub(
        r'\s*(on|in|at|inside|within)\s+(my\s+)?(desktop|documents|downloads|pictures|videos|music|home|disk|drive|folder|directory).*$',
        '', folder_name, flags=re.IGNORECASE
    ).strip().strip('"\'')
    if not clean_name:
        clean_name = folder_name
    return format_tool_result(
        execute_tool_call("tool_create_folder", {"folder_name": clean_name},
                          lambda: create_folder(clean_name))
    )


@tool
def tool_create_file(filename: str, content: str = "") -> str:
    """Create a new file on the Desktop with optional content. Use this when the user wants to create, make, write, save, or generate a file. Examples: 'create a file', 'make a notes file', 'save this in a file'."""
    return create_file(filename, content)


@tool
def tool_read_file(filepath: str) -> str:
    """Read and return the contents of a file. Use this when the user wants to open, read, view, check, or see what is inside a file. Examples: 'read this file', 'open that file', 'show me file contents'."""
    return read_file(filepath)


@tool
def tool_list_files(path: str = "") -> str:
    """List all files and folders on the Desktop. Use when user wants to see, list or show files."""
    desktop = os.path.join(os.path.expanduser("~"), "OneDrive", "Desktop")
    return list_files(path if path else desktop)


@tool
def tool_search_files(keyword: str) -> str:
    """Search for files by name on the Desktop. Use this when the user wants to find, search, locate, look for, or check whether a file/folder exists. Examples: 'find my python file', 'search folder named project', 'locate notes.txt'."""
    desktop = os.path.join(os.path.expanduser("~"), "OneDrive", "Desktop")
    return search_files(desktop, keyword)


@tool
def tool_delete_file(filepath: str) -> str:
    """Delete a file or folder. Use when user wants to delete or remove a file."""
    return delete_file(filepath)


@tool
def tool_cpu_info() -> str:
    """Get current CPU usage and information. Use when user asks about CPU, processor, or computer speed."""
    return get_cpu_info()


@tool
def tool_ram_info() -> str:
    """Get current RAM/memory usage. Use when user asks about RAM, memory, or how much memory is used."""
    return get_ram_info()


@tool
def tool_disk_info() -> str:
    """Get disk/storage usage information. Use when user asks about disk, storage, or hard drive space."""
    return get_disk_info()


@tool
def tool_battery_info() -> str:
    """Get battery level and status. Use when user asks about battery, charge level, or power."""
    return get_battery_info()


@tool
def tool_system_summary() -> str:
    """Get a full system summary including CPU, RAM, disk, and battery. Use this when the user asks for overall PC status, computer health, system condition, laptop status, or wants to know how the PC is doing."""
    return get_system_summary()


@tool
def tool_running_processes() -> str:
    """Get the list of currently running processes and apps. Use this when the user asks what is running, which apps are open, what processes are active, or wants to inspect current activity on the PC."""
    return get_running_processes()


@tool
def tool_network_info() -> str:
    """Get network information and internet stats. Use when user asks about network, internet, IP address."""
    return get_network_info()


@tool
def tool_kill_process(process_name: str) -> str:
    """Kill or stop a running process by name. Use when user wants to kill, stop or close a process."""
    return kill_process(process_name)


@tool
def tool_open_app(app_name: str) -> str:
    """Open an application on the PC. Use this when the user wants to open, launch, start, run, or bring up an app or software. Examples: 'open chrome', 'launch notepad', 'start calculator', 'run vscode'."""
    return open_application(app_name)


@tool
def tool_screenshot() -> str:
    """Take a screenshot of the current screen. Use when user wants to take a screenshot or capture the screen."""
    return take_screenshot()


@tool
def tool_open_folder(folder_path: str) -> str:
    """Open a folder in File Explorer. Use when user wants to open or browse a folder."""
    return open_folder(folder_path)


@tool
def tool_open_windows() -> str:
    """Get list of currently open windows. Use when user asks what windows are open."""
    return get_open_windows()


@tool
def tool_shutdown(delay_seconds: int = 30) -> str:
    """Shutdown the PC after a delay. Use when user wants to shutdown or turn off the PC."""
    return shutdown_pc(delay_seconds)


@tool
def tool_restart(delay_seconds: int = 30) -> str:
    """Restart the PC after a delay. Use when user wants to restart or reboot the PC."""
    return restart_pc(delay_seconds)


@tool
def tool_cancel_shutdown() -> str:
    """Cancel a scheduled shutdown or restart. Use when user wants to cancel shutdown."""
    return cancel_shutdown()


@tool
def tool_write_code(code: str, filename: str = "") -> str:
    """Write and save Python code to a file on the Desktop. Use this when the user wants to write code, generate code, save code, create a Python file, or build a script without running it yet."""

    return write_and_save_code(code, filename)


@tool
def tool_run_code(code: str) -> str:
    """Run Python code and return the output. Use when user wants to run, execute or test code."""
    return run_code(code)


@tool
def tool_write_and_run(code: str) -> str:
    """Write Python code, save it, and run it immediately. Use this when the user wants both code generation and execution together. Examples: 'write python and run it', 'make a script and execute it', 'create and test this code'."""

    return write_and_run_code(code)


@tool
def tool_install_package(package_name: str) -> str:
    """Install a Python package using pip. Use when user wants to install a Python library or package."""
    return install_package(package_name)


@tool
def tool_search_web(query: str) -> str:
    """Search the web for information. Use this when the user wants to search, look up, find information online, research something, or get internet-based information."""
    return search_web(query)


@tool
def tool_get_weather(city: str) -> str:
    """Get current weather for any city. Use when user asks about weather, temperature or forecast."""
    return get_weather(city)


@tool
def tool_get_news(topic: str) -> str:
    """Get the latest news about a topic. Use this when the user asks for news, current events, latest updates, or trending updates on any subject."""
    return get_news(topic)


@tool
def tool_calculate(expression: str) -> str:
    """Calculate a math expression. Use when user wants to calculate or solve a math problem."""
    return calculate(expression)


@tool
def tool_current_time() -> str:
    """Get current date and time. Use when user asks what time or date it is."""
    return get_current_time()


@tool
def tool_search_google(query: str) -> str:
    """Open a Google search in the browser. Use this when the user wants to search Google directly, look something up in a browser, or open Google results for a query."""
    return search_google(query)


@tool
def tool_search_youtube(query: str) -> str:
    """Search YouTube in browser. Use when user wants to search or find videos on YouTube."""
    return search_youtube(query)


@tool
def tool_open_website(url: str) -> str:
    """Open any website in the browser. Use when user wants to open or visit a website."""
    return open_website(url)


@tool
def tool_add_reminder(message: str, time_str: str) -> str:
    """Add a reminder at a specific time (HH:MM format). Use when user wants to set a reminder at a specific time."""
    return add_reminder(message, time_str)


@tool
def tool_add_reminder_minutes(message: str, minutes: int) -> str:
    """Add a reminder after a number of minutes from now. Use this when the user says remind me later, remind me in 10 minutes, after some time, or set reminder after X minutes."""

    return add_reminder_in_minutes(message, minutes)


@tool
def tool_list_reminders() -> str:
    """List all active reminders. Use when user wants to see their reminders."""
    return list_reminders()


@tool
def tool_clear_reminders() -> str:
    """Clear all reminders. Use when user wants to delete or clear all reminders."""
    return clear_reminders()

@tool
def tool_get_clipboard() -> str:
    """Read the current text content of the Windows clipboard."""
    return format_tool_result(
        execute_tool_call("tool_get_clipboard", {}, get_clipboard)
    )

@tool
def tool_set_clipboard(text: str) -> str:
    """Copy text to the Windows clipboard so the user can paste it anywhere.
    Use this when the user asks to copy something or when a result should be placed in clipboard."""
    return format_tool_result(
        execute_tool_call("tool_set_clipboard", {"text": text}, lambda: set_clipboard(text))
    )

@tool
def tool_clear_clipboard() -> str:
    """Clear the Windows clipboard."""
    return format_tool_result(
        execute_tool_call("tool_clear_clipboard", {}, clear_clipboard)
    )

@tool
def tool_append_clipboard(text: str) -> str:
    """Append text to the existing clipboard content."""
    return format_tool_result(
        execute_tool_call("tool_append_clipboard", {"text": text}, lambda: append_to_clipboard(text))
    )

@tool
def tool_capture_and_describe() -> str:
    """Take a screenshot of the PC screen and describe everything visible on it using AI vision.
    Use this when user asks what is on screen, what is open, or to see the current screen."""
    return format_tool_result(
        execute_tool_call("tool_capture_and_describe", {}, capture_and_describe)
    )

@tool
def tool_capture_and_answer(question: str) -> str:
    """Take a screenshot and answer a specific question about what is visible on screen.
    Use this when user asks something specific about their screen like 'what error is showing'
    or 'what is written in that window'."""
    return format_tool_result(
        execute_tool_call(
            "tool_capture_and_answer",
            {"question": question},
            lambda: capture_and_answer(question),
        )
    )

@tool
def tool_save_screenshot(filename: str = "") -> str:
    """Take a screenshot and save it to the Desktop as a PNG file."""
    return format_tool_result(
        execute_tool_call(
            "tool_save_screenshot",
            {"filename": filename},
            lambda: save_screenshot(filename or None),
        )
    )

@tool
def tool_list_windows() -> str:
    """List all currently open windows on the PC."""
    return format_tool_result(
        execute_tool_call("tool_list_windows", {}, list_windows)
    )

@tool
def tool_minimize_window(title_keyword: str) -> str:
    """Minimize a window by searching its title. Example: 'notepad', 'chrome', 'youtube'."""
    return format_tool_result(
        execute_tool_call("tool_minimize_window", {"title_keyword": title_keyword},
                          lambda: minimize_window(title_keyword))
    )

@tool
def tool_maximize_window(title_keyword: str) -> str:
    """Maximize a window by searching its title."""
    return format_tool_result(
        execute_tool_call("tool_maximize_window", {"title_keyword": title_keyword},
                          lambda: maximize_window(title_keyword))
    )

@tool
def tool_restore_window(title_keyword: str) -> str:
    """Restore a minimized or maximized window to its normal size."""
    return format_tool_result(
        execute_tool_call("tool_restore_window", {"title_keyword": title_keyword},
                          lambda: restore_window(title_keyword))
    )

@tool
def tool_close_window(title_keyword: str) -> str:
    """Close a window by searching its title. Use carefully."""
    return format_tool_result(
        execute_tool_call("tool_close_window", {"title_keyword": title_keyword},
                          lambda: close_window(title_keyword))
    )

@tool
def tool_focus_window(title_keyword: str) -> str:
    """Bring a window to the front and give it focus."""
    return format_tool_result(
        execute_tool_call("tool_focus_window", {"title_keyword": title_keyword},
                          lambda: focus_window(title_keyword))
    )

@tool
def tool_minimize_all_windows() -> str:
    """Minimize all windows and show the desktop. Same as pressing Win+D."""
    return format_tool_result(
        execute_tool_call("tool_minimize_all_windows", {}, minimize_all_windows)
    )

@tool
def tool_lock_screen() -> str:
    """Lock the Windows PC screen immediately.
    Use when user says lock screen, lock pc, lock computer, or lock my pc."""
    return format_tool_result(
        execute_tool_call("tool_lock_screen", {}, lock_screen)
    )

@tool
def tool_sleep_pc() -> str:
    """Put the Windows PC to sleep.
    Use when user says sleep, put pc to sleep, or sleep mode."""
    return format_tool_result(
        execute_tool_call("tool_sleep_pc", {}, sleep_pc)
    )


@tool
def tool_take_photo() -> str:
    """Open the camera app and take a photo. Photo is saved to Pictures/Camera Roll."""
    return format_tool_result(
        execute_tool_call("tool_take_photo", {}, take_photo_with_camera)
    )

@tool
def tool_send_whatsapp(contact: str, message: str) -> str:
    """Send a WhatsApp message to a contact or group via the WhatsApp desktop app.
    Use when user says send message on whatsapp, whatsapp [name], message [name] on whatsapp."""
    return format_tool_result(
        execute_tool_call(
            "tool_send_whatsapp",
            {"contact": contact, "message": message},
            lambda: send_whatsapp_message(contact, message),
        )
    )

@tool
def tool_open_whatsapp_chat(contact: str) -> str:
    """Open a WhatsApp chat with a specific contact or group.
    Use when user says open whatsapp chat with [name] or go to [name] on whatsapp."""
    return format_tool_result(
        execute_tool_call(
            "tool_open_whatsapp_chat",
            {"contact": contact},
            lambda: open_whatsapp_chat(contact),
        )
    )

@tool
def tool_add_whatsapp_contact(name: str, phone: str) -> str:
    """Save a WhatsApp contact with their phone number including country code.
    Use when user says add whatsapp contact or save number for whatsapp.
    Example: name='Satya', phone='+919876543210'"""
    return format_tool_result(
        execute_tool_call(
            "tool_add_whatsapp_contact",
            {"name": name, "phone": phone},
            lambda: add_whatsapp_contact(name, phone),
        )
    )

@tool
def tool_list_whatsapp_contacts() -> str:
    """List all saved WhatsApp contacts."""
    return format_tool_result(
        execute_tool_call("tool_list_whatsapp_contacts", {}, list_whatsapp_contacts)
    )

@tool
def tool_remove_whatsapp_contact(name: str) -> str:
    """Remove a contact from the WhatsApp contact book."""
    return format_tool_result(
        execute_tool_call(
            "tool_remove_whatsapp_contact",
            {"name": name},
            lambda: remove_whatsapp_contact(name),
        )
    )

@tool
def tool_send_whatsapp_image(contact: str, image_path: str) -> str:
    """Send an image file to a WhatsApp contact.
    Use when user says send image/photo/picture to [name] on whatsapp.
    image_path: full path to the image OR just filename if on Desktop."""
    return format_tool_result(
        execute_tool_call(
            "tool_send_whatsapp_image",
            {"contact": contact, "image_path": image_path},
            lambda: send_whatsapp_image(contact, image_path),
        )
    )

@tool
def tool_record_voice_note(duration_seconds: int = 5) -> str:
    """Record a voice note from the microphone and save it to Desktop.
    Use when user says record voice note or record audio.
    duration_seconds: how long to record in seconds."""
    return format_tool_result(
        execute_tool_call(
            "tool_record_voice_note",
            {"duration_seconds": duration_seconds},
            lambda: record_voice_note(duration_seconds),
        )
    )

@tool
def tool_send_whatsapp_voice(contact: str, duration_seconds: int = 5) -> str:
    """Record a voice note and send it to a WhatsApp contact.
    Use when user says send voice note to [name] on whatsapp.
    duration_seconds: how many seconds to record."""
    return format_tool_result(
        execute_tool_call(
            "tool_send_whatsapp_voice",
            {"contact": contact, "duration_seconds": duration_seconds},
            lambda: send_whatsapp_voice(contact, duration_seconds),
        )
    )

@tool
def tool_stop_speaking() -> str:
    """Stop the agent from speaking immediately."""
    stop_speaking()
    return "Stopped speaking."

@tool
def tool_set_voice_speed(speed: str = "normal") -> str:
    """Set the agent's speaking speed. Options: slow, normal, fast."""
    rates = {"slow": 120, "normal": 160, "fast": 200}
    rate = rates.get(speed.lower(), 160)
    set_voice_rate(rate)
    return f"Voice speed set to {speed}."

@tool
def tool_set_voice_volume(level: int = 95) -> str:
    """Set agent voice volume. 0 to 100."""
    set_voice_volume(level / 100)
    return f"Voice volume set to {level}%."


@tool
def tool_get_learning_summary() -> str:
    """Show what the agent has learned about the user so far.
    Use when user asks what have you learned, what do you know about me, or show your learning."""
    return get_learning_summary()

@tool
def tool_clear_lessons() -> str:
    """Clear all learned lessons and start fresh.
    Use when user says forget everything, clear your memory, or start fresh."""
    clear_all_lessons()
    return "All lessons cleared. Starting fresh."

@tool
def tool_remember_this(lesson: str) -> str:
    """Explicitly remember something the user tells you.
    Use when user says remember this, always do this, or never do that."""
    add_lesson(lesson, "teaching", trigger=lesson)
    return f"Got it, I'll remember: {lesson}"


@tool
def tool_check_available_apps(task: str) -> str:
    """Check which apps are available for a specific task.
    Use this when user wants to send a message, email, play music, 
    open a browser, make a video call, or any task that multiple apps can handle.
    Returns available options so you can ask the user which one to use."""
    result = get_options_for_task(task)
    if not result:
        return "Only one option available — proceed directly."
    return result["question"]

@tool  
def tool_list_available_apps() -> str:
    """List all apps available on the PC organized by category.
    Use when user asks what apps are available or what can you use."""
    return get_all_available_apps_summary()




@tool
def tool_send_email(to: str, subject: str, body: str, cc: str = "", attachment_path: str = "") -> str:
    """Send an email. Use when user says send email, email to, mail to someone.
    to: recipient email address
    subject: email subject
    body: email content
    cc: optional CC address
    attachment_path: optional file path to attach"""
    return format_tool_result(
        execute_tool_call("tool_send_email",
            {"to": to, "subject": subject},
            lambda: send_email(to, subject, body, cc, attachment_path))
    )

@tool
def tool_get_inbox(limit: int = 10, unread_only: bool = False) -> str:
    """Read emails from inbox. Use when user says check email, read inbox, show emails.
    limit: how many emails to show
    unread_only: True to show only unread emails"""
    return format_tool_result(
        execute_tool_call("tool_get_inbox",
            {"limit": limit, "unread_only": unread_only},
            lambda: get_inbox(limit, unread_only))
    )

@tool
def tool_read_email(email_number: str) -> str:
    """Read a specific email by its number from the inbox list.
    Use when user says read email number X or open this email."""
    return format_tool_result(
        execute_tool_call("tool_read_email",
            {"email_number": email_number},
            lambda: read_email(email_number))
    )

@tool
def tool_reply_email(to: str, subject: str, body: str, original_message_id: str = "") -> str:
    """Reply to an email. Use when user says reply to this email."""
    return format_tool_result(
        execute_tool_call("tool_reply_email",
            {"to": to, "subject": subject},
            lambda: reply_to_email(original_message_id, to, subject, body))
    )

@tool
def tool_forward_email(to: str, original_subject: str, original_body: str, note: str = "") -> str:
    """Forward an email to another person."""
    return format_tool_result(
        execute_tool_call("tool_forward_email",
            {"to": to},
            lambda: forward_email(to, original_subject, original_body, note))
    )

@tool
def tool_delete_email(email_number: str) -> str:
    """Delete an email by its number. Ask for confirmation first."""
    return format_tool_result(
        execute_tool_call("tool_delete_email",
            {"email_number": email_number},
            lambda: delete_email(email_number))
    )

@tool
def tool_search_emails(query: str, limit: int = 10) -> str:
    """Search emails by subject or sender name/address."""
    return format_tool_result(
        execute_tool_call("tool_search_emails",
            {"query": query},
            lambda: search_emails(query, limit))
    )

@tool
def tool_get_unread_count() -> str:
    """Get count of unread emails. Use when user asks how many unread emails."""
    return format_tool_result(
        execute_tool_call("tool_get_unread_count", {},
            get_unread_count)
    )

@tool
def tool_mark_email_read(email_number: str) -> str:
    """Mark an email as read."""
    return format_tool_result(
        execute_tool_call("tool_mark_email_read",
            {"email_number": email_number},
            lambda: mark_email_read(email_number))
    )

@tool
def tool_mark_email_unread(email_number: str) -> str:
    """Mark an email as unread."""
    return format_tool_result(
        execute_tool_call("tool_mark_email_unread",
            {"email_number": email_number},
            lambda: mark_email_unread(email_number))
    )

@tool
def tool_email_status() -> str:
    """Check if email is configured and working.
    Use when user asks about email setup or if email is connected."""
    return format_tool_result(
        execute_tool_call("tool_email_status", {},
            get_email_config_status)
    )



@tool
def tool_notepad_open() -> str:
    """Open Notepad application."""
    return format_tool_result(execute_tool_call("tool_notepad_open", {}, open_notepad))

@tool
def tool_notepad_new_tab() -> str:
    """Create a new tab in Notepad."""
    return format_tool_result(execute_tool_call("tool_notepad_new_tab", {}, new_tab))

@tool
def tool_notepad_write(text: str, clear_first: bool = False) -> str:
    """Write text into Notepad. Set clear_first=True to replace existing content.
    Use when user says write this, type this, put this text in notepad."""
    return format_tool_result(execute_tool_call("tool_notepad_write",
        {"text": text, "clear_first": clear_first},
        lambda: write_text(text, clear_first)))

@tool
def tool_notepad_append(text: str) -> str:
    """Append text at the end of current Notepad content."""
    return format_tool_result(execute_tool_call("tool_notepad_append",
        {"text": text}, lambda: append_text(text)))

@tool
def tool_notepad_clear() -> str:
    """Clear all text in the current Notepad tab."""
    return format_tool_result(execute_tool_call("tool_notepad_clear", {}, clear_notepad))

@tool
def tool_notepad_save(filename: str = "") -> str:
    """Save the current Notepad file. Provide filename for new files."""
    return format_tool_result(execute_tool_call("tool_notepad_save",
        {"filename": filename}, lambda: save_file(filename)))

@tool
def tool_notepad_save_as(filename: str) -> str:
    """Save Notepad content as a new file with the given name."""
    return format_tool_result(execute_tool_call("tool_notepad_save_as",
        {"filename": filename}, lambda: save_as(filename)))

@tool
def tool_notepad_open_file(filepath: str) -> str:
    """Open a specific file in Notepad."""
    return format_tool_result(execute_tool_call("tool_notepad_open_file",
        {"filepath": filepath}, lambda: open_file_in_notepad(filepath)))

@tool
def tool_notepad_find(search_term: str) -> str:
    """Find text in Notepad."""
    return format_tool_result(execute_tool_call("tool_notepad_find",
        {"search_term": search_term}, lambda: find_text(search_term)))

@tool
def tool_notepad_replace(find_term: str, replace_term: str, replace_all: bool = True) -> str:
    """Find and replace text in Notepad."""
    return format_tool_result(execute_tool_call("tool_notepad_replace",
        {"find": find_term, "replace": replace_term},
        lambda: find_and_replace(find_term, replace_term, replace_all)))

@tool
def tool_notepad_copy_all() -> str:
    """Copy all text from Notepad to clipboard."""
    return format_tool_result(execute_tool_call("tool_notepad_copy_all", {}, copy_all_text))

@tool
def tool_notepad_undo() -> str:
    """Undo last action in Notepad."""
    return format_tool_result(execute_tool_call("tool_notepad_undo", {}, undo))

@tool
def tool_notepad_redo() -> str:
    """Redo last undone action in Notepad."""
    return format_tool_result(execute_tool_call("tool_notepad_redo", {}, redo))

@tool
def tool_notepad_goto_line(line_number: int) -> str:
    """Go to a specific line number in Notepad."""
    return format_tool_result(execute_tool_call("tool_notepad_goto_line",
        {"line": line_number}, lambda: go_to_line(line_number)))

@tool
def tool_notepad_insert_datetime() -> str:
    """Insert current date and time at cursor in Notepad."""
    return format_tool_result(execute_tool_call("tool_notepad_insert_datetime", {}, insert_datetime))

@tool
def tool_notepad_close_tab() -> str:
    """Close the current Notepad tab."""
    return format_tool_result(execute_tool_call("tool_notepad_close_tab", {}, close_notepad_tab))

@tool
def tool_notepad_zoom_in() -> str:
    """Zoom in text in Notepad."""
    return format_tool_result(execute_tool_call("tool_notepad_zoom_in", {}, zoom_in))

@tool
def tool_notepad_zoom_out() -> str:
    """Zoom out text in Notepad."""
    return format_tool_result(execute_tool_call("tool_notepad_zoom_out", {}, zoom_out))

@tool
def tool_notepad_status() -> str:
    """Check if Notepad is open."""
    return format_tool_result(execute_tool_call("tool_notepad_status", {}, get_notepad_status))

ALL_TOOLS = [
    tool_create_folder, tool_create_file, tool_read_file,
    tool_list_files, tool_search_files, tool_delete_file,
    tool_cpu_info, tool_ram_info, tool_disk_info,
    tool_battery_info, tool_system_summary, tool_running_processes,
    tool_network_info, tool_kill_process,
    tool_open_app, tool_screenshot, tool_open_folder,tool_lock_screen,tool_sleep_pc,
    tool_open_windows, tool_shutdown, tool_restart, tool_cancel_shutdown,
    tool_write_code, tool_run_code, tool_write_and_run, tool_install_package,
    tool_search_web, tool_get_weather, tool_get_news,
    tool_calculate, tool_current_time,
    tool_search_google, tool_search_youtube, tool_open_website,
    tool_add_reminder, tool_add_reminder_minutes,tool_list_reminders, tool_clear_reminders,
    tool_get_clipboard,tool_set_clipboard,tool_clear_clipboard,tool_append_clipboard,
    tool_capture_and_describe,tool_capture_and_answer,tool_save_screenshot,
    tool_list_windows,tool_minimize_window,tool_maximize_window,tool_restore_window,tool_close_window,tool_focus_window,tool_minimize_all_windows,
    tool_take_photo,
    tool_send_whatsapp,tool_open_whatsapp_chat,tool_add_whatsapp_contact,tool_list_whatsapp_contacts,tool_remove_whatsapp_contact,tool_send_whatsapp_image,tool_record_voice_note,tool_send_whatsapp_voice,
    tool_stop_speaking,tool_set_voice_speed,tool_set_voice_volume,
    tool_get_learning_summary,tool_clear_lessons,tool_remember_this,
    tool_check_available_apps,tool_list_available_apps,
    tool_send_email,tool_get_inbox,tool_read_email,tool_reply_email,tool_forward_email,tool_delete_email,tool_search_emails,tool_get_unread_count,tool_mark_email_read,tool_mark_email_unread,tool_email_status,
    tool_notepad_open,tool_notepad_new_tab,tool_notepad_write,tool_notepad_append,tool_notepad_clear,tool_notepad_save,tool_notepad_save_as,tool_notepad_open_file,tool_notepad_find,
    tool_notepad_replace,tool_notepad_copy_all,tool_notepad_undo,tool_notepad_redo,tool_notepad_goto_line,tool_notepad_insert_datetime,tool_notepad_close_tab,tool_notepad_zoom_in,
    tool_notepad_zoom_out,tool_notepad_status,
]


TOOL_MAP = {tool_item.name: tool_item for tool_item in ALL_TOOLS}


class AgentState(TypedDict):
    messages: List
    user_input: str
    response: str
    context: str
    agent_name: str
    session_id: str



def load_memory_node(state: AgentState) -> AgentState:
    state["context"] = get_relevant_context(state["user_input"])
    if len(state["context"]) > 500:
        state["context"] = ""
    return state


def build_messages(state: AgentState) -> list:
    from tools.learning_system import get_learning_context
    _base_prompt = get_system_prompt(state["agent_name"])
    _pc_context = format_profile_for_prompt(get_or_build_profile())
    _learning_context = get_learning_context()
    _full_prompt = _base_prompt
    if _pc_context:
        _full_prompt += "\n\n" + _pc_context
    if _learning_context:
        _full_prompt += "\n\n" + _learning_context
    messages = [SystemMessage(content=_full_prompt)]

    if state.get("context"):
        messages.append(SystemMessage(content=state["context"]))

    messages.extend(state.get("messages", []))
    messages.append(HumanMessage(content=state["user_input"]))
    return messages


def invoke_without_tools(state: AgentState, reason: str = "") -> str:
    """Fallback to plain chat when tool calling is unavailable or fails."""
    tried_providers = set()
    last_error = None

    while True:
        try:
            llm, provider_name = get_llm(need_tools=False, exclude=tried_providers)
        except Exception:
            break

        messages = build_messages(state)

        if reason:
            messages.append(SystemMessage(
                content=(
                    "Tool execution is temporarily unavailable. "
                    "Respond helpfully without using tools. "
                    f"Internal note: {reason[:200]}"
                )
            ))

        try:
            response = llm.invoke(messages)
            mark_provider_healthy(provider_name)
            return response if isinstance(response, str) else response.content
        except Exception as exc:
            mark_provider_failed(provider_name, exc)
            tried_providers.add(provider_name)
            last_error = exc

    if last_error is not None:
        return (
            "I hit a temporary AI provider problem. "
            "Please try again in a moment, or configure a backup provider like OpenRouter or Ollama."
        )

    return "No plain-chat provider is available right now."


def build_confirmation_message(tool_name: str, tool_args: dict) -> str:
    if tool_name == "tool_delete_file":
        target = tool_args.get("filepath", "the target file or folder")
        return f"Please confirm: do you want me to delete '{target}'?"

    if tool_name == "tool_shutdown":
        delay = tool_args.get("delay_seconds", 30)
        return f"Please confirm: do you want me to shut down the PC in {delay} seconds?"

    if tool_name == "tool_restart":
        delay = tool_args.get("delay_seconds", 30)
        return f"Please confirm: do you want me to restart the PC in {delay} seconds?"

    if tool_name == "tool_kill_process":
        process_name = tool_args.get("process_name", "the selected process")
        return f"Please confirm: do you want me to stop the process '{process_name}'?"

    if tool_name == "tool_install_package":
        package_name = tool_args.get("package_name", "the requested package")
        return f"Please confirm: do you want me to install the Python package '{package_name}'?"

    return "Please confirm this action. Reply with yes to continue or cancel to stop."


def log_tool_execution(
    session_id: str,
    tool_name: str,
    tool_args: dict,
    result: str,
    success: bool,
) -> None:
    try:
        log_line = (
            f"[session={session_id}] "
            f"[tool={tool_name}] "
            f"[success={success}] "
            f"[args={tool_args}] "
            f"[result={result}]"
        )

        ensure_runtime_dirs()
        with TOOL_ACTIVITY_LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(log_line + "\n")
    except Exception as exc:
        print(f"Tool logging error: {exc}")


def execute_logged_tool(tool_name, tool_args, invoker, session_id, task_id=None):
    tool_result = execute_tool_call(
        tool_name=tool_name,
        tool_args=tool_args,
        invoker=invoker,
    )
    success = tool_succeeded(tool_result)
    
    log_tool_execution(
        session_id=session_id,
        tool_name=tool_name,
        tool_args=tool_args,
        result=str(tool_result),
        success=success,
    )
    
    # NEW: also save a TaskStep if we have a task_id
    if task_id is not None:
        create_task_step(
            task_id=task_id,
            session_id=session_id,
            step_index=0,  # increment this properly later
            tool_name=tool_name,
            tool_args=tool_args,
            output_text=format_tool_result(tool_result),
            success=success,
        )
    
    return tool_result


def extract_known_app_name(user_input: str) -> str | None:
    text = user_input.lower()
    for app_name in sorted(APPS.keys(), key=len, reverse=True):
        if app_name in text:
            return app_name
    return None


def extract_folder_name(user_input: str) -> str | None:
    match = re.search(
        r"(?:folder|floder|directory)(?:\s+(?:named|called|name))?\s+['\"]?([^'\"]+?)['\"]?$",
        user_input.strip(),
        re.IGNORECASE,
    )
    if not match:
        return None
    folder_name = match.group(1).strip().rstrip(".")
    return folder_name or None


def extract_windows_path(user_input: str) -> str | None:
    match = re.search(r"[A-Za-z]:\\[^\"']+", user_input)
    if match:
        return match.group(0).strip()
    return None


def extract_folder_target(user_input: str) -> str | None:
    raw_text = user_input.strip()
    lowered = raw_text.lower()

    windows_path = extract_windows_path(raw_text)
    if windows_path:
        return windows_path

    quoted = re.search(r"['\"]([^'\"]+)['\"]", raw_text)
    if quoted:
        return quoted.group(1).strip()

    for folder_name in sorted(COMMON_FOLDERS.keys(), key=len, reverse=True):
        if re.search(rf"\b{re.escape(folder_name)}\b", lowered):
            return folder_name

    match = re.search(
        r"(?:open|go to|browse|show)(?:\s+the)?(?:\s+(?:folder|directory))?\s+(.+)$",
        raw_text,
        re.IGNORECASE,
    )
    if match:
        candidate = match.group(1).strip().rstrip(".")
        candidate = re.sub(r"\b(for me|please)\b", "", candidate, flags=re.IGNORECASE).strip()
        if candidate:
            return candidate

    return extract_folder_name(raw_text)


def extract_filename(user_input: str) -> str | None:
    match = re.search(
        r"(?:file|filename)(?:\s+(?:named|called|name))?\s+['\"]?([^'\"]+?)['\"]?$",
        user_input.strip(),
        re.IGNORECASE,
    )
    if not match:
        return None
    filename = match.group(1).strip().rstrip(".")
    return filename or None


def extract_search_query(user_input: str, prefix: str) -> str | None:
    text = user_input.strip()
    lowered = text.lower()
    index = lowered.find(prefix)
    if index == -1:
        return None
    query = text[index + len(prefix):].strip(" :.-")
    return query or None


def extract_reminder_minutes(user_input: str) -> tuple[str, int] | None:
    match = re.search(
        r"remind me(?:\s+to\s+|\s+about\s+|\s+)(.+?)\s+(?:in|after)\s+(\d+)\s*(minute|minutes|min)\b",
        user_input.strip(),
        re.IGNORECASE,
    )
    if not match:
        return None
    message = match.group(1).strip().rstrip(".")
    minutes = int(match.group(2))
    return message, minutes


def detect_list_path(user_input: str) -> str:
    text = user_input.lower()
    if "downloads" in text:
        return os.path.join(os.path.expanduser("~"), "Downloads")
    if "documents" in text:
        return os.path.join(os.path.expanduser("~"), "Documents")
    return os.path.join(os.path.expanduser("~"), "OneDrive", "Desktop")


def get_session_context(session_id: str) -> dict:
    return SESSION_CONTEXTS.setdefault(
        session_id,
        {
            "last_folder_path": None,
            "last_folder_name": None,
            "last_file_path": None,
        },
    )


def update_session_context_from_tool_result(tool_result, session_context: dict) -> None:
    if not isinstance(tool_result, dict):
        return

    if not tool_result.get("success", False):
        return

    action = tool_result.get("action", "")
    data = tool_result.get("data", {}) or {}

    if action in {"create_folder", "open_folder"}:
        folder_path = data.get("path")
        if folder_path:
            session_context["last_folder_path"] = folder_path
            session_context["last_folder_name"] = os.path.basename(folder_path.rstrip("\\/"))

    if action in {"create_file", "read_file"}:
        file_path = data.get("path") or data.get("filepath")
        if file_path:
            session_context["last_file_path"] = file_path

    if action in {"write_code", "write_and_run_code"}:
        file_path = data.get("path")
        if file_path:
            session_context["last_file_path"] = file_path
            folder_path = os.path.dirname(file_path)
            session_context["last_folder_path"] = folder_path
            session_context["last_folder_name"] = os.path.basename(folder_path.rstrip("\\/"))


def resolve_contextual_step(step: str, session_context: dict) -> str:
    resolved = step.strip()
    last_folder_path = session_context.get("last_folder_path")
    if not last_folder_path:
        return resolved

    lowered = resolved.lower()
    if any(phrase in lowered for phrase in ["open it", "open that folder", "open that directory"]):
        return f"open folder {last_folder_path}"
    if any(phrase in lowered for phrase in ["go there", "go to it", "go to that folder", "browse it"]):
        return f"open folder {last_folder_path}"

    last_file_path = session_context.get("last_file_path")
    if last_file_path and any(phrase in lowered for phrase in ["run it", "run that file", "execute it"]):
        return f"run file {last_file_path}"
    if last_file_path and any(phrase in lowered for phrase in ["read it", "open that file", "show it"]):
        return f"read file {last_file_path}"

    return resolved


def build_contextual_path(name: str, session_context: dict, default_extension: str | None = None) -> str:
    cleaned = name.strip().strip('"').strip("'")
    if default_extension and "." not in os.path.basename(cleaned):
        cleaned += default_extension

    if os.path.isabs(cleaned):
        return cleaned

    last_folder_path = session_context.get("last_folder_path")
    if last_folder_path:
        return os.path.join(last_folder_path, cleaned)

    return cleaned


def extract_code_filename(user_input: str) -> str | None:
    explicit_file = re.search(r"([A-Za-z0-9_\-]+\.py)\b", user_input)
    if explicit_file:
        return explicit_file.group(1)

    named_match = re.search(
        r"(?:file|script)(?:\s+(?:named|called|name))?\s+['\"]?([^'\"\s]+)['\"]?",
        user_input,
        re.IGNORECASE,
    )
    if named_match:
        filename = named_match.group(1).strip().rstrip(".")
        if filename:
            return filename if filename.endswith(".py") else f"{filename}.py"

    return None


def infer_python_code(user_input: str) -> str | None:
    lowered = user_input.lower()

    if "hello world" in lowered:
        return 'print("Hello, world!")\n'

    if "fibonacci" in lowered:
        return (
            "def fibonacci(n):\n"
            "    sequence = [0, 1]\n"
            "    while len(sequence) < n:\n"
            "        sequence.append(sequence[-1] + sequence[-2])\n"
            "    return sequence[:n]\n\n"
            'print(fibonacci(10))\n'
        )

    if "current time" in lowered:
        return (
            "from datetime import datetime\n\n"
            'print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))\n'
        )

    if "prime" in lowered:
        return (
            "def is_prime(number):\n"
            "    if number < 2:\n"
            "        return False\n"
            "    for candidate in range(2, int(number ** 0.5) + 1):\n"
            "        if number % candidate == 0:\n"
            "            return False\n"
            "    return True\n\n"
            "for value in range(2, 30):\n"
            "    if is_prime(value):\n"
            "        print(value)\n"
        )

    return None


def split_task_steps(user_input: str) -> list[str]:
    split_pattern = (
        r"\s+(?:and then|then|after that|afterwards|and)\s+"
        r"(?=(?:open|launch|start|run|create|make|read|search|find|show|check|list|write|install|set|remind|go|browse|locate)\b)"
    )
    parts = re.split(split_pattern, user_input.strip(), flags=re.IGNORECASE)
    return [part.strip(" ,.") for part in parts if part.strip(" ,.")]


def execute_single_step_with_agent(step: str, session_id: str, agent_name: str) -> str | None:
    state: AgentState = {
        "messages": [],
        "user_input": normalize_user_input(step),
        "response": "",
        "context": get_relevant_context(step),
        "agent_name": agent_name,
        "session_id": session_id,
    }

    action_type = route_obvious_task(state["user_input"]) or plan_action(state["user_input"])
    if action_type == "multi_step":
        state["user_input"] = expand_multi_step_request(state["user_input"])
        action_type = "tool"

    if action_type == "clarify":
        return ""

    if action_type == "chat":
        return invoke_without_tools(state)

    try:
        return invoke_with_tools(state, session_id=session_id)
    except Exception as exc:
        return invoke_without_tools(state, reason=f"step execution fallback: {exc}")


def execute_multi_step_task(
    user_input: str,
    session_id: str,
    agent_name: str | None = None,
) -> str | None:
    steps = split_task_steps(user_input)
    if len(steps) < 2:
        return None

    active_agent_name = agent_name or AGENT_NAME

    session_context = get_session_context(session_id)
    results = []
    executed_any = False

    for index, step in enumerate(steps, start=1):
        resolved_step = resolve_contextual_step(step, session_context)
        step_result = run_direct_action(
            resolved_step,
            session_id,
            session_context=session_context,
        )

        if step_result is None:
            step_result = execute_single_step_with_agent(
                resolved_step,
                session_id=session_id,
                agent_name=active_agent_name,
            )

        if step_result is None:
            if executed_any:
                results.append(f"Step {index}: I could not complete this step: {resolved_step}")
                break
            return None

        executed_any = True
        results.append(f"Step {index}: {step_result}")

    return "\n\n".join(results) if executed_any else None


def persist_exchange(user_input: str, response: str, agent_name: str) -> None:
    save_memory(user_input, "user")
    save_memory(response, "assistant")

    if agent_name != DEFAULT_NAME:
        save_memory(f"My name is {agent_name}", "system")


def run_direct_action(user_input: str, session_id: str, session_context: dict | None = None) -> str | None:
    """
    Bypass LLM routing for very obvious local actions so common commands
    behave like a real PC assistant.
    """
    text = user_input.lower().strip()
    session_context = session_context or get_session_context(session_id)

    if any(phrase in text for phrase in [
        "open folder", "open directory", "go to folder", "go to directory",
        "browse folder", "show folder", "open downloads", "open documents",
        "open desktop", "open pictures", "open videos", "open music",
        "go to downloads", "go to documents", "go to desktop",
    ]):
        folder_target = extract_folder_target(user_input)
        if folder_target:
            result = execute_logged_tool(
                tool_name="tool_open_folder",
                tool_args={"folder_path": folder_target},
                invoker=lambda: open_folder(folder_target),
                session_id=session_id,
            )
            if resolved := resolve_existing_folder_path(folder_target):
                session_context["last_folder_path"] = resolved
                session_context["last_folder_name"] = os.path.basename(resolved.rstrip("\\/"))
            update_session_context_from_tool_result(result, session_context)
            return format_tool_result(result)

    if any(word in text for word in ["open", "launch", "start", "run"]):
        app_name = extract_known_app_name(user_input)
        if app_name:
            result = execute_logged_tool(
                tool_name="tool_open_app",
                tool_args={"app_name": app_name},
                invoker=lambda: open_application(app_name),
                session_id=session_id,
            )
            return format_tool_result(result)

    if "ram" in text and "program" not in text:
        result = get_ram_info()
        log_tool_execution(
            session_id=session_id,
            tool_name="tool_ram_info",
            tool_args={},
            result=str(result),
            success=True,
        )
        return result

    if "cpu" in text and "ram" in text:
        result = f"{get_cpu_info()}\n\n{get_ram_info()}"
        log_tool_execution(
            session_id=session_id,
            tool_name="tool_system_summary_partial",
            tool_args={"fields": ["cpu", "ram"]},
            result=result,
            success=True,
        )
        return result

    if any(phrase in text for phrase in ["what running", "running now", "running on my pc", "processes"]):
        result = get_running_processes()
        log_tool_execution(
            session_id=session_id,
            tool_name="tool_running_processes",
            tool_args={},
            result=result,
            success=True,
        )
        return result

    if any(phrase in text for phrase in ["system summary", "system status", "pc status", "laptop status"]):
        result = get_system_summary()
        log_tool_execution(
            session_id=session_id,
            tool_name="tool_system_summary",
            tool_args={},
            result=str(result),
            success=tool_succeeded(result),
        )
        return format_tool_result(result)

    if any(phrase in text for phrase in ["disk info", "disk usage", "storage", "hard drive"]):
        result = get_disk_info()
        log_tool_execution(
            session_id=session_id,
            tool_name="tool_disk_info",
            tool_args={},
            result=result,
            success=True,
        )
        return result

    if "battery" in text:
        result = get_battery_info()
        log_tool_execution(
            session_id=session_id,
            tool_name="tool_battery_info",
            tool_args={},
            result=result,
            success=True,
        )
        return result

    if any(phrase in text for phrase in ["network info", "internet status", "ip address", "network status"]):
        result = get_network_info()
        log_tool_execution(
            session_id=session_id,
            tool_name="tool_network_info",
            tool_args={},
            result=result,
            success=True,
        )
        return result

    if any(phrase in text for phrase in ["create folder", "make folder", "make one folder", "create a folder"]):
        folder_name = extract_folder_name(user_input)
        if folder_name:
            result = execute_logged_tool(
                tool_name="tool_create_folder",
                tool_args={"folder_name": folder_name},
                invoker=lambda: create_folder(folder_name),
                session_id=session_id,
            )
            update_session_context_from_tool_result(result, session_context)
            return format_tool_result(result)

    if any(phrase in text for phrase in ["create file", "make file", "new file"]):
        filename = extract_filename(user_input)
        if filename:
            target_path = build_contextual_path(filename, session_context)
            result = execute_logged_tool(
                tool_name="tool_create_file",
                tool_args={"filename": target_path},
                invoker=lambda: create_file(target_path),
                session_id=session_id,
            )
            update_session_context_from_tool_result(result, session_context)
            return format_tool_result(result)

    if any(phrase in text for phrase in ["read file", "open file", "show file", "read the file"]):
        filename = extract_filename(user_input)
        if filename:
            target_path = build_contextual_path(filename, session_context)
            result = execute_logged_tool(
                tool_name="tool_read_file",
                tool_args={"filepath": target_path},
                invoker=lambda: read_file(target_path),
                session_id=session_id,
            )
            update_session_context_from_tool_result(result, session_context)
            return format_tool_result(result)

    if any(phrase in text for phrase in ["list files", "show files", "show desktop files", "list desktop files"]):
        list_path = detect_list_path(user_input)
        result = list_files(list_path)
        log_tool_execution(
            session_id=session_id,
            tool_name="tool_list_files",
            tool_args={"path": list_path},
            result=result,
            success=True,
        )
        return result

    if any(phrase in text for phrase in ["find file", "search file", "locate file"]):
        filename = extract_filename(user_input)
        if filename:
            search_root = session_context.get("last_folder_path") or os.path.join(os.path.expanduser("~"), "OneDrive", "Desktop")
            result = search_files(search_root, filename)
            log_tool_execution(
                session_id=session_id,
                tool_name="tool_search_files",
                tool_args={"keyword": filename, "root": search_root},
                result=result,
                success=True,
            )
            return result

    if any(phrase in text for phrase in ["run file", "execute file", "run script"]):
        file_target = extract_code_filename(user_input) or session_context.get("last_file_path")
        if file_target:
            target_path = build_contextual_path(file_target, session_context, ".py")
            result = execute_logged_tool(
                tool_name="tool_run_file",
                tool_args={"path": target_path},
                invoker=lambda: run_file(target_path),
                session_id=session_id,
            )
            session_context["last_file_path"] = target_path
            return format_tool_result(result)

    if any(phrase in text for phrase in ["write python", "create python", "make python"]):
        code = infer_python_code(user_input)
        if code:
            filename = extract_code_filename(user_input)
            target_path = build_contextual_path(filename or "", session_context, ".py")
            target_folder = os.path.dirname(target_path) if os.path.dirname(target_path) else None
            target_filename = os.path.basename(target_path) if target_path else filename
            should_run = any(phrase in text for phrase in ["run it", "and run", "run this", "execute it"])
            if should_run:
                result = execute_logged_tool(
                    tool_name="tool_write_and_run",
                    tool_args={"filename": target_filename, "folder_path": target_folder or ""},
                    invoker=lambda: write_and_run_code(code, target_filename, target_folder),
                    session_id=session_id,
                )
            else:
                result = execute_logged_tool(
                    tool_name="tool_write_code",
                    tool_args={"filename": target_filename, "folder_path": target_folder or ""},
                    invoker=lambda: write_and_save_code(code, target_filename, target_folder),
                    session_id=session_id,
                )
            update_session_context_from_tool_result(result, session_context)
            return format_tool_result(result)

    if any(phrase in text for phrase in ["find folder", "search folder", "locate folder"]):
        folder_target = extract_folder_target(user_input)
        if folder_target:
            resolved = resolve_existing_folder_path(folder_target)
            result = execute_logged_tool(
                tool_name="tool_find_folder",
                tool_args={"folder_path": folder_target},
                invoker=lambda: (
                    f"Found folder: {resolved}"
                    if resolved
                    else f"Folder not found: {folder_target}"
                ),
                session_id=session_id,
            )
            if resolved:
                session_context["last_folder_path"] = resolved
                session_context["last_folder_name"] = os.path.basename(resolved.rstrip("\\/"))
            return format_tool_result(result)

    if any(phrase in text for phrase in ["search google", "google search", "google "]):
        query = (
            extract_search_query(user_input, "search google")
            or extract_search_query(user_input, "google search")
            or extract_search_query(user_input, "google")
        )
        if query:
            result = execute_logged_tool(
                tool_name="tool_search_google",
                tool_args={"query": query},
                invoker=lambda: search_google(query),
                session_id=session_id,
            )
            return format_tool_result(result)

    if "youtube" in text and "search" in text:
        query = extract_search_query(user_input, "search youtube") or extract_search_query(user_input, "youtube")
        if query:
            result = execute_logged_tool(
                tool_name="tool_search_youtube",
                tool_args={"query": query},
                invoker=lambda: search_youtube(query),
                session_id=session_id,
            )
            return format_tool_result(result)

    if any(phrase in text for phrase in ["search web", "search the web", "look up "]):
        query = (
            extract_search_query(user_input, "search the web")
            or extract_search_query(user_input, "search web")
            or extract_search_query(user_input, "look up")
        )
        if query:
            result = execute_logged_tool(
                tool_name="tool_search_web",
                tool_args={"query": query},
                invoker=lambda: search_web(query),
                session_id=session_id,
            )
            return format_tool_result(result)

    if text.startswith("open website ") or text.startswith("open site "):
        url = extract_search_query(user_input, "open website") or extract_search_query(user_input, "open site")
        if url:
            result = execute_logged_tool(
                tool_name="tool_open_website",
                tool_args={"url": url},
                invoker=lambda: open_website(url),
                session_id=session_id,
            )
            return format_tool_result(result)

    reminder = extract_reminder_minutes(user_input)
    if reminder:
        message, minutes = reminder
        result = add_reminder_in_minutes(message, minutes)
        log_tool_execution(
            session_id=session_id,
            tool_name="tool_add_reminder_minutes",
            tool_args={"message": message, "minutes": minutes},
            result=result,
            success=not result.lower().startswith("error"),
        )
        return result

    if any(phrase in text for phrase in ["list reminders", "show reminders", "my reminders"]):
        result = list_reminders()
        log_tool_execution(
            session_id=session_id,
            tool_name="tool_list_reminders",
            tool_args={},
            result=result,
            success=True,
        )
        return result

    if any(phrase in text for phrase in ["clear reminders", "delete reminders"]):
        result = clear_reminders()
        log_tool_execution(
            session_id=session_id,
            tool_name="tool_clear_reminders",
            tool_args={},
            result=result,
            success=True,
        )
        return result

    if any(phrase in text for phrase in ["what time", "current time", "what date", "today date"]):
        result = get_current_time()
        log_tool_execution(
            session_id=session_id,
            tool_name="tool_current_time",
            tool_args={},
            result=result,
            success=True,
        )
        return result

    return None


def invoke_with_tools(state: AgentState, session_id: str = "default") -> str:
    """Try tool calling first, then degrade gracefully to plain chat."""
    global PENDING_CONFIRMATIONS

    tried_providers = set()

    while True:
        try:
            llm, provider_name = get_llm(need_tools=True, exclude=tried_providers)
        except Exception as exc:
            return invoke_without_tools(state, reason=f"tool provider unavailable: {exc}")

        llm_with_tools = llm.bind_tools(ALL_TOOLS)
        messages = build_messages(state)

        try:
            response = llm_with_tools.invoke(messages)
            mark_provider_healthy(provider_name)
            break
        except Exception as exc:
            mark_provider_failed(provider_name, exc)
            tried_providers.add(provider_name)
            continue

    messages.append(response)

    if not getattr(response, "tool_calls", None):
        return response.content

    for tool_call in response.tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]

        if tool_name not in TOOL_MAP:
            tool_result = f"Tool '{tool_name}' is not registered."
        else:
            precheck_result = precheck_tool_call(tool_name, tool_args)
            if precheck_result is not None:
                tool_result = precheck_result
                log_tool_execution(
                    session_id=session_id,
                    tool_name=tool_name,
                    tool_args=tool_args,
                    result=str(tool_result),
                    success=False,
                )
            elif tool_name in DANGEROUS_TOOLS:
                confirmation_message = build_confirmation_message(tool_name, tool_args)
                PENDING_CONFIRMATIONS[session_id] = {
                    "tool_name": tool_name,
                    "tool_args": tool_args,
                    "message": confirmation_message,
                }
                tool_result = confirmation_message
                log_tool_execution(
                    session_id=session_id,
                    tool_name=tool_name,
                    tool_args=tool_args,
                    result="Confirmation requested",
                    success=True,
                )
            else:
                tool_result = execute_logged_tool(
                    tool_name=tool_name,
                    tool_args=tool_args,
                    invoker=lambda: TOOL_MAP[tool_name].invoke(tool_args),
                    session_id=session_id,
                )

        messages.append(ToolMessage(
            content=format_tool_result(tool_result),
            tool_call_id=tool_call["id"],
        ))

    try:
        final = llm_with_tools.invoke(messages)
        mark_provider_healthy(provider_name)
        return final.content
    except Exception as exc:
        mark_provider_failed(provider_name, exc)
        return invoke_without_tools(
            state,
            reason=f"tool follow-up failed after execution: {exc}",
        )


def route_obvious_task(user_input: str) -> str | None:
    """
    Use simple intent heuristics for obvious requests so the agent does not
    overthink very clear PC actions.
    """
    text = user_input.lower()

    if any(phrase in text for phrase in [
        "open notepad", "open chrome", "open google chrome", "open calculator",
        "open vscode", "open visual studio code", "launch ", "start ",
        "open folder", "open directory", "go to folder", "go to directory",
        "open downloads", "open documents", "open desktop", "open pictures",
        "open videos", "open music", "go to downloads", "go to documents",
    ]):
        return "tool"

    if any(phrase in text for phrase in [
        "create folder", "make folder", "make one folder", "create a folder",
        "create file", "make file", "read file", "open file", "find file",
        "find folder", "search folder", "locate folder",
    ]):
        return "tool"

    if any(phrase in text for phrase in [
        "see my ram", "show my ram", "check ram", "show cpu", "check cpu",
        "system summary", "system status", "pc status", "what running",
        "running now", "running on my pc", "processes",
    ]):
        return "tool"

    if any(phrase in text for phrase in [
        "search ", "google ", "youtube ", "news", "weather",
    ]):
        return "tool"

    if any(phrase in text for phrase in [
        "remind me", "set reminder",
    ]):
        return "tool"

    if any(phrase in text for phrase in [
        "write python", "run python", "install package", "install pandas",
    ]):
        return "tool"

    return None


def normalize_user_input(user_input: str) -> str:
    """
    Rewrite messy or informal user input into a clear internal task
    without changing the actual meaning.
    """
    try:
        llm, provider_name = get_llm(need_tools=False)
        prompt = [
            SystemMessage(content="""
You rewrite user requests into short, clear task instructions.

Rules:
- Keep the same meaning.
- Do not add new intent.
- Fix broken grammar if needed.
- Make the instruction clearer for a tool-using assistant.
- Return only the rewritten request.
"""),
            HumanMessage(content=user_input)
        ]

        response = llm.invoke(prompt)
        mark_provider_healthy(provider_name)
        return response if isinstance(response, str) else response.content.strip()
    except Exception as exc:
        try:
            mark_provider_failed(provider_name, exc)  # type: ignore[name-defined]
        except Exception:
            pass
        return user_input


def plan_action(user_input: str) -> str:
    """
    Decide whether the request is normal chat, single tool use,
    multi-step action, or needs clarification.
    Returns one of: chat, tool, multi_step, clarify
    """
    try:
        llm, provider_name = get_llm(need_tools=False)
        prompt = [
            SystemMessage(content="""
Classify the user's request into one of these labels only:

chat
tool
multi_step
clarify

Rules:
- chat = normal conversation or answer without tools
- tool = one clear action/tool is enough
- multi_step = multiple actions or a workflow is needed
- clarify = unsafe, ambiguous, or missing critical details

Return only one label.
"""),
            HumanMessage(content=user_input)
        ]

        response = llm.invoke(prompt)
        mark_provider_healthy(provider_name)
        text = response if isinstance(response, str) else response.content
        label = text.strip().lower()

        if label in {"chat", "tool", "multi_step", "clarify"}:
            return label
        return "tool"
    except Exception as exc:
        try:
            mark_provider_failed(provider_name, exc)  # type: ignore[name-defined]
        except Exception:
            pass
        return "tool"

def expand_multi_step_request(user_input: str) -> str:
    """
    Rewrite a multi-step user request into a clearer action-oriented instruction
    without changing the intended meaning.
    """
    try:
        llm, provider_name = get_llm(need_tools=False)
        prompt = [
            SystemMessage(content="""
You rewrite multi-step user requests into a short, clear step-by-step instruction.

Rules:
- Keep the same meaning.
- Do not remove any important requested action.
- Do not add extra actions.
- Make the task easier for a tool-using assistant to follow.
- Return only the rewritten instruction.
"""),
            HumanMessage(content=user_input)
        ]

        response = llm.invoke(prompt)
        mark_provider_healthy(provider_name)
        return response if isinstance(response, str) else response.content.strip()
    except Exception as exc:
        try:
            mark_provider_failed(provider_name, exc)  # type: ignore[name-defined]
        except Exception:
            pass
        return user_input


def think_node(state: AgentState) -> AgentState:
    """AI thinks and decides which tools to use."""
    normalized_input = normalize_user_input(state["user_input"])
    state["user_input"] = normalized_input

    action_type = route_obvious_task(state["user_input"]) or plan_action(state["user_input"])
    if action_type == "multi_step":
        expanded_input = expand_multi_step_request(state["user_input"])
        state["user_input"] = expanded_input


    if action_type == "clarify":
        state["response"] =""
        return state

    if action_type == "chat":
        try:
            state["response"] = invoke_without_tools(state)
        except Exception:
            state["response"] = (
                "I understood your message, but I hit a problem while replying. "
                "Please try again."
            )
        return state

    try:
        state["response"] = invoke_with_tools(
        state,
        session_id=state.get("session_id", "default"),
    )

    except Exception as exc:
        try:
            state["response"] = invoke_without_tools(
                state,
                reason=f"global fallback after exception: {exc}",
            )
        except Exception:
            state["response"] = (
                "I hit an internal problem while processing that request. "
                "Please try again, or rephrase it in a simpler way."
            )

# REMOVE this fragile block at the bottom of think_node:
    lower = state["user_input"].lower()
    if "to" in lower and any(word in lower for word in ["name", "call", "rename"]):
        words = state["user_input"].strip().split()
        new_name = words[-1].strip(".,!?")
        bad = ["name", "you", "to", "change", "call", "my",
            "your", "is", "a", "the", "from", "aria"]
        if new_name.lower() not in bad and len(new_name) >= 2:
            state["agent_name"] = new_name.upper()

    # REPLACE with this:
    name_match = re.search(
        r"(?:call|name|rename)\s+(?:you|yourself)?\s*(?:to\s+)?([A-Za-z][A-Za-z0-9]{1,29})\b",
        state["user_input"],
        re.IGNORECASE,
    )
    if name_match:
        candidate = name_match.group(1).strip()
        bad = {"name", "you", "to", "change", "call", "my", "your",
            "is", "a", "the", "from", "aria", "agent"}
        if candidate.lower() not in bad:
            state["agent_name"] = candidate.upper()

    return state



def save_memory_node(state: AgentState) -> AgentState:
    save_memory(state["user_input"], "user")
    save_memory(state["response"], "assistant")

    if state["agent_name"] != DEFAULT_NAME:
        save_memory(f"My name is {state['agent_name']}", "system")

    return state


def build_agent():
    workflow = StateGraph(AgentState)
    workflow.add_node("load_memory", load_memory_node)
    workflow.add_node("think", think_node)
    workflow.add_node("save_memory", save_memory_node)
    workflow.set_entry_point("load_memory")
    workflow.add_edge("load_memory", "think")
    workflow.add_edge("think", "save_memory")
    workflow.add_edge("save_memory", END)
    return workflow.compile()


agent = build_agent()


def load_agent_name() -> str:
    """Load agent name from memory on startup."""
    try:
        memories = search_memory("My name is", top_k=10)
        for memory in memories:
            text = memory.get("text", "")
            role = memory.get("role", "")
            if role == "system" and "My name is" in text:
                name = text.replace("My name is", "").strip()
                if len(name) >= 2:
                    print(f"Loaded agent name: {name}")
                    return name.upper()

        memories = search_memory("change your name to", top_k=2)
        for memory in memories:
            text = memory.get("text", "").lower()
            if "name" in text and "to" in text:
                words = text.split()
                if "to" in words:
                    idx = words.index("to")
                    if idx + 1 < len(words):
                        name = words[idx + 1].strip(".,!?")
                        bad = ["name", "you", "to", "change",
                               "call", "my", "your", "is", "a", "the"]
                        if name not in bad and len(name) >= 2:
                            return name.upper()
    except Exception as exc:
        print(f"Memory load error: {exc}")

    return DEFAULT_NAME


AGENT_NAME = load_agent_name()
PENDING_CONFIRMATIONS = {}
SESSION_CONTEXTS = {}



def convert_history(history: list) -> list:
    converted = []

    for msg in history:
        if isinstance(msg, dict):
            role = msg.get("role", "").lower()
            content = msg.get("content", "")

            if role == "user":
                converted.append(HumanMessage(content=content))
            elif role == "assistant":
                converted.append(AIMessage(content=content))
            elif role == "system":
                converted.append(SystemMessage(content=content))
        else:
            converted.append(msg)

    return converted

def is_confirmation(text: str) -> bool:
    return text.strip().lower() in {
        "yes", "y", "confirm", "ok", "okay", "do it", "go ahead"
    }
def is_cancellation(text: str) -> bool:
    return text.strip().lower() in {
        "cancel", "stop", "no", "don't", "do not", "abort"
    }


def clean_response(text: str) -> str:
    """Remove leaked reasoning. Never return empty."""
    if not text or not text.strip():
        return "Done."

    # Remove leaked tool call annotations like [tool_name] args: "value"
    import re
    text = re.sub(r'\[tool_\w+\][^\n]*\n?', '', text).strip()
    text = re.sub(r'tool_\w+\s*\([^)]*\)\s*', '', text).strip()
    # Remove duplicate lines (agent sometimes repeats the same sentence)
    lines = text.split('\n')
    seen = []
    for line in lines:
        if line.strip() and line.strip() not in seen:
            seen.append(line.strip())
    text = '\n'.join(seen).strip()
    if not text:
        return "Done."

    # Always return short responses as-is
    if len(text) < 200:
        return text.strip()

    # Never clean honest replies
    honest = [
        "i don't have", "i can't", "i cannot", "don't have a tool",
        "not supported", "i'm not able", "i lack", "i know your name",
        "you've taught me", "we've had", "got it", "i'll remember",
        "noted", "understood",
    ]
    if any(p in text.lower() for p in honest):
        return text.strip()

    # Detect leaked reasoning
    leaks = [
        "we need to", "the user wants", "the user asked",
        "let me think", "let me consider", "the tool list",
        "we should", "we can", "given that", "given the context",
        "the assistant", "we might", "we could",
        "the conversation shows", "there is no tool",
        "there's no tool", "let's see",
    ]

    count = sum(1 for p in leaks if p in text.lower())

    if count >= 2 and len(text) > 300:
        # Find last clean paragraph
        for para in reversed([p.strip() for p in text.split('\n\n') if p.strip()]):
            para_leaks = sum(1 for p in leaks if p in para.lower())
            if para_leaks == 0 and 5 < len(para) < 300:
                return para
        # Last sentence
        sentences = [s.strip() for s in re.split(r'[.!?]', text) if s.strip()]
        if sentences and len(sentences[-1]) < 200:
            return sentences[-1] + "."
        return "I had trouble with that. Please try again."

    return text.strip() if text.strip() else "Done."
def chat(
    user_input: str,
    history: list | None = None,
    agent_name: str | None = None,
    session_id: str = "default",
) -> tuple:
    history = history[-4:] if len(history) > 4 else history
    global AGENT_NAME, PENDING_CONFIRMATIONS

    current_name = agent_name or AGENT_NAME
    converted_history = convert_history(history or [])
    pending = PENDING_CONFIRMATIONS.get(session_id)

    if pending and is_confirmation(user_input):
        tool_name = pending["tool_name"]
        tool_args = pending["tool_args"]

        try:
            result = execute_logged_tool(
                tool_name=tool_name,
                tool_args=tool_args,
                invoker=lambda: TOOL_MAP[tool_name].invoke(tool_args),
                session_id=session_id,
            )

            del PENDING_CONFIRMATIONS[session_id]
            response_text = f"Confirmed. {format_tool_result(result)}"
            persist_exchange(user_input, response_text, AGENT_NAME)
            return clean_response(response_text), AGENT_NAME

        except Exception as exc:
            del PENDING_CONFIRMATIONS[session_id]
            response_text = f"I tried to execute the confirmed action, but it failed: {exc}"
            persist_exchange(user_input, response_text, AGENT_NAME)
            return clean_response(response_text), AGENT_NAME


    if pending and is_cancellation(user_input):
        del PENDING_CONFIRMATIONS[session_id]
        response_text = "Okay, I cancelled the pending action."
        persist_exchange(user_input, response_text, AGENT_NAME)
        return clean_response(response_text), AGENT_NAME

    if pending and not is_confirmation(user_input):
        response_text = f"{pending['message']} Reply with yes to continue or say cancel."
        persist_exchange(user_input, response_text, AGENT_NAME)
        return clean_response(response_text), AGENT_NAME

    multi_step_result = execute_multi_step_task(user_input, session_id, current_name)
    if multi_step_result is not None:
        persist_exchange(user_input, multi_step_result, AGENT_NAME)
        return clean_response(multi_step_result), AGENT_NAME

    direct_result = run_direct_action(user_input, session_id)
    if direct_result is not None:
        persist_exchange(user_input, direct_result, AGENT_NAME)
        return clean_response(direct_result), AGENT_NAME

    result = agent.invoke({
        "user_input": user_input,
        "messages": converted_history,
        "response": "",
        "context": "",
        "agent_name": current_name,
        "session_id": session_id,
    })

    AGENT_NAME = result["agent_name"]
    return result["response"], AGENT_NAME
