import xmlrpc.client

url = 'https://erp.stephanspetstore.co.tz'
db = 'Stephans'
username = 'info@stephanspetstore.co.tz'
password = 'Stephan@3202'

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

# Fetch all orders where create_date was between Monday 2026-10-12 and Saturday 2026-10-17 (or Sunday Oct 18)
orders = models.execute_kw(db, uid, password, 'pos.order', 'search_read', [
    [('create_date', '>=', '2026-10-12 00:00:00'), ('create_date', '<=', '2026-10-18 23:59:59')]
], {
    'fields': ['id', 'name', 'pos_reference', 'amount_total', 'date_order', 'create_date', 'session_id', 'config_id'],
    'order': 'create_date asc'
})

total_by_create = sum(o['amount_total'] for o in orders)
print(f"Total orders by create_date (Oct 12 - Oct 18): {len(orders)} orders, Total: {total_by_create:,.2f}")

# Group by shop (config)
by_config = {}
for o in orders:
    cfg = o['config_id'][1]
    by_config.setdefault(cfg, []).append(o)

for cfg, cfg_orders in by_config.items():
    print(f"  Config: {cfg} -> {len(cfg_orders)} orders, Total: {sum(o['amount_total'] for o in cfg_orders):,.2f}")

# Check create_date for all orders in October
all_oct = models.execute_kw(db, uid, password, 'pos.order', 'search_read', [
    [('create_date', '>=', '2026-10-01 00:00:00')]
], {
    'fields': ['id', 'name', 'amount_total', 'date_order', 'create_date', 'session_id', 'config_id'],
    'order': 'id asc'
})

print(f"\nTotal orders in Oct: {len(all_oct)}")
