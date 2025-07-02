from flask import Flask

from app.sync import sync_new_orders, sync_others
from .routes import routes
import threading

def create_flask_app():
    app = Flask(__name__, template_folder='../templates',)
    app.register_blueprint(routes)

    # Start automatic synchronization thread
    threading.Thread(target=sync_new_orders, daemon=True).start()

    # Start the automatic synchronization of customers, invoices, etc.
    threading.Thread(target=sync_others, daemon=True).start()

    return app
