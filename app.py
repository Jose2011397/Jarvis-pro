from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import requests
import socket
import firebase_admin
from firebase_admin import credentials, firestore

app = Flask(__name__)
CORS(app)

# Inicialização do Firebase na Render via Variáveis de Ambiente
try:
    private_key = os.environ.get("FIREBASE_PRIVATE_KEY")
    if private_key:
        private_key = private_key.replace("\\n", "\n")
        
    cred_dict = {
        "type": "service_account",
        "project_id": os.environ.get("FIREBASE_PROJECT_ID"),
        "private_key_id": os.environ.get("FIREBASE_PRIVATE_KEY_ID", ""),
        "private_key": private_key,
        "client_email": os.environ.get("FIREBASE_CLIENT_EMAIL"),
        "client_id": os.environ.get("FIREBASE_CLIENT_ID", ""),
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": os.environ.get("FIREBASE_CLIENT_X509_CERT_URL", "")
    }
    cred = credentials.Certificate(cred_dict)
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("Conectado ao Firebase Firestore na nuvem com sucesso!")
except Exception as e:
    print("Erro crítico ao inicializar o Firebase na nuvem:", e)
    db = None

PC_MAC_ADDRESS = "3C:7C:3F:7B:E9:83"

@app.route('/')
def home():
    return jsonify({"status": "online", "mensagem": "Servidor Jarvis Cloud rodando com sucesso!"})

@app.route('/api/bom-dia', methods=['GET'])
def rotina_bom_dia():
    lat, lon = -12.5, -45.7 
    url_clima = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max&current_weather=true&timezone=auto"
    
    try:
        resposta = requests.get(url_clima).json()
        temp_atual = resposta['current_weather']['temperature']
        temp_max = resposta['daily']['temperature_2m_max'][0]
        temp_min = resposta['daily']['temperature_2m_min'][0]
        chance_chuva = resposta['daily']['precipitation_probability_max'][0]

        texto = (
            f"Bom dia! A temperatura atual é de {temp_atual}°C. "
            f"Hoje teremos máxima de {temp_max}°C, mínima de {temp_min}°C "
            f"e a chance de chuva é de {chance_chuva} por cento."
        )
        return jsonify({"status": "sucesso", "mensagem": texto})
    except Exception as e:
        return jsonify({"status": "erro", "mensagem": "Não foi possível obter a previsão do tempo."}), 500

@app.route('/pc/ligar', methods=['POST'])
def ligar_pc():
    try:
        mac_limpo = PC_MAC_ADDRESS.replace('-', '').replace(':', '')
        data = bytes.fromhex('FF' * 6 + mac_limpo * 16)
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            s.sendto(data, ('255.255.255.255', 9))
        return jsonify({"status": "sucesso", "mensagem": "Pacote Wake-on-LAN enviado pela nuvem!"})
    except Exception as e:
        return jsonify({"status": "erro", "mensagem": str(e)}), 500

@app.route('/pc/comando', methods=['POST'])
def enviar_comando_pc():
    dados = request.get_json() or {}
    acao = dados.get("acao")
    parametro = dados.get("parametro", "")
    
    if db:
        try:
            db.collection("fila_comandos_pc").add({
                "acao": acao,
                "parametro": parametro,
                "status": "pendente",
                "timestamp": firestore.SERVER_TIMESTAMP
            })
            return jsonify({"status": "sucesso", "mensagem": f"Comando '{acao}' enviado para a fila do PC."})
        except Exception as e:
            return jsonify({"status": "erro", "mensagem": str(e)}), 500
    return jsonify({"status": "erro", "mensagem": "Base de dados indisponível."}), 500

@app.route('/pc/apps', methods=['GET'])
def listar_apps():
    apps_comuns = [
        {"nome": "Google Chrome", "comando": "chrome"},
        {"nome": "Spotify", "comando": "spotify"},
        {"nome": "Bloco de Notas", "comando": "notepad"},
        {"nome": "Calculadora", "comando": "calc"},
        {"nome": "Explorador de Arquivos", "comando": "explorer"},
        {"nome": "Prompt de Comando", "comando": "cmd"},
        {"nome": "Visual Studio Code", "comando": "code"}
    ]
    return jsonify(apps_comuns)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
