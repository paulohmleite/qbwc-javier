import json
import requests
import time
import os
import uuid

SUPABASE_URL = "https://ojybvaboxesqiutohbgw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9qeWJ2YWJveGVzcWl1dG9oYmd3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDczOTA1OTMsImV4cCI6MjA2Mjk2NjU5M30.2cocq1cpXIin5YYIPAf6Xw8JaokDV-DPV1mB53EZGQk"

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

# venv\Scripts\activate.bat

def get_existing_qbids():
    url = f"{SUPABASE_URL}/rest/v1/customers?select=qbid"
    resp = requests.get(url, headers=HEADERS)
    if resp.status_code == 200:
        return set(row['qbid'] for row in resp.json())
    else:
        print(f"Error fetching existing qbids: {resp.text}")
        return set()

def get_existing_customers_dict():
    url = f"{SUPABASE_URL}/rest/v1/customers"
    resp = requests.get(url, headers=HEADERS)
    if resp.status_code == 200:
        return {row['qbid']: row for row in resp.json()}
    else:
        print(f"Error fetching existing customers: {resp.text}")
        return {}

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

def compare_and_split(records, existing_dict, key_field):
    to_insert = []
    to_update = []
    for record in records:
        key = record[key_field]
        existing = existing_dict.get(key)
        if not existing:
            to_insert.append(record)
        else:
            changed = False
            for k in record:
                v1 = record[k]
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

def upsert_from_json(json_path, table, key_field, field_map):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    items = data.get('result', [])
    print(f"Loaded {len(items)} records from {json_path}")

    # Filter for Maracay if stock_per_site and keep only productlistid and quantity
    if table == "stock_per_site":
        items = [item for item in items if item.get("InventorySiteFullName") == "Maracay"]
        ex = [item for item in items if item.get("ProductListId") and item.get("ProductFullName")]
        # Only keep productlistid and quantity
        items = [{"ProductListId": item["ProductListId"], "Quantity": item["Quantity"]} for item in items]
        print(f"Filtered to {len(items)} Maracay records for stock_per_site")

    select_fields = ','.join(field_map.values())
    existing_dict = fetch_all_rows(table, select_fields)

    records = []
    for item in items:
        record = {db_field: (item.get(json_field) if json_field != key_field else item[key_field]) for json_field, db_field in field_map.items()}
        # Type conversions for known numeric fields
        if table == "customers":
            record["balance"] = float(item["Balance"]) if item.get("Balance") not in (None, "") else 0.0
            record["totalbalance"] = float(item["TotalBalance"]) if item.get("TotalBalance") not in (None, "") else 0.0
            record["creditlimit"] = float(item["CreditLimit"]) if item.get("CreditLimit") not in (None, "") else None
        elif table == "item_inventory":
            record["salesprice"] = float(item["SalesPrice"]) if item.get("SalesPrice") not in (None, "") else None
        records.append(record)

    to_insert, to_update = compare_and_split(records, existing_dict, field_map[key_field])
    bulk_insert(table, to_insert)
    patch_update(table, to_update, field_map[key_field])

def add_missing_item_inventory_entries_from_stock_per_site():
    # Load stock_per_site data
    with open("data/stock_per_site.json", 'r', encoding='utf-8') as f:
        data = json.load(f)
    items = data.get('result', [])
    # Filter for Maracay and non-null ProductListId/ProductFullName
    filtered = [item for item in items if item.get("InventorySiteFullName") == "Maracay" and item.get("ProductListId") and item.get("ProductFullName")]
    productlistids = set(item["ProductListId"] for item in filtered)

    # Fetch all existing listid from item_inventory
    existing_item_inventory = fetch_all_rows("item_inventory", "listid")
    existing_listids = set(existing_item_inventory.keys())

    # Find ProductListIds not in item_inventory
    missing_listids = productlistids - existing_listids
    if not missing_listids:
        print("No missing listids to add to item_inventory.")
        return
    # Prepare records with only listid
    new_records = [{"listid": listid} for listid in missing_listids]
    bulk_insert("item_inventory", new_records)

if __name__ == "__main__":
    upsert_from_json(
        "data/customers.json",
        "customers",
        key_field="QBId",
        field_map={
            "QBId": "qbid",
            "CustomerName": "customername",
            "FullName": "fullname",
            "Email": "email",
            "Balance": "balance",
            "TotalBalance": "totalbalance",
            "MainPhone": "mainphone",
            "CreditLimit": "creditlimit",
            "Address": "address",
            "Term": "term",
        }
    )
    upsert_from_json(
        "data/stock_per_site.json",
        "stock_per_site",
        key_field="ProductListId",
        field_map={
            "ProductListId": "productlistid",
            "Quantity": "quantity",
        }
    )
    upsert_from_json(
        "data/item_inventory.json",
        "item_inventory",
        key_field="ListID",
        field_map={
            "ListID": "listid",
            "Name": "name",
            "SalesPrice": "salesprice",
            "Description": "description",
            "Brand": "brand",
            "Category": "category",
        }
    )
    add_missing_item_inventory_entries_from_stock_per_site()
