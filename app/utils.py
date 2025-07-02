from app.qb_state import pending_iterators, collected_products, collected_customers, collected_invoices, collected_stock_sites, collected_sales_orders, collected_pricelevels

def enqueue_iterator_continue(type_, iterator_id):
    pending_iterators.appendleft({
        "type": type_,
        "iterator_id": iterator_id,
        "iterator": "Continue"
    })
