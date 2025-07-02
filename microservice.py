from werkzeug.middleware.dispatcher import DispatcherMiddleware
from waitress import serve
from app import create_flask_app
from app.soap_service import application_soap
import os
import logging

flask_app = create_flask_app()

combined_app = DispatcherMiddleware(flask_app, {
    '/soap': application_soap
})

# Make the app variable available for gunicorn
app = combined_app

def start_server():
    try:
        host = os.getenv("QWC_HOST", "localhost")
        port = int(os.getenv("QWC_PORT", 8001))
        url = f"http://{host}:{port}/home"

        logging.info(f"🚀 Iniciando servidor em {host}:{port}...\n")

        print("\n" + "=" * 60)
        print("✅ SERVIDOR INICIADO COM SUCESSO!")
        print("🌐 Acesse a interface web em:\n")
        print(f"👉  \033[1;32m{url}\033[0m")
        print("=" * 60 + "\n")

        serve(
            combined_app,
            host=host,
            port=port,
            threads=8,       # número de threads de worker
            connection_limit=100,  # máximo de conexões simultâneas
            asyncore_loop_timeout=1  # frequência do loop interno
        )

    except Exception as e:
        logging.exception("❌ Erro fatal ao iniciar o servidor")


if __name__ == "__main__":
    start_server()
