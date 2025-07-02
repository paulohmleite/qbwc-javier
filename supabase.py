import json
import requests
import os

SUPABASE_URL = "https://ojybvaboxesqiutohbgw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9qeWJ2YWJveGVzcWl1dG9oYmd3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDczOTA1OTMsImV4cCI6MjA2Mjk2NjU5M30.2cocq1cpXIin5YYIPAf6Xw8JaokDV-DPV1mB53EZGQk"

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

def fetch_all_rows(table, select_fields):
    all_rows = []
    limit = 1000
    offset = 0
    while True:
        url = f"{SUPABASE_URL}/rest/v1/{table}?select={select_fields}&limit={limit}&offset={offset}"
        resp = requests.get(url, headers=HEADERS)
        if resp.status_code == 200:
            rows = resp.json()
            all_rows.extend(rows)
            if len(rows) < limit:
                break
            offset += limit
        else:
            print(f"Error fetching {table}: {resp.text}")
            break
    return {row[list(row.keys())[0]]: row for row in all_rows}  # Use first field as key

def compare_and_split(records, existing_dict, key_field, fields_to_check=None):
    to_insert = []
    to_update = []
    for record in records:
        key = record[key_field]
        existing = existing_dict.get(key)
        if not existing:
            to_insert.append(record)
        else:
            changed = False
            for k in (fields_to_check if fields_to_check else record):
                v1 = record.get(k)
                v2 = existing.get(k)
                if v1 != v2 and not (v1 in (None, "") and v2 in (None, "")):
                    changed = True
                    break
            if changed:
                to_update.append(record)
    return to_insert, to_update

def bulk_insert(table, records):
    if records:
        url = f"{SUPABASE_URL}/rest/v1/{table}"
        resp = requests.post(url, headers=HEADERS, data=json.dumps(records))
        if resp.status_code in (201, 200):
            print(f"Inserted {len(records)} new records into {table}.")
        else:
            print(f"Failed to insert new records into {table}: {resp.text}")
    else:
        print(f"No new records to insert into {table}.")

def patch_update(table, records, key_field):
    updated_count = 0
    for record in records:
        patch_url = f"{SUPABASE_URL}/rest/v1/{table}?{key_field}=eq.{record[key_field]}"
        resp = requests.patch(patch_url, headers=HEADERS, data=json.dumps(record))
        if resp.status_code in (200, 204):
            updated_count += 1
        else:
            print(f"Failed to update {table} {record[key_field]}: {resp.text}")
    if updated_count:
        print(f"Updated {updated_count} records in {table}.")
    else:
        print(f"No records to update in {table}.")

def upsert_stocks(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"Loaded {len(data)} stock records from {json_path}")
    # Prepare records for stocks table
    records = [
        {"productlistid": item["ProductListId"], "quantity": item["Quantity"]}
        for item in data
    ]
    existing_dict = fetch_all_rows("stocks", "productlistid,quantity")
    to_insert, to_update = compare_and_split(records, existing_dict, "productlistid", fields_to_check=["quantity"])
    bulk_insert("stocks", to_insert)
    patch_update("stocks", to_update, "productlistid")
    return set(item["productlistid"] for item in records)

def upsert_items(json_path, valid_listids):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"Loaded {len(data)} item records from {json_path}")
    # Only insert items whose listid exists in stocks
    records = [
        {
            "listid": item["ListID"],
            "name": item.get("Name"),
            "salesprice": item.get("SalesPrice"),
            "description": item.get("Description"),
            "brand": item.get("Brand"),
            "category": item.get("Category")
        }
        for item in data if item["ListID"] in valid_listids
    ]
    existing_dict = fetch_all_rows("items", "listid,name,salesprice,description,brand,category")
    to_insert, to_update = compare_and_split(
        records, existing_dict, "listid",
        fields_to_check=["name", "salesprice", "description", "brand", "category"]
    )
    bulk_insert("items", to_insert)
    patch_update("items", to_update, "listid")

def upsert_customers(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"Loaded {len(data)} customer records from {json_path}")
    records = []
    for item in data:
        record = {
            "qbid": item["QBId"],
            "customername": item.get("CustomerName"),
            "fullname": item.get("FullName"),
            "email": item.get("Email"),
            "balance": float(item["Balance"]) if item.get("Balance") not in (None, "") else 0.0,
            "totalbalance": float(item["TotalBalance"]) if item.get("TotalBalance") not in (None, "") else 0.0,
            "mainphone": item.get("MainPhone"),
            "creditlimit": float(item["CreditLimit"]) if item.get("CreditLimit") not in (None, "") else None,
            "address": item.get("Address"),
            "term": item.get("Term"),
        }
        records.append(record)
    existing_dict = fetch_all_rows("customers", "qbid,customername,fullname,email,balance,totalbalance,mainphone,creditlimit,address,term")
    to_insert, to_update = compare_and_split(
        records, existing_dict, "qbid",
        fields_to_check=["customername", "fullname", "email", "balance", "totalbalance", "mainphone", "creditlimit", "address", "term"]
    )
    bulk_insert("customers", to_insert)
    patch_update("customers", to_update, "qbid")

def upsert_invoices(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"Loaded {len(data)} invoice records from {json_path}")
    records = []
    for item in data:
        record = {
            "txnid": item["TxnID"],
            "qbid": item.get("QBId"),
            "customerfullname": item.get("CustomerFullName"),
            "txndate": item.get("TxnDate"),
            "refnumber": item.get("RefNumber"),
            "subtotal": float(item["Subtotal"]) if item.get("Subtotal") not in (None, "") else 0.0,
            "balanceremaining": float(item["BalanceRemaining"]) if item.get("BalanceRemaining") not in (None, "") else 0.0,
        }
        records.append(record)
    existing_dict = fetch_all_rows("invoices", "txnid,qbid,customerfullname,txndate,refnumber,subtotal,balanceremaining")
    to_insert, to_update = compare_and_split(
        records, existing_dict, "txnid",
        fields_to_check=["qbid", "customerfullname", "txndate", "refnumber", "subtotal", "balanceremaining"]
    )
    bulk_insert("invoices", to_insert)
    patch_update("invoices", to_update, "txnid")
    return {item["TxnID"] for item in data}

def upsert_invoice_lineitems(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"Loaded {len(data)} invoice records for line items from {json_path}")
    records = []
    for item in data:
        txnid = item["TxnID"]
        for li in item.get("LineItems", []):
            record = {
                "txnlineid": li["TxnLineID"],
                "invoice_txnid": txnid,
                "itemfullname": li.get("ItemFullName"),
                "description": li.get("Desc"),
                "quantity": float(li["Quantity"]) if li.get("Quantity") not in (None, "") else 0.0,
                "unitofmeasure": li.get("UnitOfMeasure"),
                "rate": float(li["Rate"]) if li.get("Rate") not in (None, "") else 0.0,
                "amount": float(li["Amount"]) if li.get("Amount") not in (None, "") else 0.0,
            }
            records.append(record)
    existing_dict = fetch_all_rows("invoice_lineitems", "txnlineid,invoice_txnid,itemfullname,description,quantity,unitofmeasure,rate,amount")
    to_insert, to_update = compare_and_split(
        records, existing_dict, "txnlineid",
        fields_to_check=["invoice_txnid", "itemfullname", "description", "quantity", "unitofmeasure", "rate", "amount"]
    )
    bulk_insert("invoice_lineitems", to_insert)
    patch_update("invoice_lineitems", to_update, "txnlineid")

def upsert_sales_orders(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"Loaded {len(data)} sales order records from {json_path}")
    records = []
    for item in data:
        record = {
            "txnid": item["TxnID"],
            "refnumber": item.get("RefNumber"),
            "customername": item.get("CustomerName"),
            "txndate": item.get("TxnDate"),
            "subtotal": float(item["Subtotal"]) if item.get("Subtotal") not in (None, "") else 0.0,
            "totalamount": float(item["TotalAmount"]) if item.get("TotalAmount") not in (None, "") else 0.0,
            "salesrepname": item.get("SalesRepName"),
            "isfullyinvoiced": item.get("IsFullyInvoiced"),
            "memo": item.get("Memo"),
        }
        records.append(record)
    existing_dict = fetch_all_rows("sales_orders", "txnid,refnumber,customername,txndate,subtotal,totalamount,salesrepname,isfullyinvoiced,memo")
    to_insert, to_update = compare_and_split(
        records, existing_dict, "txnid",
        fields_to_check=["refnumber", "customername", "txndate", "subtotal", "totalamount", "salesrepname", "isfullyinvoiced", "memo"]
    )
    bulk_insert("sales_orders", to_insert)
    patch_update("sales_orders", to_update, "txnid")
    return {item["TxnID"] for item in data}

def upsert_sales_order_lineitems(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"Loaded {len(data)} sales order line items from {json_path}")
    records = []
    for item in data:
        record = {
            "txnlineid": item["TxnLineID"],
            "sales_order_txnid": item.get("SalesOrder_TxnID"),
            "itemfullname": item.get("ItemFullName"),
            "description": item.get("Description"),
            "quantity": float(item["Quantity"]) if item.get("Quantity") not in (None, "") else 0.0,
            "rate": float(item["Rate"]) if item.get("Rate") not in (None, "") else 0.0,
            "amount": float(item["Amount"]) if item.get("Amount") not in (None, "") else 0.0,
        }
        records.append(record)
    existing_dict = fetch_all_rows("sales_order_lineitems", "txnlineid,sales_order_txnid,itemfullname,description,quantity,rate,amount")
    to_insert, to_update = compare_and_split(
        records, existing_dict, "txnlineid",
        fields_to_check=["sales_order_txnid", "itemfullname", "description", "quantity", "rate", "amount"]
    )
    bulk_insert("sales_order_lineitems", to_insert)
    patch_update("sales_order_lineitems", to_update, "txnlineid")

def main():
    # Upsert stocks first, then items
    valid_listids = upsert_stocks("data/filter_stocks.json")
    upsert_items("data/filter_items.json", valid_listids)
    upsert_customers("data/filter_customers.json")
    upsert_invoices("data/filter_invoices.json")
    upsert_invoice_lineitems("data/filter_invoices.json")
    upsert_sales_orders("data/filter_sales_orders.json")
    upsert_sales_order_lineitems("data/filter_sales_order_lineitems.json")

if __name__ == "__main__":
    main()



# venv\Scripts\activate.bat