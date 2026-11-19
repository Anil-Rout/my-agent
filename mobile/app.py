# Mobile Web App - access agent from phone browser
from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)
AGENT_URL = "http://localhost:8000"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/send", methods=["POST"])
def send():
    message = request.json.get("message", "")
    try:
        response = requests.post(f"{AGENT_URL}/chat/send", json={"content": message})
        return jsonify(response.json())
    except Exception as e:
        return jsonify({"response": f"Error: {str(e)}"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
