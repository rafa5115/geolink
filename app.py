from flask import Flask, request, jsonify
import secrets
import string
import json
import os
from datetime import datetime
import requests

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


# --------------------------------------------------
# 1) ROTA PARA GERAR LINK
# --------------------------------------------------
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


# --------------------------------------------------
# 2) ROTA PARA REGISTRAR CLIQUE + ENVIAR PARA N8N
# --------------------------------------------------
@app.get("/r/<id>")
def registrar(id):
    if id not in DB:
        return "Link inválido", 404

    ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    user_agent = request.headers.get("User-Agent", "desconhecido")
    now = datetime.now().isoformat()

    registro = {
        "ip": ip,
        "user_agent": user_agent,
        "datetime": now
    }

    DB[id]["cliques"].append(registro)
    salvar_db()

    # ---------------------------------------------
    # ENVIAR AUTOMATICAMENTE PARA O N8N
    # ---------------------------------------------
    try:
        requests.post(
            "https://n8n.teleflowbr.com/webhook-test/7aed12c8-e20a-4129-bb31-75b213949243",
            json={
                "id": id,
                "ip": ip,
                "user_agent": user_agent,
                "datetime": now
            },
            timeout=5
        )
    except Exception as e:
        print("Erro ao chamar o webhook:", e)

    return jsonify({
        "status": "clique registrado",
        "id": id,
        "dados": registro
    })


# --------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
