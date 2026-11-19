# Code Runner - writes and runs Python code
import subprocess
import tempfile
import os

def run_python_code(code: str) -> str:
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_path = f.name
        result = subprocess.run(
            ["python", temp_path],
            capture_output=True, text=True, timeout=30
        )
        os.unlink(temp_path)
        output = result.stdout if result.stdout else result.stderr
        return f"Output:\n{output}"
    except subprocess.TimeoutExpired:
        return "Error: Code took too long to run (30s timeout)"
    except Exception as e:
        return f"Error running code: {str(e)}"
