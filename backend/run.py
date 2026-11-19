# run.py — Start the backend server
# Run: python run.py

import uvicorn
from config.paths import BACKEND_DIR, ENV_FILE, ensure_runtime_dirs

if __name__ == "__main__":
    ensure_runtime_dirs()

    host = "0.0.0.0"
    port = 8000

    print("=" * 50)
    print("MY AGENT BACKEND STARTING")
    print("=" * 50)
    print(f"Backend: {BACKEND_DIR}")
    print(f"Env:     {ENV_FILE}")
    print(f"URL:     http://{host}:{port}")
    print(f"Local:   http://localhost:{port}")
    print("=" * 50)

    uvicorn.run(
        "api.main:app",
        host=host,
        port=port,
        reload=False,
    )
