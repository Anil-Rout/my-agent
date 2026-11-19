import os
import subprocess
import tempfile
from datetime import datetime


DESKTOP = os.path.join(os.path.expanduser("~"), "OneDrive", "Desktop")


def make_tool_result(action: str, success: bool, message: str, data: dict | None = None) -> dict:
    return {
        "success": success,
        "action": action,
        "message": message,
        "data": data or {},
    }


def _resolve_code_path(filename=None, folder_path=None):
    target_folder = folder_path or DESKTOP
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"code_{timestamp}.py"
    
    # Only add .py if file has NO extension at all
    if "." not in os.path.basename(filename):
        filename += ".py"
    
    path = os.path.join(target_folder, filename)
    return filename, path


def write_and_save_code(code: str, filename: str | None = None, folder_path: str | None = None) -> dict:
    """Save code to a Python file."""
    try:
        filename, path = _resolve_code_path(filename, folder_path)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as file_handle:
            file_handle.write(code)
        return make_tool_result(
            action="write_code",
            success=True,
            message=f"Code saved: {path}",
            data={"filename": filename, "path": path},
        )
    except Exception as exc:
        return make_tool_result(
            action="write_code",
            success=False,
            message=f"Error saving code: {exc}",
            data={"filename": filename or "", "folder_path": folder_path or DESKTOP},
        )


def run_code(code: str, timeout: int = 10) -> str:
    """Run Python code and return output."""
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".py",
            delete=False,
            encoding="utf-8",
        ) as file_handle:
            file_handle.write(code)
            temp_path = file_handle.name

        result = subprocess.run(
            ["python", temp_path],
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        os.unlink(temp_path)

        if result.returncode == 0:
            output = result.stdout or "Code ran successfully with no output"
            return f"Output:\n{output}"
        return f"Error:\n{result.stderr}"

    except subprocess.TimeoutExpired:
        return f"Code timed out after {timeout} seconds"
    except Exception as exc:
        return f"Error running code: {exc}"


def run_file(path: str, timeout: int = 30) -> str:
    """Run an existing Python file."""
    try:
        if not os.path.exists(path):
            return f"File not found: {path}"

        result = subprocess.run(
            ["python", path],
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        if result.returncode == 0:
            output = result.stdout or "File ran successfully"
            return f"Output:\n{output}"
        return f"Error:\n{result.stderr}"

    except subprocess.TimeoutExpired:
        return f"Timed out after {timeout} seconds"
    except Exception as exc:
        return f"Error: {exc}"


def write_and_run_code(code: str, filename: str | None = None, folder_path: str | None = None) -> dict:
    """Write code, save it, and run it."""
    try:
        filename, path = _resolve_code_path(filename, folder_path)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as file_handle:
            file_handle.write(code)

        result = subprocess.run(
            ["python", path],
            capture_output=True,
            text=True,
            timeout=15,
        )

        if result.returncode == 0:
            output = result.stdout or "No output"
            return make_tool_result(
                action="write_and_run_code",
                success=True,
                message=f"Code saved to {path} and ran successfully.",
                data={"filename": filename, "path": path, "output": output},
            )

        return make_tool_result(
            action="write_and_run_code",
            success=False,
            message=f"Code saved to {path} but failed to run.",
            data={"filename": filename, "path": path, "error": result.stderr},
        )

    except Exception as exc:
        return make_tool_result(
            action="write_and_run_code",
            success=False,
            message=f"Error: {exc}",
            data={"filename": filename or "", "folder_path": folder_path or DESKTOP},
        )


def install_package(package: str) -> str:
    """Install a Python package."""
    try:
        result = subprocess.run(
            ["pip", "install", package],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode == 0:
            return f"Package installed: {package}"
        return f"Error installing {package}:\n{result.stderr}"
    except Exception as exc:
        return f"Error: {exc}"


def list_desktop_code_files() -> str:
    """List Python files on Desktop."""
    try:
        files = [filename for filename in os.listdir(DESKTOP) if filename.endswith(".py")]
        if not files:
            return "No Python files found on Desktop"
        result = "Python files on Desktop:\n"
        for filename in files:
            result += f"  - {filename}\n"
        return result
    except Exception as exc:
        return f"Error: {exc}"
