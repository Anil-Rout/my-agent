# file_tool.py - File and folder operations for the local PC

import os
import shutil
from datetime import datetime


DESKTOP = os.path.join(os.path.expanduser("~"), "OneDrive", "Desktop")
DOCUMENTS = os.path.join(os.path.expanduser("~"), "Documents")
DOWNLOADS = os.path.join(os.path.expanduser("~"), "Downloads")
PICTURES = os.path.join(os.path.expanduser("~"), "Pictures")
VIDEOS = os.path.join(os.path.expanduser("~"), "Videos")
MUSIC = os.path.join(os.path.expanduser("~"), "Music")
ONEDRIVE = os.path.join(os.path.expanduser("~"), "OneDrive")
HOME = os.path.expanduser("~")

COMMON_FOLDERS = {
    "desktop": DESKTOP,
    "documents": DOCUMENTS,
    "document": DOCUMENTS,
    "downloads": DOWNLOADS,
    "download": DOWNLOADS,
    "pictures": PICTURES,
    "picture": PICTURES,
    "photos": PICTURES,
    "videos": VIDEOS,
    "video": VIDEOS,
    "music": MUSIC,
    "songs": MUSIC,
    "onedrive": ONEDRIVE,
    "home": HOME,
    "user": HOME,
}


def make_tool_result(action: str, success: bool, message: str, data: dict | None = None) -> dict:
    return {
        "success": success,
        "action": action,
        "message": message,
        "data": data or {},
    }


def normalize_user_path(path: str) -> str:
    return path.strip().strip('"').strip("'")


def resolve_user_path(path: str, prefer_existing: bool = False) -> str:
    cleaned = normalize_user_path(path)
    lowered = cleaned.lower()

    if lowered in COMMON_FOLDERS:
        return COMMON_FOLDERS[lowered]

    expanded = os.path.expandvars(os.path.expanduser(cleaned))

    if os.path.isabs(expanded):
        return expanded

    home_candidate = os.path.join(HOME, expanded)
    desktop_candidate = os.path.join(DESKTOP, expanded)
    documents_candidate = os.path.join(DOCUMENTS, expanded)
    downloads_candidate = os.path.join(DOWNLOADS, expanded)

    candidates = [desktop_candidate, documents_candidate, downloads_candidate, home_candidate]

    if prefer_existing:
        for candidate in candidates:
            if os.path.exists(candidate):
                return candidate

    return desktop_candidate


def find_folder_by_name(folder_name: str, max_depth: int = 4) -> str | None:
    cleaned = normalize_user_path(folder_name)
    lowered = cleaned.lower()

    if lowered in COMMON_FOLDERS:
        return COMMON_FOLDERS[lowered]

    search_roots = [DESKTOP, DOCUMENTS, DOWNLOADS, ONEDRIVE, HOME]
    seen = set()

    for root in search_roots:
        if not os.path.isdir(root) or root in seen:
            continue
        seen.add(root)

        for current_root, dirs, _ in os.walk(root):
            relative = os.path.relpath(current_root, root)
            depth = 0 if relative == "." else relative.count(os.sep) + 1
            if depth > max_depth:
                dirs[:] = []
                continue

            for directory in dirs:
                if directory.lower() == lowered:
                    return os.path.join(current_root, directory)

    return None


def resolve_existing_folder_path(path: str) -> str | None:
    cleaned = normalize_user_path(path)
    resolved = resolve_user_path(cleaned, prefer_existing=True)

    if os.path.isdir(resolved):
        return resolved

    if os.path.isdir(cleaned):
        return cleaned

    return find_folder_by_name(cleaned)


def _resolve_path(path: str) -> str:
    return resolve_user_path(path)


def create_folder(path: str) -> dict:
    """Create a new folder."""
    import re
    # Strip location words — extract only the folder name
    clean = re.sub(
        r'\s+(on|in|at|inside|to)\s+(my\s+)?(desktop|documents|downloads|pictures|videos|music|home|pc|computer|disk|drive).*$',
        '', path, flags=re.IGNORECASE
    ).strip().strip('"\'')
    if clean and clean != path:
        path = clean
    try:
        folder_path = _resolve_path(path)
        os.makedirs(folder_path, exist_ok=True)
        folder_name = os.path.basename(folder_path.rstrip("\\/"))
        return make_tool_result(
            action="create_folder",
            success=True,
            message=f"Folder '{folder_name}' created successfully.",
            data={"folder_name": folder_name, "path": folder_path},
        )
    except Exception as exc:
        return make_tool_result(
            action="create_folder",
            success=False,
            message=f"Error creating folder: {exc}",
            data={"path": path},
        )

def create_file(path: str, content: str = "") -> dict:
    """Create a new file with optional content."""
    try:
        file_path = _resolve_path(path)
        with open(file_path, "w", encoding="utf-8") as file_handle:
            file_handle.write(content)
        filename = os.path.basename(file_path)
        return make_tool_result(
            action="create_file",
            success=True,
            message=f"File '{filename}' created successfully.",
            data={"filename": filename, "path": file_path},
        )
    except Exception as exc:
        return make_tool_result(
            action="create_file",
            success=False,
            message=f"Error creating file: {exc}",
            data={"path": path},
        )


def read_file(path: str) -> dict:
    """Read contents of a file."""
    try:
        file_path = _resolve_path(path)
        with open(file_path, "r", encoding="utf-8") as file_handle:
            content = file_handle.read()
        return make_tool_result(
            action="read_file",
            success=True,
            message="File read successfully.",
            data={"filepath": file_path, "content": content},
        )
    except Exception as exc:
        return make_tool_result(
            action="read_file",
            success=False,
            message=f"Error reading file: {exc}",
            data={"filepath": path},
        )


def delete_file(path: str) -> dict:
    """Delete a file or folder."""
    try:
        target_path = _resolve_path(path)
        if os.path.isfile(target_path):
            os.remove(target_path)
            return make_tool_result(
                action="delete_file",
                success=True,
                message=f"File deleted: {target_path}",
                data={"filepath": target_path},
            )
        if os.path.isdir(target_path):
            shutil.rmtree(target_path)
            return make_tool_result(
                action="delete_file",
                success=True,
                message=f"Folder deleted: {target_path}",
                data={"filepath": target_path},
            )
        return make_tool_result(
            action="delete_file",
            success=False,
            message=f"File not found: {target_path}",
            data={"filepath": target_path},
        )
    except Exception as exc:
        return make_tool_result(
            action="delete_file",
            success=False,
            message=f"Error deleting: {exc}",
            data={"filepath": path},
        )


def list_files(path: str = DESKTOP) -> str:
    """List all files in a folder."""
    try:
        folder_path = _resolve_path(path)
        items = os.listdir(folder_path)
        if not items:
            return f"Folder is empty: {folder_path}"

        result = f"Contents of {folder_path}:\n"
        for item in items:
            full_path = os.path.join(folder_path, item)
            icon = "[DIR]" if os.path.isdir(full_path) else "[FILE]"
            result += f"  {icon} {item}\n"
        return result
    except Exception as exc:
        return f"Error listing files: {exc}"


def search_files(folder: str, keyword: str) -> str:
    """Search for files by name keyword."""
    try:
        folder_path = _resolve_path(folder)
        results = []
        for root, _, files in os.walk(folder_path):
            for file_name in files:
                if keyword.lower() in file_name.lower():
                    results.append(os.path.join(root, file_name))

        if not results:
            return f"No files found with keyword: {keyword}"

        result = f"Found {len(results)} files:\n"
        for found_path in results[:20]:
            result += f"  [FILE] {found_path}\n"
        return result
    except Exception as exc:
        return f"Error searching: {exc}"


def get_file_info(path: str) -> str:
    """Get detailed info about a file."""
    try:
        target_path = _resolve_path(path)
        stat = os.stat(target_path)
        size = stat.st_size
        modified = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
        return (
            "File Info:\n"
            f"  Path:     {target_path}\n"
            f"  Size:     {size} bytes\n"
            f"  Modified: {modified}\n"
            f"  Type:     {'Folder' if os.path.isdir(target_path) else 'File'}"
        )
    except Exception as exc:
        return f"Error: {exc}"
