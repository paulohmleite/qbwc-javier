import json

# Activate venv before running this script:
#   venv\\Scripts\\activate.bat

# Read the stock_per_site.json file
with open('data/stock_per_site.json', 'r', encoding='utf-8') as infile:
    data = json.load(infile)

# Filter the results and collect ProductListIds
filtered_results = [
    item for item in data.get('result', [])
    if item.get('InventorySiteFullName') == 'Maracay' and item.get('ProductListId')
]
filtered_product_ids = {item['ProductListId'] for item in filtered_results}

# Prepare the output structure for stock
filtered_data = [
    {
        'ProductListId': item['ProductListId'],
        'Quantity': item['Quantity']
    }
    for item in filtered_results
]
# Write the filtered data to filter_stock.json
with open('data/filter_stocks.json', 'w', encoding='utf-8') as outfile:
    json.dump(filtered_data, outfile, ensure_ascii=False, indent=2)

# Read the item_inventory.json file
with open('data/item_inventory.json', 'r', encoding='utf-8') as infile:
    item_data = json.load(infile)

# Filter item inventory based on ProductListId matches ListID
filtered_items = [
    item for item in item_data.get('result', [])
    if item.get('ListID') in filtered_product_ids
]

filtered_item_data = filtered_items

# Write the filtered item inventory to filter_item_inventory.json
with open('data/filter_items.json', 'w', encoding='utf-8') as outfile:
    json.dump(filtered_item_data, outfile, ensure_ascii=False, indent=2)

# Read the customers.json file
with open('data/customers.json', 'r', encoding='utf-8') as infile:
    customers_data = json.load(infile)

# For now, copy all customers to filter_customers.json as an array
filtered_customers = customers_data.get('result', [])

# Write the filtered users to filter_users.json
with open('data/filter_customers.json', 'w', encoding='utf-8') as outfile:
    json.dump(filtered_customers, outfile, ensure_ascii=False, indent=2)

# Read the invoices.json file
with open('data/invoices.json', 'r', encoding='utf-8') as infile:
    invoices_data = json.load(infile)

# For now, copy all invoices to filter_invoices.json as an array
filtered_invoices = invoices_data.get('result', [])

# Write the filtered invoices to filter_invoices.json
with open('data/filter_invoices.json', 'w', encoding='utf-8') as outfile:
    json.dump(filtered_invoices, outfile, ensure_ascii=False, indent=2)

# Read the sales_orders.json file
with open('data/sales_orders.json', 'r', encoding='utf-8') as infile:
    sales_orders_data = json.load(infile)

# For now, copy all sales orders to filter_sales_orders.json as an array
filtered_sales_orders = sales_orders_data.get('result', [])

# Write the filtered sales orders to filter_sales_orders.json
with open('data/filter_sales_orders.json', 'w', encoding='utf-8') as outfile:
    json.dump(filtered_sales_orders, outfile, ensure_ascii=False, indent=2)

# Extract and flatten line items for all sales orders
sales_order_lineitems = []
for order in filtered_sales_orders:
    txnid = order.get('TxnID')
    for li in order.get('LineItems', []):
        lineitem = {
            'TxnLineID': li.get('TxnLineID'),
            'SalesOrder_TxnID': txnid,
            'ItemFullName': li.get('ItemFullName'),
            'Description': li.get('Description'),
            'Quantity': li.get('Quantity'),
            'Rate': li.get('Rate'),
            'Amount': li.get('Amount')
        }
        sales_order_lineitems.append(lineitem)

# Write the flattened sales order line items to filter_sales_order_lineitems.json
with open('data/filter_sales_order_lineitems.json', 'w', encoding='utf-8') as outfile:
    json.dump(sales_order_lineitems, outfile, ensure_ascii=False, indent=2)
