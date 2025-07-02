from collections import deque
import json
from app.qb_state import ordersQueue

# ordersQueue = {}
invoices_queue = {}
qb_request_queue = deque()
pending_iterators = deque()

def parse_items(items):
    parsed_items = []
    for index, item in enumerate(items):
        try:
            if isinstance(item, str):
                item = json.loads(item.strip())
            if isinstance(item, list) and len(item) >= 4:
                for i in range(0, len(item), 4):
                    description = item[i] if i < len(item) and item[i] else "N/A"
                    productid = item[i + 1] if i + 1 < len(item) and item[i + 1] else "N/A"
                    try:
                        price = f"{float(item[i + 2]) if item[i + 2] else 0:.2f}"
                    except Exception:
                        price = "0.00"
                    try:
                        quantity = int(item[i + 3]) if item[i + 3] else 0
                    except Exception:
                        quantity = 0
                    parsed_items.append({
                        "description": description,
                        "productid": productid,
                        "price": price,
                        "quantity": quantity
                    })
        except Exception as e:
            print(f"⚠️ Error al parsear JSON de items: {item}, {str(e)}")
    return parsed_items
