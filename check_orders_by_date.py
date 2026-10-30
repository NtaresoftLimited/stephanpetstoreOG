import xmlrpc.client
from datetime import datetime

url = 'https://erp.stephanspetstore.co.tz'
db = 'Stephans'
username = 'info@stephanspetstore.co.tz'
password = 'Stephan@3202'

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

# Fetch all orders from session 603
orders_603 = models.execute_kw(db, uid, password, 'pos.order', 'search_read', [
    [('session_id', '=', 603)]
], {
    'fields': ['id', 'name', 'pos_reference', 'state', 'amount_total', 'date_order', 'create_date', 'write_date'],
    'order': 'date_order asc'
})

print(f"Total orders in session 603: {len(orders_603)}")

# Group orders by day
by_day = {}
for o in orders_603:
    day = o['date_order'][:10]
    by_day.setdefault(day, []).append(o)

for day, day_orders in sorted(by_day.items()):
    day_total = sum(o['amount_total'] for o in day_orders)
    print(f"Day: {day} | Count: {len(day_orders):2d} | Total: {day_total:12,.2f}")

# Check orders specifically from Oct 12 to Oct 18 (last week: Monday Oct 12 to Sunday Oct 18)
last_week_orders = [o for o in orders_603 if '2026-10-12' <= o['date_order'][:10] <= '2026-10-18']
last_week_total = sum(o['amount_total'] for o in last_week_orders)
print(f"\nTotal last week (Oct 12 - Oct 18) in session 603: {last_week_total:,.2f} ({len(last_week_orders)} orders)")

# Check session 602 as well
orders_602 = models.execute_kw(db, uid, password, 'pos.order', 'search_read', [
    [('session_id', '=', 602)]
], {
    'fields': ['id', 'name', 'pos_reference', 'state', 'amount_total', 'date_order'],
    'order': 'date_order asc'
})
last_week_602 = [o for o in orders_602 if '2026-10-12' <= o['date_order'][:10] <= '2026-10-18']
print(f"Total last week (Oct 12 - Oct 18) in session 602: {sum(o['amount_total'] for o in last_week_602):,.2f} ({len(last_week_602)} orders)")

# Now check if there is any combination or specific sum = 5,651,000
# Let's check running sum or subsets
print("\n--- Let's check sums for Saturday Oct 17 or whole week ---")
