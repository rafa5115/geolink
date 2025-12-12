from flask import Flask, request, jsonify
import secrets
import string
import json
import os
from datetime import datetime
import requests

app = Flask(__name__)

DB_FILE = "data.json"

# --------------------------------------------------
# CARREGAR / SALVAR BASE
# --------------------------------------------------
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
# ROTA DE TESTE
# --------------------------------------------------
@app.get("/teste")
def testar():
    return "Rota funcionando"


# --------------------------------------------------
# 1) GERAR LINK COM PREFIXO E CRIADOR
# --------------------------------------------------
@app.get("/gerar/<prefixo>")
def gerar_link(prefixo):
    new_id = gerar_id()

    creator = request.args.get("creator")  # número do criador

    DB[new_id] = {
        "id": new_id,
        "prefixo": prefixo,
        "creator": creator,
        "cliques": [],
        "localizacoes": []
    }
    salvar_db()

    host = "clicklink.online"
    link = f"https://{host}/{prefixo}/{new_id}"

    return jsonify({
        "status": "ok",
        "id": new_id,
        "prefixo": prefixo,
        "creator": creator,
        "link": link
    })



# --------------------------------------------------
# 2) REGISTRAR CLIQUE + ENVIAR WEBHOOK + VOLTAR AO WHATSAPP
# --------------------------------------------------
@app.get("/<prefixo>/<id>")
def registrar(prefixo, id):
    if id not in DB:
        return "Link inválido", 404

    # Capturar IP real corretamente
    ip = request.headers.get("CF-Connecting-IP")
    if not ip:
        ip = request.headers.get("X-Real-IP")
    if not ip:
        ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
    if not ip:
        ip = request.remote_addr

    user_agent = request.headers.get("User-Agent", "desconhecido")
    referer = request.headers.get("Referer", None)
    now = datetime.now().isoformat()

    # Dono do link
    creator = DB[id].get("creator")

    # Registro do clique
    registro = {
        "ip": ip,
        "user_agent": user_agent,
        "datetime": now,
        "prefixo": prefixo,
        "referer": referer,
        "creator": creator
    }

    # Evitar duplicação por IP seguido
    ultimo = DB[id]["cliques"][-1] if DB[id]["cliques"] else None
    if not ultimo or ultimo["ip"] != ip:
        DB[id]["cliques"].append(registro)
        salvar_db()

    # Enviar webhook ao n8n
    try:
        requests.post(
            "http://82.25.85.25:5678/webhook/4aa565ae-6d8f-4231-8626-9512cc8f66b2",
            json={
                "id": id,
                "prefixo": prefixo,
                "ip": ip,
                "referer": referer,
                "creator": creator,
                "user_agent": user_agent,
                "datetime": now
            },
            timeout=3
        )
    except Exception as e:
        print("Erro ao enviar webhook:", e)

    # --------------------------------------------------
    # REDIRECIONAMENTO AUTOMÁTICO PARA WHATSAPP DO CRIADOR
    # --------------------------------------------------
    if creator:  # se o link tem dono, volta para o WhatsApp dele
        html_auto_close = '''
        <!DOCTYPE html>
        <html>
          <head><meta charset="UTF-8"></head>
          <body style="margin:0;padding:0;background:#fff;">
            <script>
              window.location.href = "https://google.com";
            </script>
          </body>
        </html>
        '''

    return html_auto_close


# --------------------------------------------------
# 3) EXECUTAR SERVIDOR
# --------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=8080)
