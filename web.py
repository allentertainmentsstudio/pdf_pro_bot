from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "🤖 PDF Pro Bot Running"

@app.route("/health")
def health():
    return "OK"
