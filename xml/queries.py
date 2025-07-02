from datetime import datetime, timedelta
from app.qb_state import pending_iterators, collected_stock_sites, collected_products, collected_customers, collected_invoices, collected_sales_orders, collected_pricelevels

def sync_price_level():
    reqXML = f"""<?qbxml version="13.0"?>
                <QBXML>
                    <QBXMLMsgsRq onError="stopOnError">
                        <PriceLevelQueryRq requestID="1">
                            <MaxReturned >100</MaxReturned>
                        </PriceLevelQueryRq>
                    </QBXMLMsgsRq>
                </QBXML>
            """
    print(reqXML)
    return reqXML

def get_customer_xml():
    reqXML = f"""<?qbxml version="13.0"?>
                <QBXML>
                    <QBXMLMsgsRq onError="stopOnError">
                        <CustomerQueryRq requestID="1">
                            <FullName>Kern Lighting Warehouse</FullName>
                        </CustomerQueryRq>
                    </QBXMLMsgsRq>
                </QBXML>
            """
    print(reqXML)
    return reqXML


def generate_sales_order():
    """Generate a sample sales order XML."""
    customer_name = "John Doe"
    transaction_date = datetime.date.today().strftime("%Y-%m-%d")

    reqXML = f"""<?qbxml version="13.0"?>
<QBXML>
   <QBXMLMsgsRq onError="stopOnError">
      <SalesOrderAddRq requestID="cda7f342bb3542f992badad4332c4db7.1.salesorder:add.1">
        <SalesOrderAdd>
            <CustomerRef>
                <FullName>teste123</FullName>
            </CustomerRef>
            <SalesOrderLineAdd>
                <ItemRef>
                    <FullName>55</FullName>
                </ItemRef>
                <Quantity>10</Quantity>
                <Other1></Other1>
            </SalesOrderLineAdd>
        </SalesOrderAdd>
      </SalesOrderAddRq>
   </QBXMLMsgsRq>s
</QBXML>"""
    return reqXML


def generate_multiple_sales_orders(pending_orders):
    """
    Gera múltiplas ordens de venda no formato QBXML.
    :param pending_orders: Lista de pedidos pendentes.
    :return: String XML contendo as ordens de venda.
    """
    orders_xml = ""
    for order in pending_orders:
        customer_name = order.get("customerName", "Cliente não identificado")
        order_id = order.get("orderId", "N/A")
        items = order.get("items", [])

        items_xml = ""
        for item in items:
            description = item.get("description", "N/A")
            productid = item.get("productid", "N/A")
            quantity = item.get("quantity", 0)
            price = item.get("price", "0.00")

            items_xml += f"""
                <SalesOrderLineAdd>
                    <ItemRef>
                        <ListID>{productid}</ListID>
                    </ItemRef>
                    <Quantity>{quantity}</Quantity>
                    <Rate>{price}</Rate>
                </SalesOrderLineAdd>
            """

        orders_xml += f"""
            <SalesOrderAddRq requestID="{order_id}.salesorder:add.1">
                <SalesOrderAdd>
                    <CustomerRef>
                        <FullName>{customer_name}</FullName>
                    </CustomerRef>
                    {items_xml}
                </SalesOrderAdd>
            </SalesOrderAddRq>
        """

    reqXML = f"""<?qbxml version="13.0"?>
        <QBXML>
           <QBXMLMsgsRq onError="stopOnError">
              {orders_xml}
           </QBXMLMsgsRq>
        </QBXML>
    """

    return reqXML


# def generate_multiple_sales_orders(pending_orders):
#     """
#     Gera múltiplas ordens de venda no formato QBXML.
#     :param pending_orders: Lista de pedidos pendentes.
#     :return: String XML contendo as ordens de venda.
#     """
#     orders_xml = ""
#     for i, order in enumerate(pending_orders, start=1):
#         customer_name = order.get("customerName", "Cliente não identificado")
#         items = order.get("items", [])
#
#         items_xml = ""
#         for item in items:
#             item_name, item_code, quantity, price = item
#             items_xml += f"""
#                 <SalesOrderLineAdd>
#                     <ItemRef>
#                         <FullName>{item_name} ({item_code})</FullName>
#                     </ItemRef>
#                     <Quantity>{quantity}</Quantity>
#                     <Amount>{price}</Amount>
#                 </SalesOrderLineAdd>
#             """
#
#         orders_xml += f"""
#             <SalesOrderAddRq requestID="pedido-{i}">
#                 <SalesOrderAdd>
#                     <CustomerRef>
#                         <FullName>{customer_name}</FullName>
#                     </CustomerRef>
#                     {items_xml}
#                 </SalesOrderAdd>
#             </SalesOrderAddRq>
#         """
#
#     reqXML = f"""<?qbxml version="13.0"?>
#         <QBXML>
#            <QBXMLMsgsRq onError="stopOnError">
#               {orders_xml}
#            </QBXMLMsgsRq>
#         </QBXML>
#     """
#
#     return reqXML
#
#
# def generate_multiple_sales_orders():
#     """Gera um XML com vários pedidos de venda usando o mesmo produto com quantidades diferentes."""
#     # Lista de quantidades para cada pedido
#     quantities = [100, 20, 30, 40]
#
#     # Monta os nós de pedido para cada quantidade
#     orders_xml = ""
#     for i, qty in enumerate(quantities, start=1):
#         orders_xml += f"""
#               <SalesOrderAddRq requestID="pedido-{i}">
#                 <SalesOrderAdd>
#                     <CustomerRef>
#                         <FullName>teste123</FullName>
#                     </CustomerRef>
#                     <SalesOrderLineAdd>
#                         <ItemRef>H
#                             <FullName>55</FullName>
#                         </ItemRef>
#                         <Quantity>{qty}</Quantity>
#                         <Other1></Other1>
#                     </SalesOrderLineAdd>
#                 </SalesOrderAdd>
#               </SalesOrderAddRq>
#         """
#
#     reqXML = f"""<?qbxml version="13.0"?>
#         <QBXML>
#            <QBXMLMsgsRq onError="stopOnError">
#               {orders_xml}
#            </QBXMLMsgsRq>
#         </QBXML>
#     """
#
#     return reqXML

def format_qb_date(date_obj):
    return date_obj.strftime("%Y-%m-%dT%H:%M:%S-00:00")


# def sync_all_xml():
#     """Generate a XML for syncing all data."""

#     today = datetime.today().strftime("%Y-%m-%d")

#     last_3_months_start = (datetime.today() - timedelta(days=90)).strftime("%Y-%m-%d")

#     last_5_years_start = (datetime.today() - timedelta(days=365 * 5)).strftime("%Y-%m-%d")

#     max_returned = 100

#     reqXML = f"""<?qbxml version="16.0"?>
#         <QBXML>
#             <QBXMLMsgsRq onError="stopOnError">
#                 <ItemInventoryQueryRq requestID="prod-1" iterator="Start">
#                     <MaxReturned>100</MaxReturned>
#                     <OwnerID>0</OwnerID>
#                 </ItemInventoryQueryRq>
            

#             </QBXMLMsgsRq>
#         </QBXML>
#     """
#     return reqXML


def sync_all_xml():
    """Generate a XML for syncing all data."""

    today = datetime.today().strftime("%Y-%m-%d")

    last_3_months_start = (datetime.today() - timedelta(days=90)).strftime("%Y-%m-%d")

    last_5_years_start = (datetime.today() - timedelta(days=365 * 5)).strftime("%Y-%m-%d")

    max_returned = 100

    reqXML = f"""<?qbxml version="16.0"?>
        <QBXML>
            <QBXMLMsgsRq onError="stopOnError">
             
                 <CustomerQueryRq requestID="cust-1" iterator="Start">
                    <MaxReturned>100</MaxReturned>
                </CustomerQueryRq>
                <ItemInventoryQueryRq requestID="prod-1" iterator="Start">
                    <MaxReturned>100</MaxReturned>
                    <OwnerID>0</OwnerID>
                </ItemInventoryQueryRq>
                
                <ItemSitesQueryRq requestID="site-1" iterator="Start">
                    <MaxReturned>500</MaxReturned>
                </ItemSitesQueryRq>


                 <InvoiceQueryRq iterator="Start" requestID="4361726">
              
                    <MaxReturned>{max_returned}</MaxReturned>
                
                    <TxnDateRangeFilter>
                        <FromTxnDate>{last_3_months_start}</FromTxnDate>
                        <ToTxnDate>{today}</ToTxnDate>
                    </TxnDateRangeFilter>
            
                <PaidStatus>NotPaidOnly</PaidStatus>
                <IncludeLineItems>true</IncludeLineItems>
                
                </InvoiceQueryRq>
                

            </QBXMLMsgsRq>
        </QBXML>
    """
    return reqXML

def sync_customers_and_items():
    """Generate a XML for syncing customers and items."""

    reqXML = f"""<?qbxml version="16.0"?>
        <QBXML>
            <QBXMLMsgsRq onError="stopOnError">
                <CustomerQueryRq requestID="cust-1" iterator="Start">
                    <MaxReturned>100</MaxReturned>
                </CustomerQueryRq>
                <ItemInventoryQueryRq requestID="prod-1" iterator="Start">
                    <MaxReturned>100</MaxReturned>
                    <OwnerID>0</OwnerID>
                </ItemInventoryQueryRq>
            </QBXMLMsgsRq>
        </QBXML>
    """
    return reqXML

def sync_invoices():
    """Generate a XML for syncing invoices."""

    today = datetime.today().strftime("%Y-%m-%d")

    last_3_months_start = (datetime.today() - timedelta(days=90)).strftime("%Y-%m-%d")

    max_returned = 100

    reqXML = f"""<?qbxml version="16.0"?>
        <QBXML>
            <QBXMLMsgsRq onError="stopOnError">
                <InvoiceQueryRq iterator="Start" requestID="4361726">
                    <MaxReturned>{max_returned}</MaxReturned>
                    <TxnDateRangeFilter>
                        <FromTxnDate>{last_3_months_start}</FromTxnDate>
                        <ToTxnDate>{today}</ToTxnDate>
                    </TxnDateRangeFilter>
                    <PaidStatus>NotPaidOnly</PaidStatus>
                    <IncludeLineItems>true</IncludeLineItems>
                </InvoiceQueryRq>
            </QBXMLMsgsRq>
        </QBXML>
    """
    return reqXML

def sync_customers():
    """Generate a XML for syncing customers."""

    reqXML = f"""<?qbxml version="16.0"?>
        <QBXML>
            <QBXMLMsgsRq onError="stopOnError">
                <CustomerQueryRq requestID="cust-1" iterator="Start">
                    <MaxReturned>100</MaxReturned>
                </CustomerQueryRq>
            </QBXMLMsgsRq>
        </QBXML>
    """
    return reqXML

def sync_item_inventory():
    """Generate a XML for syncing item inventory."""

    reqXML = f"""<?qbxml version="16.0"?>
        <QBXML>
            <QBXMLMsgsRq onError="stopOnError">
                <ItemInventoryQueryRq requestID="prod-1" iterator="Start">
                    <MaxReturned>5</MaxReturned>
                    <OwnerID>0</OwnerID>
                </ItemInventoryQueryRq>
            </QBXMLMsgsRq>
        </QBXML>
    """
    return reqXML

def sync_stock_sites():
    # """Generate a XML for syncing stock sites."""

    # reqXML = f"""<?qbxml version="16.0"?>
    #     <QBXML>
    #         <QBXMLMsgsRq onError="stopOnError">
    #             <ItemSitesQueryRq requestID="site-1" iterator="Start">
    #                 <MaxReturned>12</MaxReturned>
    #             </ItemSitesQueryRq>
    #         </QBXMLMsgsRq>
    #     </QBXML>
    # """
    # return reqXML
    """Inicia sincronização via iterator"""
    collected_stock_sites.clear()

    pending_iterators.appendleft({
        "type": "ItemSitesQueryRq",
        "iterator": "Start",
        "iterator_id": None
    })

def sync_orders():
    """Generate a XML for syncing orders."""

    today = datetime.today().strftime("%Y-%m-%d")

    last_3_months_start = (datetime.today() - timedelta(days=90)).strftime("%Y-%m-%d")

    max_returned = 100

    reqXML = f"""<?qbxml version="13.0"?>
        <QBXML>
            <QBXMLMsgsRq onError="stopOnError">
                <SalesOrderQueryRq requestID="salesorder-1" iterator="Start">
                    <MaxReturned>{max_returned}</MaxReturned>

                    <TxnDateRangeFilter>
                        <FromTxnDate>{last_3_months_start}</FromTxnDate>
                        <ToTxnDate>{today}</ToTxnDate>
                    </TxnDateRangeFilter>

                    <OwnerID >0</OwnerID>
                </SalesOrderQueryRq>
            </QBXMLMsgsRq>
        </QBXML>
    """
    print(reqXML)

def generate_invoice_req_xml():
    """Generate a sample invoice request XML."""

    today = datetime.today().strftime("%Y-%m-%d")

    last_3_months_start = (datetime.today() - timedelta(days=90)).strftime("%Y-%m-%d")

    max_returned = 100

    reqXML = f"""
        <?qbxml version="8.0"?>
        <QBXML>
           <QBXMLMsgsRq onError="stopOnError">
              <InvoiceQueryRq iterator="Start" requestID="4361726">
              
                <MaxReturned>{max_returned}</MaxReturned>
              
                <TxnDateRangeFilter>
                    <FromTxnDate>{last_3_months_start}</FromTxnDate>
                    <ToTxnDate>{today}</ToTxnDate>
                </TxnDateRangeFilter>
            
                <PaidStatus>NotPaidOnly</PaidStatus>
                <IncludeLineItems>true</IncludeLineItems>
                
              </InvoiceQueryRq>
           </QBXMLMsgsRq>
        </QBXML>
    """

    return reqXML

                # <IncludeRetElement>TxnID</IncludeRetElement>
                # <IncludeRetElement>TxnDate</IncludeRetElement>
                # <IncludeRetElement>RefNumber</IncludeRetElement>
                # <IncludeRetElement>CustomerRef</IncludeRetElement>
                # <IncludeRetElement>BalanceRemaining</IncludeRetElement>
                # <IncludeRetElement>Subtotal</IncludeRetElement>


def generate_multiple_sales_orders():
    quantities = [100, 20, 30, 40]

    orders_xml = ""
    for i, qty in enumerate(quantities, start=1):
        orders_xml += f"""
              <SalesOrderAddRq requestID="pedido-{i}">
                <SalesOrderAdd>
                    <CustomerRef>
                        <FullName>teste123</FullName>
                    </CustomerRef>
                    <SalesOrderLineAdd>
                        <ItemRef>
                            <FullName>55</FullName>
                        </ItemRef>
                        <Quantity>{qty}</Quantity>
                        <Other1></Other1>
                    </SalesOrderLineAdd>
                </SalesOrderAdd>
              </SalesOrderAddRq>
        """

    reqXML = f"""<?qbxml version="13.0"?>
        <QBXML>
           <QBXMLMsgsRq onError="stopOnError">
              {orders_xml}
           </QBXMLMsgsRq>
        </QBXML>
    """

    return reqXML


def generate_multiple_sales_orders_xml(pending_orders):
    """
    "Generate the xml for the orders."
    """
    orders_xml = ""
    for order in pending_orders:
        customer_name = order.get("customerName", "Cliente não identificado")
        order_id = order.get("orderId", "N/A")
        items = order.get("items", [])

        items_xml = ""
        for item in items:
            description = item.get("description", "N/A")
            productid = item.get("productid", "N/A")
            quantity = item.get("quantity", 0)
            price = item.get("price", "0.00")

            items_xml += f"""
                <SalesOrderLineAdd>
                    <ItemRef>
                        <ListID>{productid}</ListID>
                    </ItemRef>
                    <Quantity>{quantity}</Quantity>
                    <Rate>{price}</Rate>
                </SalesOrderLineAdd>
            """

        orders_xml += f"""
            <SalesOrderAddRq requestID="{order_id}.salesorder:add.1">
                <SalesOrderAdd>
                    <CustomerRef>
                        <FullName>{customer_name}</FullName>
                    </CustomerRef>
                    {items_xml}
                </SalesOrderAdd>
            </SalesOrderAddRq>
        """

    reqXML = f"""<?qbxml version="13.0"?>
        <QBXML>
           <QBXMLMsgsRq onError="stopOnError">
              {orders_xml}
           </QBXMLMsgsRq>
        </QBXML>
    """

    return reqXML


def generate_invoice_continue_xml(iterator_id):
    return f"""<?qbxml version=\"16.0\"?>
<QBXML>
  <QBXMLMsgsRq onError=\"stopOnError\">
    <InvoiceQueryRq iterator=\"Continue\" iteratorID=\"{iterator_id}\" requestID=\"inv123\">
    <MaxReturned>100</MaxReturned>
      <IncludeLineItems>true</IncludeLineItems>
    </InvoiceQueryRq>
  </QBXMLMsgsRq>
</QBXML>"""

def generate_customer_continue_xml(iterator_id):
    return f"""<?qbxml version="16.0"?>
<QBXML>
  <QBXMLMsgsRq onError="stopOnError">
    <CustomerQueryRq iterator="Continue" iteratorID="{iterator_id}" requestID="cust123">
      <MaxReturned>100</MaxReturned>
    </CustomerQueryRq>
  </QBXMLMsgsRq>
</QBXML>"""



def generate_product_continue_xml(iterator_id):
    return f"""<?qbxml version=\"16.0\"?>
<QBXML>
  <QBXMLMsgsRq onError=\"stopOnError\">
    <ItemInventoryQueryRq iterator=\"Continue\" iteratorID=\"{iterator_id}\" requestID=\"prod123\">
       <MaxReturned>100</MaxReturned>
      <OwnerID>0</OwnerID>
    </ItemInventoryQueryRq>
  </QBXMLMsgsRq>
</QBXML>"""
