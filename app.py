from flask import Flask, jsonify
import os

app = Flask(__name__)

@app.route("/")
def home():
    return jsonify({"message": "Flask app is running!"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 1000))  # Render assigns a dynamic port
    app.run(host="0.0.0.0", port=port)

