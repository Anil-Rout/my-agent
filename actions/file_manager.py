# file_manager.py — All file and folder operations

import os
import shutil
from datetime import datetime

def create_folder(path: str) -> str:
    """Create a new folder"""
    try:
        os.makedirs(path, exist_ok=True)
        return f"Folder created: {path}"
    except Exception as e:
        return f"Error creating folder: {str(e)}"

def create_file(path: str, content: str = "") -> str:
    """Create a new file with optional content"""
    try:
        with open(path, "w") as f:
            f.write(content)
        return f"File created: {path}"
    except Exception as e:
        return f"Error creating file: {str(e)}"

def read_file(path: str) -> str:
    """Read contents of a file"""
    try:
        with open(path, "r") as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"

def delete_file(path: str) -> str:
    """Delete a file"""
    try:
        os.remove(path)
        return f"File deleted: {path}"
    except Exception as e:
        return f"Error deleting file: {str(e)}"

def list_files(path: str) -> list:
    """List all files in a folder"""
    try:
        return os.listdir(path)
    except Exception as e:
        return [f"Error: {str(e)}"]

def search_files(folder: str, extension: str) -> list:
    """Search for files by extension"""
    results = []
    for root, dirs, files in os.walk(folder):
        for file in files:
            if file.endswith(extension):
                results.append(os.path.join(root, file))
    return results
