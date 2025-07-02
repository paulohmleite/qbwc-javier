import os
import subprocess
import time
import requests
from pathlib import Path
import sys

# CONFIGURAÇÕES
MICROSERVICE_DIR = r"C:\Users\jimacuser\microservice"
NGROK_PATH = r"C:\Users\jimacuser\ngrok\ngrok.exe"
PYTHON_EXEC = os.path.join(MICROSERVICE_DIR, "venv", "Scripts", "python.exe")
MICROSERVICE_SCRIPT = os.path.join(MICROSERVICE_DIR, "microservice.py")

def run_microservice():
    print("🚀 Iniciando microserviço...")
    subprocess.Popen([PYTHON_EXEC, MICROSERVICE_SCRIPT], cwd=MICROSERVICE_DIR)

def run_ngrok():
    print("🌐 Iniciando ngrok...")
    subprocess.Popen([NGROK_PATH, "http", "8001"], cwd=MICROSERVICE_DIR)
    time.sleep(8)  # Aguarda ngrok iniciar

def get_ngrok_url():
    try:
        response = requests.get("http://127.0.0.1:4040/api/tunnels")
        data = response.json()
        url = data["tunnels"][0]["public_url"]
        print(f"🌍 URL pública do ngrok: {url}")
        return url
    except Exception as e:
        print(f"❌ Erro ao obter URL do ngrok: {e}")
        return None

if __name__ == "__main__":
    os.chdir(MICROSERVICE_DIR)

    run_microservice()
    run_ngrok()

    ngrok_url = get_ngrok_url()
    if ngrok_url:
        print(f"\n✅ Microserviço acessível em: {ngrok_url}/home\n")
    else:
        print("⚠️ Não foi possível obter a URL do ngrok.")
