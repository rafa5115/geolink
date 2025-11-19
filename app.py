from flask import Flask, jsonify
import secrets
import string

app = Flask(__name__)

def generate_id(size=6):
    chars = string.ascii_letters + string.digits
    return ''.join(secrets.choice(chars) for _ in range(size))

@app.get("/id")
def get_id():
    new_id = generate_id()
    return jsonify({"id": new_id})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
