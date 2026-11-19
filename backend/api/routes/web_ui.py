from pathlib import Path
from fastapi import APIRouter
from fastapi.responses import HTMLResponse, Response

router = APIRouter()

_UI_PATH = Path(__file__).resolve().parent.parent.parent / "static" / "ui.html"


def _no_cache_html(content: str) -> Response:
    return Response(
        content=content,
        media_type="text/html",
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )


@router.get("/ui", include_in_schema=False)
def serve_ui():
    if not _UI_PATH.exists():
        return HTMLResponse(content=f"<pre>Not found: {_UI_PATH}</pre>", status_code=404)
    return _no_cache_html(_UI_PATH.read_text(encoding="utf-8"))


@router.get("/ui/reset", include_in_schema=False)
def reset_ui():
    return _no_cache_html("""<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Resetting...</title>
<style>
body{background:#0D1117;color:#E6EDF3;font-family:sans-serif;
display:flex;align-items:center;justify-content:center;
height:100vh;margin:0;flex-direction:column;gap:16px;font-size:16px}
</style>
</head><body>
<p>Clearing session...</p>
<script>
localStorage.clear();
sessionStorage.clear();
document.cookie.split(';').forEach(function(c){
  document.cookie=c.replace(/^ +/,'').replace(/=.*/,'=;expires='+new Date().toUTCString()+';path=/');
});
setTimeout(function(){ window.location.replace('/ui'); }, 500);
</script>
</body></html>""")