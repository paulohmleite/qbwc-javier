# app/routes.py
from flask import Blueprint, request, jsonify, render_template
import logging
import os
import json
from functools import wraps
import jwt
from datetime import datetime, timedelta

from xml.queries import sync_all_xml, sync_customers, sync_customers_and_items, sync_invoices, sync_item_inventory, sync_orders, sync_price_level, sync_stock_sites
from .queues import ordersQueue, parse_items
from .soap_service import qb_request_queue
from app.qb_state import pending_iterators, collected_products, collected_customers, collected_invoices, collected_stock_sites, collected_sales_orders, collected_pricelevels

# Secret key for JWT - should be in environment variables in production
SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-secret-key-here')

routes = Blueprint('routes', __name__)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # Check if token is in headers
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]  # Get token from "Bearer <token>"
            except IndexError:
                return jsonify({'message': 'Invalid token format'}), 401

        if not token:
            return jsonify({'message': 'Token is missing'}), 401

        try:
            # Verify token
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            # You can add additional checks here if needed
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token'}), 401

        return f(*args, **kwargs)
    return decorated

@routes.route('/home')
def home():
    return render_template('index.html')

@routes.route('/send-request', methods=['POST'])
def send_qb_request():
    try:
        action = request.json.get("action")
        logging.info(f"Action received: {action}")
        if action == "sync_all":
            collected_customers.clear()
            collected_products.clear()
            collected_stock_sites.clear()
            collected_invoices.clear()

            pending_iterators.appendleft({
                "type": "InvoiceQueryRq",
                "iterator": "Start",
                "iterator_id": None
            })
            pending_iterators.appendleft({
                "type": "ItemSitesQueryRq",
                "iterator": "Start",
                "iterator_id": None
            })
            pending_iterators.appendleft({
                "type": "ItemInventoryQueryRq",
                "iterator": "Start",
                "iterator_id": None
            })
            pending_iterators.appendleft({
                "type": "CustomerQueryRq",
                "iterator": "Start",
                "iterator_id": None
            })
            return jsonify({"message": "SYNC ALL was initiated via iterator!"})

        if action == "sync_customers_and_items":
            collected_customers.clear()
            collected_products.clear()

            pending_iterators.appendleft({
                "type": "ItemInventoryQueryRq",
                "iterator": "Start",
                "iterator_id": None
            })
            pending_iterators.appendleft({
                "type": "CustomerQueryRq",
                "iterator": "Start",
                "iterator_id": None
            })

            logging.info("SYNC CUSTOMERS AND ITEMS was initiated: both iterators enqueued.")
            return jsonify({"message": "SYNC CUSTOMERS AND ITEMS was initiated via iterator!"})

        if action == "sync_invoices":
            collected_invoices.clear()

            pending_iterators.appendleft({
                "type": "InvoiceQueryRq",
                "iterator": "Start",
                "iterator_id": None
            })

            logging.info("SYNC INVOICES iterator START added to pending_iterators")
            return jsonify({"message": "SYNC INVOICES was initiated via iterator!"})

        if action == "sync_customers":
            collected_customers.clear()

            # Adiciona o iterator para CustomerQuery
            pending_iterators.appendleft({
                "type": "CustomerQueryRq",
                "iterator": "Start",
                "iterator_id": None
            })

            logging.info("SYNC CUSTOMERS iterator START added to pending_iterators")
            return jsonify({"message": "SYNC CUSTOMERS was initiated via iterator!"})

        if action == "sync_inventory":
            collected_products.clear()

            pending_iterators.appendleft({
                "type": "ItemInventoryQueryRq",
                "iterator": "Start",
                "iterator_id": None
            })

            logging.info("SYNC PRODUCTS (ItemInventory) iterator START added to pending_iterators")
            return jsonify({"message": "SYNC PRODUCTS was initiated via iterator!"})

        if action == "sync_stock_sites":
            sync_stock_sites()
            logging.info("SYNC STOCK SITES iterator START added to pending_iterators")
            return jsonify({"message": "SYNC STOCK SITES iterator was initiated!"})

        if action == "sync_orders":
            collected_sales_orders.clear()

            pending_iterators.appendleft({
                "type": "SalesOrderQueryRq",
                "iterator": "Start",
                "iterator_id": None
            })

            logging.info("SYNC SALES ORDERS iterator START added to pending_iterators")
            return jsonify({"message": "SYNC SALES ORDERS was initiated via iterator!"})

        if action == "sync_price_level":
            collected_pricelevels.clear()

            qb_request_queue.append("""<?xml version="1.0"?>
                <?qbxml version="13.0"?>
                <QBXML>
                <QBXMLMsgsRq onError="stopOnError">
                <PriceLevelQueryRq>
                </PriceLevelQueryRq>
                </QBXMLMsgsRq>
                </QBXML>""")

            logging.info("SYNC PRICE LEVEL enqueued (without iterator)")
            return jsonify({"message": "SYNC PRICE LEVEL was initiated!"})

        return jsonify({"message": "Invalid action"}), 400

    except Exception as e:
        logging.error(f"Error processing request: {str(e)}")
        return jsonify({"message": "Internal Server Error", "error": str(e)}), 500

@routes.route("/create-order", methods=["POST"])
def create_order():
    print("📥 Recibida orden de venta desde Bubble:")
    try:
        if not request.data:
            return jsonify({"message": "❌ Cuerpo de la solicitud vacío."}), 400

        try:
            body = request.get_json(force=True)
        except Exception as e:
            return jsonify({"message": "❌ Cuerpo de la solicitud inválido.", "error": str(e)}), 400

        if not all(key in body for key in ["orderId", "customerName", "items", "totalAmount"]):
            return jsonify({"message": "❌ Datos de la orden incompletos."}), 400

        orderId = body["orderId"]
        customerName = body["customerName"].split(",")[0].strip()

        if orderId not in ordersQueue or ordersQueue[orderId].get("status") != "sent":
            ordersQueue[orderId] = {
                "orderId": orderId,
                "customerName": customerName,
                "totalAmount": f"{float(body['totalAmount'].replace(',', '.')):.2f}",
                "items": parse_items(body["items"]),
                "status": "pending"
            }

            logging.info(f"📌 Pedido {orderId} armazenado na fila de sincronização.")
            print(f"📌 XML da ordem {orderId} adicionado à fila para o QuickBooks.")

        print("✅ Orden almacenada para QuickBooks:")
        print(f"🔹 Order ID: {orderId}")
        print(f"🔹 Cliente: {customerName}")
        print(f"🔹 Total Amount: ${body['totalAmount']}")
        print("🔹 Items:")
        for item in ordersQueue[orderId]["items"]:
            print(item)

        return jsonify({
            "message": "✅ Orden recibida correctamente.",
            "order": ordersQueue[orderId]
        }), 200

    except Exception as e:
        print("❌ Error procesando la solicitud:", str(e))
        return jsonify({"message": "❌ Error interno en el servidor.", "error": str(e)}), 500


def read_json_file(filepath):
    if not os.path.exists(filepath):
        return jsonify({"message": "Arquivo não encontrado."}), 404
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return jsonify(data), 200
    except Exception as e:
        return jsonify({"message": "Erro ao ler o arquivo.", "error": str(e)}), 500

@routes.route('/item-inventory', methods=["GET"])
#@token_required
def get_item_inventory():
    return read_json_file("data/item_inventory.json")

@routes.route('/invoices', methods=["GET"])
#@token_required
def get_invoices():
    return read_json_file("data/invoices.json")

@routes.route('/customers', methods=["GET"])
#@token_required
def get_customers():
    return read_json_file("data/customers.json")

@routes.route('/stock-sites', methods=["GET"])
#@token_required
def get_stock_sites():
    return read_json_file("data/stock_per_site.json")

@routes.route('/orders', methods=["GET"])
#@token_required
def get_orders():
    return read_json_file("data/sales_orders.json")

@routes.route('/pricelevels', methods=["GET"])
#@token_required
def get_pricelevels():
    return read_json_file("data/price_levels.json")

@routes.route('/login', methods=['POST'])
def login():
    auth = request.json

    if not auth or not auth.get('username') or not auth.get('password'):
        return jsonify({'message': 'Could not verify', 'WWW-Authenticate': 'Basic realm="Login required!"'}), 401

    # In production, you should validate against a database
    # This is just an example
    if auth.get('username') == 'admin' and auth.get('password') == 'admin':
        token = jwt.encode({
            'user': auth.get('username')
        }, SECRET_KEY)

        return jsonify({'token': token})

    return jsonify({'message': 'Could not verify', 'WWW-Authenticate': 'Basic realm="Login required!"'}), 401