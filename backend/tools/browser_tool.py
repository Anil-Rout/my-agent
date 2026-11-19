# browser_tool.py — Browser control and web search
# Both browser automation and search in one file

import os
import requests
import webbrowser
import subprocess
from tools.app_tool import _force_window_to_front

# ─────────────────────────────────────────
# WEB SEARCH — No API key needed
# ─────────────────────────────────────────

def search_web(query: str) -> str:
    """Search web using DuckDuckGo — no API key needed"""
    try:
        url = "https://api.duckduckgo.com/"
        params = {
            "q": query,
            "format": "json",
            "no_html": "1",
            "skip_disambig": "1"
        }
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        results = []

        if data.get("Answer"):
            results.append(f"💡 Answer: {data['Answer']}")

        if data.get("Abstract"):
            results.append(f"📌 Summary:\n{data['Abstract']}")

        if data.get("RelatedTopics"):
            results.append("\n🔍 Related:")
            for topic in data["RelatedTopics"][:5]:
                if "Text" in topic:
                    results.append(f"  • {topic['Text']}")

        if not results:
            return f"No results found for: {query}"

        return "\n".join(results)

    except Exception as e:
        return f"❌ Search error: {str(e)}"

def get_weather(city: str) -> str:
    """Get weather for any city — no API key needed"""
    try:
        url = f"https://wttr.in/{city}?format=3"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            return f"🌤️ {r.text.strip()}"
        return f"❌ Could not get weather for {city}"
    except Exception as e:
        return f"❌ Error: {str(e)}"

def get_news(topic: str) -> str:
    """Get latest news on any topic"""
    try:
        url = "https://api.duckduckgo.com/"
        params = {"q": f"{topic} news", "format": "json", "no_html": "1"}
        r = requests.get(url, params=params, timeout=10)
        data = r.json()
        results = [f"📰 News: {topic}\n"]
        if data.get("RelatedTopics"):
            for item in data["RelatedTopics"][:8]:
                if "Text" in item:
                    results.append(f"  • {item['Text']}")
        if len(results) == 1:
            return f"No news found for: {topic}"
        return "\n".join(results)
    except Exception as e:
        return f"❌ Error: {str(e)}"

def calculate(expression: str) -> str:
    """Calculate math expression safely using ast"""
    import ast
    import operator

    allowed_operators = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
    }

    def _eval(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in allowed_operators:
            return allowed_operators[type(node.op)](_eval(node.left), _eval(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in allowed_operators:
            return allowed_operators[type(node.op)](_eval(node.operand))
        raise ValueError(f"Unsupported operation: {ast.dump(node)}")

    try:
        tree = ast.parse(expression.strip(), mode="eval")
        result = _eval(tree.body)
        return f"✅ {expression} = {result}"
    except ZeroDivisionError:
        return "❌ Error: division by zero"
    except Exception:
        return "❌ Invalid expression — only numbers and basic operators ( + - * / % ** ) are supported"

def get_current_time() -> str:
    """Get current date and time"""
    from datetime import datetime
    now = datetime.now()
    return f"🕐 {now.strftime('%A, %d %B %Y — %I:%M %p')}"

# ─────────────────────────────────────────
# BROWSER CONTROL
# ─────────────────────────────────────────

def open_website(url: str) -> str:
    """Open any website in default browser and bring to front"""
    try:
        if not url.startswith("http"):
            url = "https://" + url
        os.system(f'start "" "{url}"')
        _force_window_to_front("Chrome", wait=2.0)
        return f"✅ Opened: {url}"
    except Exception as e:
        return f"❌ Error: {str(e)}"

def search_google(query: str) -> str:
    """Open Google search in browser and bring to front"""
    try:
        url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        os.system(f'start "" "{url}"')
        _force_window_to_front("Chrome", wait=2.0)
        return f"✅ Searching Google for: {query}"
    except Exception as e:
        return f"❌ Error: {str(e)}"

def search_youtube(query: str) -> str:
    """Search YouTube in browser and bring to front"""
    try:
        url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
        os.system(f'start "" "{url}"')
        _force_window_to_front("YouTube", wait=2.5)
        return f"✅ Searching YouTube for: {query}"
    except Exception as e:
        return f"❌ Error: {str(e)}"

def open_github(repo: str = "") -> str:
    """Open GitHub"""
    try:
        url = f"https://github.com/{repo}" if repo else "https://github.com"
        webbrowser.open(url)
        return f"✅ Opened GitHub: {url}"
    except Exception as e:
        return f"❌ Error: {str(e)}"