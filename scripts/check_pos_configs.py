import xmlrpc.client

url = 'https://erp.stephanspetstore.co.tz'
db = 'Stephans'
username = 'info@stephanspetstore.co.tz'
password = 'Stephan@3202'

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

pos_configs = models.execute_kw(db, uid, password, 'pos.config', 'search_read', [[]], {
    'fields': ['id', 'name', 'warehouse_id', 'picking_type_id']
})
print("POS Configurations:")
for pc in pos_configs:
    print(f"  ID {pc['id']} | Name: {pc['name']} | Warehouse: {pc['warehouse_id']} | Picking Type: {pc['picking_type_id']}")

# Also test cashier search_read
uid_cashier = 11
cashier_orders = models.execute_kw(db, uid, password, 'pos.order', 'search_read', [
    [('date_order', '>=', '2026-10-12 00:00:00')]
], {
    'fields': ['name', 'date_order', 'amount_total', 'session_id'],
    'context': {'uid': uid_cashier}
})
print(f"\nOrders visible since 2026-10-12: {len(cashier_orders)}")
print(f"Total sales sum: {sum(o['amount_total'] for o in cashier_orders):,.2f} TZS")
