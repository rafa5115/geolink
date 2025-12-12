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
#  CARREGAR / SALVAR BASE
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
#  ROTA DE TESTE
# --------------------------------------------------
@app.get("/teste")
def testar():
    return "Rota funcionando"


# --------------------------------------------------
#  1) GERAR LINK COM PREFIXO PERSONALIZADO
# --------------------------------------------------
@app.get("/gerar/<prefixo>")
def gerar_link(prefixo):
    new_id = gerar_id()

    # Criar estrutura de dados
    DB[new_id] = {
        "id": new_id,
        "prefixo": prefixo,
        "cliques": []
    }
    salvar_db()

    # Montar link final usando domínio real
    host = "clicklink.online"
    link = f"https://{host}/{prefixo}/{new_id}"

    return jsonify({
        "status": "ok",
        "id": new_id,
        "prefixo": prefixo,
        "link": link
    })


# --------------------------------------------------
#  2) ROTA DINÂMICA PARA REGISTRAR CLIQUE
# --------------------------------------------------
@app.get("/<prefixo>/<id>")
def registrar(prefixo, id):
    if id not in DB:
        return "Link inválido", 404

    # Capturar IP real
    raw_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    ip = raw_ip.split(",")[0].strip()

    user_agent = request.headers.get("User-Agent", "desconhecido")
    now = datetime.now().isoformat()

    registro = {
        "ip": ip,
        "user_agent": user_agent,
        "datetime": now,
        "prefixo": prefixo
    }

    # Evitar registrar múltiplas vezes o mesmo IP
    if len(DB[id]["cliques"]) == 0 or DB[id]["cliques"][-1]["ip"] != ip:
        DB[id]["cliques"].append(registro)
        salvar_db()

    # Envia webhook para n8n
    try:
        requests.post(
            "http://82.25.85.25:5678/webhook-test/4aa565ae-6d8f-4231-8626-9512cc8f66b2",
            json={
                "id": id,
                "prefixo": prefixo,
                "ip": ip,
                "user_agent": user_agent,
                "datetime": now
            },
            timeout=2
        )
    except Exception as e:
        print("Erro ao enviar webhook:", e)

    # Página invisível + saída imediata
    html_auto_close = """
    <!DOCTYPE html>
    <html>
      <head><meta charset="UTF-8" /></head>
      <body style="margin:0;padding:0;background:#000;">
        <script>
          setTimeout(() => { 
            window.location.replace("https://google.com"); 
          }, 10);
        </script>
      </body>
    </html>
    """

    return html_auto_close


# --------------------------------------------------
#  3) EXECUTAR SERVIDOR NA PORTA 8080
# --------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=8080)
