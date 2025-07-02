from lxml import etree
import logging
import os

logging.basicConfig(level=logging.INFO)

def extract_orders_from_response(response_xml):
    # print(f"Response XML: {response_xml}")
    try:
        root = etree.fromstring(response_xml.encode("utf-8"))
        order_items = root.findall(".//SalesOrderRet")

        orders = []

        for order in order_items:
            line_items = []
            for line in order.findall("SalesOrderLineRet"):
                # logging.info(f"Line: {line}")
                line_items.append({
                    "TxnLineID": line.findtext("TxnLineID"),
                    "ItemFullName": line.findtext("ItemRef/FullName"),
                    "Description": line.findtext("Desc"),
                    "Quantity": float(line.findtext("Quantity", "0").replace(",", ".")),
                    "Rate": float(line.findtext("Rate", "0").replace(",", ".")),
                    "Amount": float(line.findtext("Amount", "0").replace(",", ".")),
                })

            orders.append({
                "TxnID": order.findtext("TxnID"),
                "RefNumber": order.findtext("RefNumber"),
                "CustomerName": order.findtext("CustomerRef/FullName") or "Sem nome",
                "TxnDate": order.findtext("TxnDate"),
                "Subtotal": float(order.findtext("Subtotal", "0").replace(',', '.')),
                "TotalAmount": float(order.findtext("TotalAmount", "0").replace(',', '.')),
                "SalesRepName": order.findtext("SalesRepRef/FullName"),
                "IsFullyInvoiced": order.findtext("IsFullyInvoiced") == "true",
                "Memo": order.findtext("Memo"),
                "LineItems": line_items
            })

        return orders
    except Exception as e:
        logging.error(f"Erro ao extrair pedidos: {e}")
        return []
    
def extract_products_from_response(response_xml):

    # logging.info(response_xml)

    try:
        root = etree.fromstring(response_xml.encode("utf-8"))
        inventory_items = root.findall(".//ItemInventoryRet")
        site_items = root.findall(".//ItemSitesRet")

        site_quantities = {}
        for item in site_items:
            name = item.findtext("ItemInventoryRef/FullName")
            qty = int(float(item.findtext("QuantityOnHand", "0").replace(',', '.')))
            site_quantities[name] = site_quantities.get(name, 0) + qty

        products = []
        for item in inventory_items:
            name = item.findtext("Name")
            price = float(item.findtext("SalesPrice", "0").replace(',', '.'))
            brand = None
            category = None
            for ext in item.findall("DataExtRet"):
                field_name = ext.findtext("DataExtName", "").upper()
                if field_name == "BRAND":
                    brand = ext.findtext("DataExtValue")
                elif field_name == "CATEGORIA":
                    category = ext.findtext("DataExtValue")

            products.append({
                "ListID": item.findtext("ListID"),
                "Name": name,
                "SalesPrice": price,
                "Description": item.findtext("SalesDesc") or "Sin descripcion",
                "Brand": brand or "Sin marca",
                "Category": category or "Sin categoría",
            })

        return products
    except Exception as e:
        logging.error(f"Erro ao extrair produtos: {e}")
        return []


def extract_customers_from_response(response_xml):
    try:
        root = etree.fromstring(response_xml.encode("utf-8"))
        customer_items = root.findall(".//CustomerRet")

        customers = []
        for cust in customer_items:
            customers.append({
                "QBId": cust.findtext("ListID"),
                "CustomerName": cust.findtext("CompanyName") or cust.findtext("Name") or "Sem nome",
                "FullName": f"{cust.findtext('FirstName') or ''} {cust.findtext('LastName') or ''}".strip(),
                "Email": cust.findtext("Email") or "",
                "Balance": cust.findtext("Balance") or "",
                "TotalBalance": cust.findtext("TotalBalance") or "",
                "MainPhone": cust.findtext("Phone") or "",
                "CreditLimit": cust.findtext("CreditLimit") or "",
                "Address": cust.findtext("BillAddress/Addr1") or "",
                "Term": cust.findtext("TermsRef/FullName") or "",
            })

        return customers
    except Exception as e:
        logging.error(f"Erro ao extrair clientes: {e}")
        return []

def extract_pricelevel_from_response(response_xml):
    try:
        root = etree.fromstring(response_xml.encode("utf-8"))
        pricelevel_items = root.findall(".//PriceLevelRet")

        pricelevels = []

        for item in pricelevel_items:
            price_level_type = item.findtext("PriceLevelType")
            fixed_percentage = item.findtext("PriceLevelFixedPercentage")

            per_item_prices = []
            for per_item in item.findall("PriceLevelPerItemRet"):
                per_item_prices.append({
                    "ItemFullName": per_item.findtext("ItemRef/FullName"),
                    "ItemListID": per_item.findtext("ItemRef/ListID"),
                    "CustomPrice": per_item.findtext("CustomPrice"),
                    "CustomPricePercent": per_item.findtext("CustomPricePercent"),
                })

            pricelevels.append({
                "ListID": item.findtext("ListID"),
                "Name": item.findtext("Name") or "Sem nome",
                "IsActive": item.findtext("IsActive") == "true",
                "PriceLevelType": price_level_type,
                "FixedPercentage": float(fixed_percentage.replace(",", ".")) if fixed_percentage else None,
                "PerItemPrices": per_item_prices if per_item_prices else None,
                "Currency": item.findtext("CurrencyRef/FullName"),
            })

        return pricelevels
    except Exception as e:
        logging.error(f"Erro ao extrair PriceLevel: {e}")
        return []