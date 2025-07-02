from concurrent.futures import ThreadPoolExecutor
import uuid
import logging
import os
from datetime import datetime, timedelta
import json
from dotenv import load_dotenv

# COMPANY_NAME = "s:\\qbs\\jimac\\jimac enterprises llc.qbw";

from app.utils import enqueue_iterator_continue
from spyne.application import Application
from spyne.service import ServiceBase
from spyne.model.primitive import Integer, Unicode
from spyne.model.complex import Array
from spyne.decorator import srpc
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication
from app.qb_state import pending_iterators, qb_request_queue, collected_stock_sites, collected_products, collected_customers, collected_invoices, collected_sales_orders, collected_pricelevels, ordersQueue

from xml.queries import generate_multiple_sales_orders_xml
from xml.utils import extract_customers_from_response, extract_orders_from_response, extract_pricelevel_from_response, extract_products_from_response


load_dotenv()

QB_USER = "Admin"
QB_PASSWORD = os.getenv("QB_PASSWORD")
COMPANY_NAME = os.getenv("COMPANY_NAME")
print(f"COMPANY_NAME: {COMPANY_NAME}")
print(f"QB_PASSWORD: {QB_PASSWORD}")

ITEM_INVENTORY_FILE = "data/item_inventory.json"
INVOICES_FILE = "data/invoices.json"
CUSTOMERS_FILE = "data/customers.json"
ITEM_SITES_FILE = "data/item_sites.json"
SALESORDERS = "data/salesorders.json"

os.makedirs(os.path.dirname(ITEM_INVENTORY_FILE), exist_ok=True)

executor = ThreadPoolExecutor(max_workers=5)


logging.basicConfig(level=logging.INFO)


def process_response_async(response):
    try:
        from lxml import etree
        global collected_products
        global collected_invoices
        global collected_customers
        global collected_sites
        global collected_salesorders
        global collected_pricelevels

        root = etree.fromstring(response.encode('utf-8'))

        SALESORDER_RS = root.find('.//SalesOrderQueryRs')
        if SALESORDER_RS is not None:
            global collected_sales_orders

            logging.info("XML SalesOrder:")
            logging.info(response)

            iterator_id = SALESORDER_RS.get("iteratorID")
            remaining_count = int(SALESORDER_RS.get("iteratorRemainingCount", "0"))
            logging.info(f"📦 Remaining sales orders: {remaining_count}")

            # Extrai e acumula os pedidos
            extracted_orders = extract_orders_from_response(response)
            collected_sales_orders.extend(extracted_orders)

            if remaining_count > 0 and iterator_id:
                enqueue_iterator_continue("SalesOrderQueryRq", iterator_id)
                return

            # ✅ Fim da iteração — salva no JSON
            SALES_ORDER_FILE = "data/sales_orders.json"
            os.makedirs(os.path.dirname(SALES_ORDER_FILE), exist_ok=True)

            logging.info(collected_sales_orders)

            data_to_save = {
                "retrieved_at": datetime.now().astimezone().isoformat(),
                "result": collected_sales_orders
            }

            try:
                with open(SALES_ORDER_FILE, "w", encoding="utf-8") as f:
                    json.dump(data_to_save, f, indent=2, ensure_ascii=False)
                logging.info(f"ALl sales orders saved in {SALES_ORDER_FILE}")
            except Exception as e:
                logging.error(f"❌ Error saving sales_orders.json: {e}")

            collected_sales_orders = []

        pricelevel_rs = root.find('.//PriceLevelQueryRs')
        if pricelevel_rs is not None:
            global collected_pricelevels

            iterator_id = pricelevel_rs.get("iteratorID")
            remaining_count = int(pricelevel_rs.get("iteratorRemainingCount", "0"))
            logging.info(f"🏷️ Remaining price levels: {remaining_count}")

            pricelevels = extract_pricelevel_from_response(response)
            collected_pricelevels.extend(pricelevels)

            if remaining_count > 0 and iterator_id:
                enqueue_iterator_continue("PriceLevelQueryRq", iterator_id)
                return

            PRICELEVEL_FILE = "data/price_levels.json"
            os.makedirs(os.path.dirname(PRICELEVEL_FILE), exist_ok=True)

            data_to_save = {
                "retrieved_at": datetime.now().astimezone().isoformat(),
                "result": collected_pricelevels
            }

            try:
                with open(PRICELEVEL_FILE, "w", encoding="utf-8") as f:
                    json.dump(data_to_save, f, indent=2, ensure_ascii=False)
                logging.info(f"✅ All price levels saved in {PRICELEVEL_FILE}")
            except Exception as e:
                logging.error(f"❌ Error saving price_levels.json: {e}")

            collected_pricelevels = []


        iteminv_rs = root.find('.//ItemInventoryQueryRs')
        if iteminv_rs is not None:
            iterator_id = iteminv_rs.get("iteratorID")
            remaining_count = int(iteminv_rs.get("iteratorRemainingCount", "0"))
            logging.info(f"📦 Remaining products: {remaining_count}")

            # print("\n" + "=" * 60)
            # print("📦 RESPOSTA DO ITEM INVENTORY QUERY:")
            # print(response)
            # print("=" * 60 + "\n")

            products = extract_products_from_response(response)
            collected_products.extend(products)

            if remaining_count > 0 and iterator_id:
                enqueue_iterator_continue("ItemInventoryQueryRq", iterator_id)
                return

            ITEM_INVENTORY_FILE = "data/item_inventory.json"
            os.makedirs(os.path.dirname(ITEM_INVENTORY_FILE), exist_ok=True)

            data_to_save = {
                "retrieved_at": datetime.now().astimezone().isoformat(),
                "result": collected_products
            }

            try:
                with open(ITEM_INVENTORY_FILE, "w", encoding="utf-8") as f:
                    json.dump(data_to_save, f, indent=2, ensure_ascii=False)
                logging.info(f"✅ All products saved in {ITEM_INVENTORY_FILE}")
            except Exception as e:
                logging.error(f"❌ Error saving item_inventory.json: {e}")

            collected_products = []



        invoice_rs = root.find('.//InvoiceQueryRs')
        if invoice_rs is not None:
            global collected_invoices

            iterator_id = invoice_rs.get("iteratorID")
            remaining_count = int(invoice_rs.get("iteratorRemainingCount", "0"))
            logging.info(f"🧾 Remaining invoices: {remaining_count}")

            for invoice_ret in root.findall('.//InvoiceRet'):
                # logging.info("XML do Invoice:")
                # logging.info(invoice_ret)
                invoice_data = {
                    "TxnID": invoice_ret.findtext('TxnID'),
                    "QBId": invoice_ret.findtext('TxnID'),
                    "CustomerFullName": invoice_ret.findtext('CustomerRef/FullName'),
                    "TxnDate": invoice_ret.findtext('TxnDate'),
                    "RefNumber": invoice_ret.findtext('RefNumber'),
                    "Subtotal": float(invoice_ret.findtext('Subtotal', "0").replace(',', '.')),
                    "BalanceRemaining": float(invoice_ret.findtext('BalanceRemaining', "0").replace(',', '.')),
                    "LineItems": []
                }

                for line_ret in invoice_ret.findall('.//InvoiceLineRet'):
                    invoice_data["LineItems"].append({
                        "TxnLineID": line_ret.findtext('TxnLineID'),
                        "ItemFullName": line_ret.findtext('ItemRef/FullName'),
                        "Desc": line_ret.findtext('Desc', ""),
                        "Quantity": float(line_ret.findtext('Quantity', "0").replace(',', '.')),
                        "UnitOfMeasure": line_ret.findtext('UnitOfMeasure', ""),
                        "Rate": float(line_ret.findtext('Rate', "0").replace(',', '.')),
                        "Amount": float(line_ret.findtext('Amount', "0").replace(',', '.')),
                    })

                collected_invoices.append(invoice_data)

            if remaining_count > 0 and iterator_id:
                enqueue_iterator_continue("InvoiceQueryRq", iterator_id)
                return

            INVOICES_FILE = "data/invoices.json"
            os.makedirs(os.path.dirname(INVOICES_FILE), exist_ok=True)

            data_to_save = {
                "retrieved_at": datetime.now().astimezone().isoformat(),
                "result": collected_invoices
            }

            try:
                with open(INVOICES_FILE, "w", encoding="utf-8") as f:
                    json.dump(data_to_save, f, indent=2, ensure_ascii=False)
                logging.info(f"✅ All invoices saved in {INVOICES_FILE}")
            except Exception as e:
                logging.error(f"❌ Error saving invoices.json: {e}")

            collected_invoices = []


        customer_rs = root.find('.//CustomerQueryRs')
        if customer_rs is not None:
            global collected_customers

            iterator_id = customer_rs.get("iteratorID")
            remaining_count = int(customer_rs.get("iteratorRemainingCount", "0"))
            logging.info(f"👥 Remaining customers: {remaining_count}")

            customers = extract_customers_from_response(response)
            collected_customers.extend(customers)

            if remaining_count > 0 and iterator_id:
                enqueue_iterator_continue("CustomerQueryRq", iterator_id)
                return

            CUSTOMERS_FILE = "data/customers.json"
            os.makedirs(os.path.dirname(CUSTOMERS_FILE), exist_ok=True)

            data_to_save = {
                "retrieved_at": datetime.now().astimezone().isoformat(),
                "result": collected_customers
            }

            try:
                with open(CUSTOMERS_FILE, "w", encoding="utf-8") as f:
                    json.dump(data_to_save, f, indent=2, ensure_ascii=False)
                logging.info(f"✅ All customers saved in {CUSTOMERS_FILE}")
            except Exception as e:
                logging.error(f"❌ Error saving customers.json: {e}")

            collected_customers = []


        site_rs = root.find('.//ItemSitesQueryRs')
        if site_rs is not None:
            global collected_stock_sites

            iterator_id = site_rs.get("iteratorID")
            remaining_count = int(site_rs.get("iteratorRemainingCount", "0"))
            logging.info(f"🏬 Remaining stock sites: {remaining_count}")

            site_entries = root.findall(".//ItemSitesRet")

            stock_per_site = []
            for site in site_entries:
                product_name = site.findtext("ItemInventoryRef/FullName")
                product_listid = site.findtext("ItemInventoryRef/ListID")
                site_name = site.findtext("InventorySiteRef/FullName")
                list_id = site.findtext("InventorySiteRef/ListID")
                quantity = float(site.findtext("QuantityOnHand", "0").replace(",", "."))

                stock_per_site.append({
                    "ProductFullName": product_name,
                    "ProductListId": product_listid,
                    "InventorySiteListID": list_id,
                    "InventorySiteFullName": site_name,
                    "Quantity": quantity
                })

            collected_stock_sites.extend(stock_per_site)

            if remaining_count > 0 and iterator_id:
                enqueue_iterator_continue("ItemSitesQueryRq", iterator_id)
                return

            SITES_FILE = "data/stock_per_site.json"
            os.makedirs(os.path.dirname(SITES_FILE), exist_ok=True)

            data_to_save = {
                "retrieved_at": datetime.now().astimezone().isoformat(),
                "result": collected_stock_sites
            }

            try:
                with open(SITES_FILE, "w", encoding="utf-8") as f:
                    json.dump(data_to_save, f, indent=2, ensure_ascii=False)
                logging.info(f"✅ Stock per site saved in {SITES_FILE}")
            except Exception as e:
                logging.error(f"❌ Error saving stock_per_site.json: {e}")

            collected_stock_sites = []


    except Exception as e:
        logging.error("Error processing asynchronous XML:", exc_info=True)

# =============================
# Soap Service
# =============================
class QBWCService(ServiceBase):

    # @srpc(Unicode, Unicode, Unicode, Unicode, Integer, Integer, _returns=Unicode)
    # def sendRequestXML(ticket, strHCPResponse, strCompanyFileName, qbXMLCountry, qbXMLMajorVers, qbXMLMinorVers):
    #     """Send qbXML request to QuickBooks."""
    #     logging.info(f"Sending qbXML request for ticket: {ticket}")
    #     # TODO here you can check in the database if there are orders to send to QuickBooks
    #     # xml_order = generate_sales_order()
    #     # xml_order = generate_multiple_sales_orders()
    #     # logging.info(f"Generated sales order XML: {xml_order}")
    #     xml_order = get_customer_xml()
    #     logging.info(f"Generated customer XML: {xml_order}")
    #     return xml_order

    @srpc(Unicode, Unicode, Unicode, Unicode, Integer, Integer, _returns=Unicode)
    def sendRequestXML(ticket, strHCPResponse, strCompanyFileName, qbXMLCountry, qbXMLMajorVers, qbXMLMinorVers):
        """Send qbXML request to QuickBooks."""
        logging.info(f"Processing QuickBooks request for ticket: {ticket}")

        logging.info(f": {ordersQueue}")
        if ordersQueue:
            pending_orders = [order for order in ordersQueue.values() if order["status"] == "pending"]
            logging.info(f"Pending orders: {len(pending_orders)}")
            if pending_orders:
                xml_request = generate_multiple_sales_orders_xml(pending_orders)
                logging.info(xml_request)

                for order in pending_orders:
                    order["status"] = "sent"

                return xml_request


        if qb_request_queue:
            xml_request = qb_request_queue.popleft()
            return xml_request

        if pending_iterators:
            iterator_task = pending_iterators.popleft()
            iterator_type = iterator_task["type"]

            if iterator_type == "PriceLevelQueryRq":
                xml_request = """<?xml version="1.0"?>
                    <?qbxml version="13.0"?>
                    <QBXML>
                    <QBXMLMsgsRq onError="stopOnError">
                    <PriceLevelQueryRq>
                    <MaxReturned>1000</MaxReturned>
                    </PriceLevelQueryRq>
                    </QBXMLMsgsRq>
                    </QBXML>"""
                logging.info(f"xml: {xml_request}")
                logging.info("Sending PriceLevelQueryRq without iterator")
                return xml_request

            iterator_id = iterator_task.get("iterator_id")
            iterator_flag = iterator_task.get("iterator", "Continue")

            if iterator_flag == "Start":
                if iterator_type == "SalesOrderQueryRq":
                    from_date = "2024-01-01"
                    to_date = datetime.today().strftime("%Y-%m-%d")

                    today = datetime.today().strftime("%Y-%m-%d")
                    last_3_months_start = (datetime.today() - timedelta(days=90)).strftime("%Y-%m-%d")

                    xml_request = f"""<?xml version="1.0"?>
                                    <?qbxml version="13.0"?>
                                    <QBXML>
                                        <QBXMLMsgsRq onError="stopOnError">
                                            <SalesOrderQueryRq requestID="start-SalesOrderQueryRq" iterator="Start">
                                                <MaxReturned>100</MaxReturned>
                                                <TxnDateRangeFilter>
                                                    <FromTxnDate>{from_date}</FromTxnDate>
                                                    <ToTxnDate>{to_date}</ToTxnDate>
                                                </TxnDateRangeFilter>
                                                <IncludeLineItems>true</IncludeLineItems>
                                                <OwnerID>0</OwnerID>
                                            </SalesOrderQueryRq>
                                        </QBXMLMsgsRq>
                                    </QBXML>"""

                elif iterator_type == "ItemInventoryQueryRq":
                    xml_request = f"""<?xml version="1.0"?>
                                    <?qbxml version="13.0"?>
                                    <QBXML>
                                        <QBXMLMsgsRq onError="stopOnError">
                                            <{iterator_type} requestID="start-{iterator_type}" iterator="Start">
                                                <MaxReturned>100</MaxReturned>
                                                <OwnerID>0</OwnerID>
                                            </{iterator_type}>
                                        </QBXMLMsgsRq>
                                    </QBXML>"""

                elif iterator_type == "InvoiceQueryRq":
                    xml_request = f"""<?xml version="1.0"?>
                                    <?qbxml version="13.0"?>
                                    <QBXML>
                                        <QBXMLMsgsRq onError="stopOnError">
                                            <{iterator_type} requestID="start-{iterator_type}" iterator="Start">
                                                <MaxReturned>100</MaxReturned>
                                                <PaidStatus>NotPaidOnly</PaidStatus>
                                                <IncludeLineItems>true</IncludeLineItems>
                                            </{iterator_type}>
                                        </QBXMLMsgsRq>
                                    </QBXML>"""

                else:
                    xml_request = f"""<?xml version="1.0"?>
                                <?qbxml version="13.0"?>
                                <QBXML>
                                    <QBXMLMsgsRq onError="stopOnError">
                                        <{iterator_type} requestID="start-{iterator_type}" iterator="Start">
                                            <MaxReturned>100</MaxReturned>
                                        </{iterator_type}>
                                    </QBXMLMsgsRq>
                                </QBXML>"""
            else:
                if iterator_type == "SalesOrderQueryRq":
                    from_date = "2024-01-01"
                    to_date = datetime.today().strftime("%Y-%m-%d")

                    xml_request = f"""<?xml version="1.0"?>
                                    <?qbxml version="13.0"?>
                                    <QBXML>
                                        <QBXMLMsgsRq onError="stopOnError">
                                            <SalesOrderQueryRq iterator="Continue" iteratorID="{iterator_id}" requestID="cont-SalesOrderQueryRq">
                                                <MaxReturned>100</MaxReturned>
                                                <TxnDateRangeFilter>
                                                    <FromTxnDate>{from_date}</FromTxnDate>
                                                    <ToTxnDate>{to_date}</ToTxnDate>
                                                </TxnDateRangeFilter>
                                                <IncludeLineItems>true</IncludeLineItems>
                                                <OwnerID>0</OwnerID>
                                            </SalesOrderQueryRq>
                                        </QBXMLMsgsRq>
                                    </QBXML>"""


                elif iterator_type == "ItemInventoryQueryRq":
                    xml_request = f"""<?xml version="1.0"?>
                                    <?qbxml version="13.0"?>
                                    <QBXML>
                                        <QBXMLMsgsRq onError="stopOnError">
                                            <{iterator_type} iterator="Continue" iteratorID="{iterator_id}" requestID="cont-{iterator_type}">
                                                <MaxReturned>100</MaxReturned>
                                                <OwnerID>0</OwnerID>
                                            </{iterator_type}>
                                        </QBXMLMsgsRq>
                                    </QBXML>"""

                elif iterator_type == "InvoiceQueryRq":
                    xml_request = f"""<?xml version="1.0"?>
                                    <?qbxml version="13.0"?>
                                    <QBXML>
                                        <QBXMLMsgsRq onError="stopOnError">
                                            <{iterator_type} iterator="Continue" iteratorID="{iterator_id}" requestID="cont-{iterator_type}">
                                                <MaxReturned>100</MaxReturned>
                                                <PaidStatus>NotPaidOnly</PaidStatus>
                                                <IncludeLineItems>true</IncludeLineItems>
                                            </{iterator_type}>
                                        </QBXMLMsgsRq>
                                    </QBXML>"""

                else:
                    xml_request = f"""<?xml version="1.0"?>
                                        <?qbxml version="13.0"?>
                                            <QBXML>
                                            <QBXMLMsgsRq onError="stopOnError">
                                                <{iterator_type} iterator="Continue" iteratorID="{iterator_id}" requestID="cont-{iterator_type}">
                                                   <MaxReturned>100</MaxReturned>
                                                </{iterator_type}>
                                            </QBXMLMsgsRq>
                                        </QBXML>"""

            logging.info(f"Iterator ID: {iterator_id}")
            logging.info(f"xml: {xml_request}")
            logging.info(f"Sending iterator {iterator_flag} for {iterator_type}")
            return xml_request

        return ""

    @srpc(Unicode, Unicode, _returns=Array(Unicode))
    def authenticate(strUserName, strPassword):
        """Authenticate the user."""
        logging.info(f"Attempting authentication for user: {strUserName}")
        if strUserName == QB_USER and strPassword == QB_PASSWORD:
            session_ticket = str(uuid.uuid4())
            logging.info(f"Authentication successful. Session ticket: {session_ticket}")
            return [session_ticket, COMPANY_NAME]
        else:
            logging.warning("Authentication failed. Invalid credentials.")
            return ["none", "nvu"]

    @srpc(Unicode, _returns=Unicode)
    def clientVersion(strVersion):
        """Get the client version."""
        logging.info(f"Client version received: {strVersion}")
        return ""

    # server version
    @srpc(Unicode, _returns=Unicode)
    def serverVersion(strVersion):
        """Get the server version."""
        logging.info(f"Server version received: {strVersion}")
        return "1.0.0"

    @srpc(Unicode, _returns=Unicode)
    def closeConnection(ticket):
        """Indicate that the connection is closed."""
        logging.info(f"Closing connection for ticket: {ticket}")
        return "OK, all done!"

    @srpc(Unicode, Unicode, Unicode, _returns=Unicode)
    def connectionError(ticket, hresult, message):
        """Return an error message for the given ticket."""
        logging.error(f"Connection error with ticket: {ticket}, HRESULT: {hresult}, message: {message}")
        return "done"

    @srpc(Unicode, _returns=Unicode)
    def getLastError(ticket):
        """Return the last error for the given ticket."""
        logging.info(f"Fetching last error for ticket: {ticket}")
        return "No errors."

    @srpc(Unicode, Unicode, Unicode, Unicode, _returns=Integer)
    def receiveResponseXML(ticket, response, hresult, message):
        logging.info("----- receiveResponseXML -----")
        logging.info(f"Ticket: {ticket}")
        logging.info(f"Hresult: {hresult}")
        logging.info(f"Message: {message}")
        logging.info(f"Response: {response[:500]}")

        if not response.strip():
            return 100

        # Processa a resposta no mesmo thread para garantir que pending_iterators seja atualizado
        process_response_async(response)

        # Se tiver mais páginas, continue
        return 0 if pending_iterators else 100




# Create the soap app
soap_app = Application(
    [QBWCService],
    tns="http://developer.intuit.com/",
    in_protocol=Soap11(validator="lxml"),
    out_protocol=Soap11(),
)
application_soap = WsgiApplication(soap_app)