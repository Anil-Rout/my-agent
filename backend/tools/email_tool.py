# email_tool.py — Full email control via Gmail or Outlook
# Supports: send, read, reply, delete, search, attachments

import imaplib
import json
import os
import smtplib
import email as email_lib
from datetime import datetime
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import decode_header
from pathlib import Path
from typing import Optional

from config.paths import load_backend_env

load_backend_env()

# ── CONFIG ────────────────────────────────────────────────────────────────────

PROVIDER_SETTINGS = {
    "gmail": {
        "smtp_host": "smtp.gmail.com",
        "smtp_port": 587,
        "imap_host": "imap.gmail.com",
        "imap_port": 993,
    },
    "outlook": {
        "smtp_host": "smtp-mail.outlook.com",
        "smtp_port": 587,
        "imap_host": "outlook.office365.com",
        "imap_port": 993,
    },
    "yahoo": {
        "smtp_host": "smtp.mail.yahoo.com",
        "smtp_port": 587,
        "imap_host": "imap.mail.yahoo.com",
        "imap_port": 993,
    },
}


def _get_config() -> tuple[str, str, str]:
    """Get email address, password, provider from env."""
    address  = os.getenv("EMAIL_ADDRESS", "").strip()
    password = os.getenv("EMAIL_PASSWORD", "").strip()
    provider = os.getenv("EMAIL_PROVIDER", "gmail").strip().lower()
    return address, password, provider


def _get_settings(provider: str) -> dict:
    return PROVIDER_SETTINGS.get(provider, PROVIDER_SETTINGS["gmail"])


def _is_configured() -> bool:
    address, password, _ = _get_config()
    return bool(address and password)


def make_result(action: str, success: bool, message: str, data: dict | None = None) -> dict:
    return {"success": success, "action": action, "message": message, "data": data or {}}


# ── SMTP — SENDING ────────────────────────────────────────────────────────────

def _get_smtp() -> smtplib.SMTP:
    address, password, provider = _get_config()
    settings = _get_settings(provider)
    server = smtplib.SMTP(settings["smtp_host"], settings["smtp_port"])
    server.ehlo()
    server.starttls()
    server.login(address, password)
    return server


def send_email(
    to: str,
    subject: str,
    body: str,
    cc: str = "",
    attachment_path: str = "",
) -> dict:
    """Send an email."""
    if not _is_configured():
        return make_result("send_email", False,
            "Email not configured. Add EMAIL_ADDRESS and EMAIL_PASSWORD to .env file.")
    try:
        address, _, _ = _get_config()
        msg = MIMEMultipart()
        msg["From"]    = address
        msg["To"]      = to
        msg["Subject"] = subject
        if cc:
            msg["Cc"] = cc

        msg.attach(MIMEText(body, "plain"))

        # Attach file if provided
        if attachment_path and os.path.exists(attachment_path):
            with open(attachment_path, "rb") as f:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(f.read())
            encoders.encode_base64(part)
            filename = os.path.basename(attachment_path)
            part.add_header("Content-Disposition", f"attachment; filename={filename}")
            msg.attach(part)

        recipients = [to] + ([cc] if cc else [])
        server = _get_smtp()
        server.sendmail(address, recipients, msg.as_string())
        server.quit()

        return make_result("send_email", True,
            f"Email sent to {to} — Subject: {subject}",
            {"to": to, "subject": subject, "has_attachment": bool(attachment_path)})

    except Exception as exc:
        return make_result("send_email", False, f"Failed to send email: {exc}")


def reply_to_email(
    original_message_id: str,
    to: str,
    subject: str,
    body: str,
    original_body: str = "",
) -> dict:
    """Reply to an email."""
    if not _is_configured():
        return make_result("reply_email", False, "Email not configured.")
    try:
        address, _, _ = _get_config()
        msg = MIMEMultipart()
        msg["From"]    = address
        msg["To"]      = to
        msg["Subject"] = subject if subject.startswith("Re:") else f"Re: {subject}"
        if original_message_id:
            msg["In-Reply-To"] = original_message_id
            msg["References"]  = original_message_id

        reply_body = body
        if original_body:
            reply_body += f"\n\n--- Original Message ---\n{original_body}"

        msg.attach(MIMEText(reply_body, "plain"))

        server = _get_smtp()
        server.sendmail(address, [to], msg.as_string())
        server.quit()

        return make_result("reply_email", True,
            f"Reply sent to {to}",
            {"to": to, "subject": msg["Subject"]})

    except Exception as exc:
        return make_result("reply_email", False, f"Failed to reply: {exc}")


def forward_email(
    to: str,
    original_subject: str,
    original_body: str,
    note: str = "",
) -> dict:
    """Forward an email to another recipient."""
    if not _is_configured():
        return make_result("forward_email", False, "Email not configured.")
    try:
        body = note + "\n\n--- Forwarded Message ---\n" + original_body if note else "--- Forwarded Message ---\n" + original_body
        return send_email(to, f"Fwd: {original_subject}", body)
    except Exception as exc:
        return make_result("forward_email", False, f"Failed to forward: {exc}")


# ── IMAP — READING ────────────────────────────────────────────────────────────

def _get_imap() -> imaplib.IMAP4_SSL:
    address, password, provider = _get_config()
    settings = _get_settings(provider)
    mail = imaplib.IMAP4_SSL(settings["imap_host"], settings["imap_port"])
    mail.login(address, password)
    return mail


def _decode_header_value(value: str) -> str:
    """Decode email header."""
    if not value:
        return ""
    try:
        parts = decode_header(value)
        result = ""
        for part, charset in parts:
            if isinstance(part, bytes):
                result += part.decode(charset or "utf-8", errors="replace")
            else:
                result += part
        return result
    except Exception:
        return str(value)


def _parse_email(msg_data: bytes) -> dict:
    """Parse raw email bytes into a dict."""
    try:
        msg = email_lib.message_from_bytes(msg_data)
        subject  = _decode_header_value(msg.get("Subject", ""))
        from_    = _decode_header_value(msg.get("From", ""))
        to_      = _decode_header_value(msg.get("To", ""))
        date_    = msg.get("Date", "")
        msg_id   = msg.get("Message-ID", "")

        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    try:
                        body = part.get_payload(decode=True).decode(
                            part.get_content_charset() or "utf-8", errors="replace"
                        )
                        break
                    except Exception:
                        pass
        else:
            try:
                body = msg.get_payload(decode=True).decode(
                    msg.get_content_charset() or "utf-8", errors="replace"
                )
            except Exception:
                body = str(msg.get_payload())

        return {
            "message_id": msg_id,
            "subject":    subject,
            "from":       from_,
            "to":         to_,
            "date":       date_,
            "body":       body[:2000].strip(),
        }
    except Exception as exc:
        return {"error": str(exc)}


def get_inbox(limit: int = 10, unread_only: bool = False) -> dict:
    """Get emails from inbox."""
    if not _is_configured():
        return make_result("get_inbox", False, "Email not configured.")
    try:
        mail = _get_imap()
        mail.select("INBOX")

        search_criteria = "UNSEEN" if unread_only else "ALL"
        _, message_numbers = mail.search(None, search_criteria)
        msg_ids = message_numbers[0].split()

        # Get latest emails
        latest = msg_ids[-limit:] if len(msg_ids) > limit else msg_ids
        latest = list(reversed(latest))

        emails = []
        for num in latest:
            _, msg_data = mail.fetch(num, "(RFC822)")
            if msg_data and msg_data[0]:
                parsed = _parse_email(msg_data[0][1])
                parsed["num"] = num.decode()
                emails.append(parsed)

        mail.logout()

        if not emails:
            label = "unread emails" if unread_only else "emails"
            return make_result("get_inbox", True,
                f"No {label} found.",
                {"emails": [], "count": 0})

        # Format summary
        lines = []
        for i, e in enumerate(emails, 1):
            lines.append(
                f"{i}. From: {e.get('from', 'Unknown')[:40]}\n"
                f"   Subject: {e.get('subject', 'No subject')[:60]}\n"
                f"   Date: {e.get('date', '')[:30]}"
            )

        return make_result("get_inbox", True,
            f"Latest {len(emails)} emails:\n\n" + "\n\n".join(lines),
            {"emails": emails, "count": len(emails)})

    except Exception as exc:
        return make_result("get_inbox", False, f"Failed to read inbox: {exc}")


def read_email(email_number: str) -> dict:
    """Read a specific email by its number."""
    if not _is_configured():
        return make_result("read_email", False, "Email not configured.")
    try:
        mail = _get_imap()
        mail.select("INBOX")

        _, msg_data = mail.fetch(email_number.encode(), "(RFC822)")
        if not msg_data or not msg_data[0]:
            mail.logout()
            return make_result("read_email", False, "Email not found.")

        parsed = _parse_email(msg_data[0][1])

        # Mark as read
        mail.store(email_number.encode(), "+FLAGS", "\\Seen")
        mail.logout()

        summary = (
            f"From: {parsed.get('from', '')}\n"
            f"Subject: {parsed.get('subject', '')}\n"
            f"Date: {parsed.get('date', '')}\n\n"
            f"{parsed.get('body', '')}"
        )

        return make_result("read_email", True, summary, {"email": parsed})

    except Exception as exc:
        return make_result("read_email", False, f"Failed to read email: {exc}")


def delete_email(email_number: str) -> dict:
    """Delete (trash) an email by its number."""
    if not _is_configured():
        return make_result("delete_email", False, "Email not configured.")
    try:
        mail = _get_imap()
        mail.select("INBOX")
        mail.store(email_number.encode(), "+FLAGS", "\\Deleted")
        mail.expunge()
        mail.logout()

        return make_result("delete_email", True,
            f"Email #{email_number} deleted.")

    except Exception as exc:
        return make_result("delete_email", False, f"Failed to delete email: {exc}")


def search_emails(query: str, limit: int = 10) -> dict:
    """Search emails by subject or sender."""
    if not _is_configured():
        return make_result("search_emails", False, "Email not configured.")
    try:
        mail = _get_imap()
        mail.select("INBOX")

        # Search by subject and sender
        _, nums_subject = mail.search(None, f'SUBJECT "{query}"')
        _, nums_from    = mail.search(None, f'FROM "{query}"')

        all_nums = list(set(
            nums_subject[0].split() + nums_from[0].split()
        ))

        if not all_nums:
            mail.logout()
            return make_result("search_emails", True,
                f"No emails found matching '{query}'.",
                {"emails": [], "count": 0})

        latest = list(reversed(all_nums))[:limit]
        emails = []
        for num in latest:
            _, msg_data = mail.fetch(num, "(RFC822)")
            if msg_data and msg_data[0]:
                parsed = _parse_email(msg_data[0][1])
                parsed["num"] = num.decode()
                emails.append(parsed)

        mail.logout()

        lines = []
        for i, e in enumerate(emails, 1):
            lines.append(
                f"{i}. From: {e.get('from', '')[:40]}\n"
                f"   Subject: {e.get('subject', '')[:60]}"
            )

        return make_result("search_emails", True,
            f"Found {len(emails)} emails for '{query}':\n\n" + "\n\n".join(lines),
            {"emails": emails, "count": len(emails)})

    except Exception as exc:
        return make_result("search_emails", False, f"Search failed: {exc}")


def get_unread_count() -> dict:
    """Get count of unread emails."""
    if not _is_configured():
        return make_result("unread_count", False, "Email not configured.")
    try:
        mail = _get_imap()
        mail.select("INBOX")
        _, msgs = mail.search(None, "UNSEEN")
        count = len(msgs[0].split()) if msgs[0] else 0
        mail.logout()

        msg = f"You have {count} unread email{'s' if count != 1 else ''}."
        return make_result("unread_count", True, msg, {"count": count})

    except Exception as exc:
        return make_result("unread_count", False, f"Failed to get unread count: {exc}")


def mark_email_read(email_number: str) -> dict:
    """Mark an email as read."""
    if not _is_configured():
        return make_result("mark_read", False, "Email not configured.")
    try:
        mail = _get_imap()
        mail.select("INBOX")
        mail.store(email_number.encode(), "+FLAGS", "\\Seen")
        mail.logout()
        return make_result("mark_read", True, f"Email #{email_number} marked as read.")
    except Exception as exc:
        return make_result("mark_read", False, f"Failed: {exc}")


def mark_email_unread(email_number: str) -> dict:
    """Mark an email as unread."""
    if not _is_configured():
        return make_result("mark_unread", False, "Email not configured.")
    try:
        mail = _get_imap()
        mail.select("INBOX")
        mail.store(email_number.encode(), "-FLAGS", "\\Seen")
        mail.logout()
        return make_result("mark_unread", True, f"Email #{email_number} marked as unread.")
    except Exception as exc:
        return make_result("mark_unread", False, f"Failed: {exc}")


def get_email_config_status() -> dict:
    """Check if email is configured."""
    address, _, provider = _get_config()
    if not _is_configured():
        return make_result("email_status", False,
            "Email not configured. Add EMAIL_ADDRESS and EMAIL_PASSWORD to the .env file. "
            "For Gmail, use an App Password from myaccount.google.com/apppasswords")
    return make_result("email_status", True,
        f"Email configured: {address} ({provider})",
        {"address": address, "provider": provider})