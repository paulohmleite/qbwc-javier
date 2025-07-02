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
                        <ItemRef>H
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
