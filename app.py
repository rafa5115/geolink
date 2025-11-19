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
    host = request.headers.get("Host", "linkio.me")
    scheme = request.headers.get("X-Forwarded-Proto", "https")
    link = f"{scheme}://{host}/{prefixo}/{new_id}"


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

    raw_ip = request.headers.get("X-Forwarded-For", request.remote_addr)

    # Sempre pega APENAS o primeiro IP real
    ip = raw_ip.split(",")[0].strip()

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

    # Envia webhook para N8N
    try:
        requests.post(
            "https://n8n.teleflowbr.com/webhook/7aed12c8-e20a-4129-bb31-75b213949243",
            json={
                "id": id,
                "prefixo": prefixo,
                "ip": ip,
                "user_agent": user_agent,
                "datetime": now
            },
            timeout=2
        )
    except:
        pass

    # Página que fecha automaticamente
    html_auto_close = """
    <html>
        <head>
            <meta charset="UTF-8" />
            <title>OK</title>
            <script>
                setTimeout(function() {
                    window.close();
                }, 200);
            </script>
        </head>
        <body style="background:#000; color:#fff;">
            <p>Registrado...</p>
        </body>
    </html>
    """

    return html_auto_close




# --------------------------------------------------
# 3) EXECUTAR SERVIDOR NA PORTA 8080
# --------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="127.0.0.1", port=8080)

