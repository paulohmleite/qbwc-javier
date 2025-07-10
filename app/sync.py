# app/sync.py
import json
import logging
import os
import time
from datetime import datetime
from .queues import ordersQueue, parse_items
import time
import logging
from dotenv import load_dotenv
from .utils import (
    collected_customers,
    collected_products,
    collected_stock_sites,
    collected_invoices,
    pending_iterators,
)

load_dotenv()

OTHERS_SYNC_TIME_IN_SEC = int(os.getenv("OTHERS_SYNC_TIME_IN_SEC", 3600)) # 1 hour
ORDERS_SYNC_TIME_IN_SEC = int(os.getenv("ORDERS_SYNC_TIME_IN_SEC", 300)) # 5 minutes

def sync_new_orders():
    logging.info(f"🔄 Orders sync time: {ORDERS_SYNC_TIME_IN_SEC} seconds")
    while True:
        print("🔄 Starting synchronization of new orders...")
        try:
            path = "data/new_orders.json"
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                if data:
                    logging.info("🔄 Synchronizing new orders...")
                    logging.info(f"🔍 Found {len(data)} new orders to synchronize.")
                    for body in data:
                        print(body)
                        if not all(k in body for k in ["orderId", "customerName", "items", "totalAmount"]):
                            print(f"⚠️ Incomplete order: {body}")
                            continue

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

                            logging.info(f"📌 Order {orderId} stored in the queue.")
                            print(f"✅ Order {orderId} added to the QuickBooks queue.")

                    with open(path, "w", encoding="utf-8") as f:
                        json.dump([], f, indent=2)

        except Exception as e:
            logging.error("❌ Error during synchronization of new orders.", exc_info=True)

        time.sleep(ORDERS_SYNC_TIME_IN_SEC)

def sync_others():
    logging.info(f"🔄 Others sync time: {OTHERS_SYNC_TIME_IN_SEC} seconds")
    while True:
        try:
            logging.info(f"⏳ Starting full sync at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

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
            pending_iterators.appendleft({
                "type": "SalesOrderQueryRq",
                "iterator": "Start",
                "iterator_id": None
            })

            logging.info(f"✅ Sync finished at {datetime.now().strftime('%H:%M:%S')}")

            logging.info(f"📊 Now we just need to wait the response from QB.")

        except Exception as e:
            logging.error("❌ Error during synchronization of customers, invoices, etc.", exc_info=True)

        time.sleep(OTHERS_SYNC_TIME_IN_SEC)
