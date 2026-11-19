# Actions routes - executes PC actions
from fastapi import APIRouter
from actions.file_manager import create_folder, create_file, read_file, delete_file, list_files
from actions.system_info import get_cpu, get_ram, get_disk, get_all_info
from actions.app_controller import open_app, take_screenshot
from actions.code_runner import run_python_code
import re

router = APIRouter()

def execute_action(ai_response: str) -> str:
    """Parse AI response and execute the requested action"""
    try:
        action_match = re.search(r'ACTION:\s*(\w+)', ai_response)
        if not action_match:
            return None
        
        action = action_match.group(1).lower()
        
        # Parse parameters
        params = {}
        params_match = re.search(r'PARAMS:\s*(.+)', ai_response)
        if params_match:
            params_str = params_match.group(1)
            for param in params_str.split(','):
                if '=' in param:
                    key, value = param.split('=', 1)
                    params[key.strip()] = value.strip()
        
        # Execute the action
        if action == "create_folder":
            return create_folder(params.get("path", "new_folder"))
        elif action == "create_file":
            return create_file(params.get("path", "new_file.txt"), params.get("content", ""))
        elif action == "read_file":
            return read_file(params.get("path", ""))
        elif action == "delete_file":
            return delete_file(params.get("path", ""))
        elif action == "list_files":
            return list_files(params.get("path", "."))
        elif action == "open_app":
            return open_app(params.get("app", ""))
        elif action == "take_screenshot":
            return take_screenshot()
        elif action == "system_info":
            info_type = params.get("type", "all")
            if info_type == "cpu":   return get_cpu()
            if info_type == "ram":   return get_ram()
            if info_type == "disk":  return get_disk()
            return get_all_info()
        elif action == "run_code":
            return run_python_code(params.get("code", ""))
        else:
            return f"Unknown action: {action}"
    except Exception as e:
        return f"Error executing action: {str(e)}"

@router.get("/test")
def test_actions():
    return {"status": "Actions ready"}
