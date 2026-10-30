import xmlrpc.client

url = 'https://erp.stephanspetstore.co.tz'
db = 'Stephans'
username = 'info@stephanspetstore.co.tz'
password = 'Stephan@3202'

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

orders = models.execute_kw(db, uid, password, 'pos.order', 'search_read', [
    [('session_id', '=', 603)]
], {
    'fields': ['id', 'name', 'pos_reference', 'amount_total', 'create_date', 'date_order'],
    'order': 'id asc'
})

order_nums = []
for o in orders:
    # name is "Stephan's Pet Store Masaki/2949"
    num = int(o['name'].split('/')[-1])
    order_nums.append((num, o['id'], o['amount_total'], o['create_date']))

# Check if there are any gaps in num sequence
nums_only = [x[0] for x in order_nums]
print(f"Min order num: {min(nums_only)}, Max order num: {max(nums_only)}, Total count: {len(nums_only)}")
gaps = []
for i in range(min(nums_only), max(nums_only)):
    if i not in nums_only:
        gaps.append(i)

print("Sequence gaps in Masaki POS/00603:", gaps)

# Also check Mikocheni session 602
orders_602 = models.execute_kw(db, uid, password, 'pos.order', 'search_read', [
    [('session_id', '=', 602)]
], {
    'fields': ['id', 'name', 'pos_reference', 'amount_total', 'create_date', 'date_order'],
    'order': 'id asc'
})
nums_602 = [int(o['name'].split('/')[-1]) for o in orders_602]
gaps_602 = []
for i in range(min(nums_602), max(nums_602)):
    if i not in nums_602:
        gaps_602.append(i)
print("Sequence gaps in Mikocheni POS/00602:", gaps_602)

