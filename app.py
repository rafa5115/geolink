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
# 1) GERA LINK COM PREFIXO PERSONALIZADO
# --------------------------------------------------
@app.get("/gerar/<prefixo>")
def gerar_link(prefixo):
    new_id = gerar_id()

    # Salva dados na base
    DB[new_id] = {
        "id": new_id,
        "prefixo": prefixo,
        "cliques": []
    }
    salvar_db()

    # LINK FINAL usando domínio (SEM :8080)
    link = f"https://linkio.me/{prefixo}/{new_id}"

    return jsonify({
        "status": "ok",
        "id": new_id,
        "prefixo": prefixo,
        "link": link
    })


# --------------------------------------------------
# 2) ROTA DINÂMICA PARA REGISTRAR CLIQUE
# --------------------------------------------------
@app.get("/<prefixo>/<id>")
def registrar(prefixo, id):
    if id not in DB:
        return "Link inválido", 404

    # IP real (Cloudflare + NGINX + cliente)
    ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    
    user_agent = request.headers.get("User-Agent", "desconhecido")
    now = datetime.now().isoformat()

    registro = {
        "ip": ip,
        "user_agent": user_agent,
        "datetime": now,
        "prefixo": prefixo
    }

    DB[id]["cliques"].append(registro)
    salvar_db()

    # ENVIA WEBHOOK PARA N8N
    try:
        requests.post(
            "https://n8n.teleflowbr.com/webhook-test/7aed12c8-e20a-4129-bb31-75b213949243",
            json={
                "id": id,
                "prefixo": prefixo,
                "ip": ip,
                "user_agent": user_agent,
                "datetime": now
            },
            timeout=5
        )
    except Exception as e:
        print("Erro ao enviar webhook:", e)

    return jsonify({
        "status": "clique registrado",
        "id": id,
        "prefixo": prefixo,
        "dados": registro
    })


# --------------------------------------------------
# 3) EXECUTAR SERVIDOR NA PORTA 8080
# --------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="127.0.0.1", port=8080)

