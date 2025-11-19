from flask import Flask, request, jsonify
import secrets
import string
import json
import os
from datetime import datetime

app = Flask(__name__)

DB_FILE = "data.json"

# Carregar base
if os.path.exists(DB_FILE):
    with open(DB_FILE, "r") as f:
        DB = json.load(f)
else:
    DB = {}

def salvar_db():
    with open(DB_FILE, "w") as f:
        json.dump(DB, f, indent=2)

def gerar_id(tamanho=6):
    chars = string.ascii_letters + string.digits
    return ''.join(secrets.choice(chars) for _ in range(tamanho))

# Rota para gerar link
@app.get("/gerar")
def gerar_link():
    new_id = gerar_id()
    DB[new_id] = {
        "id": new_id,
        "cliques": []
    }
    salvar_db()

    link = f"http://82.25.85.25:8080/r/{new_id}"

    return jsonify({
        "status": "ok",
        "id": new_id,
        "link": link
    })

# Rota para registrar clique
@app.get("/r/<id>")
def registrar(id):
    if id not in DB:
        return "Link inválido", 404

    ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    user_agent = request.headers.get("User-Agent", "desconhecido")

    registro = {
        "ip": ip,
        "user_agent": user_agent,
        "datetime": datetime.now().isoformat()
    }

    DB[id]["cliques"].append(registro)
    salvar_db()

    return jsonify({
        "status": "clique registrado",
        "id": id,
        "dados": registro
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
