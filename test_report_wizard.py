import xmlrpc.client

url = 'https://erp.stephanspetstore.co.tz'
db = 'Stephans'
username = 'info@stephanspetstore.co.tz'
password = 'Stephan@3202'

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

# Test report data for last week (Monday Oct 12 to Saturday Oct 17)
wiz_id = models.execute_kw(db, uid, password, 'pos.details.wizard', 'create', [{
    'date_start_only': '2026-10-12',
    'date_end_only': '2026-10-17',
}])

data = models.execute_kw(db, uid, password, 'pos.details.wizard', '_get_report_data', [[wiz_id]])
print("Report total sales (Mon-Sat):", f"{data['total_sales']:,.2f}")
print("Report total grooming:", f"{data['total_grooming']:,.2f}")
print("Total orders count:", data['total_orders'])
print("Payments breakdown:")
for p in data['payments']:
    print(f"  {p['method']}: {p['amount']:,.2f}")

# Also check Mon-Sun (2026-10-12 to 2026-10-18)
wiz_id2 = models.execute_kw(db, uid, password, 'pos.details.wizard', 'create', [{
    'date_start_only': '2026-10-12',
    'date_end_only': '2026-10-18',
}])
data2 = models.execute_kw(db, uid, password, 'pos.details.wizard', '_get_report_data', [[wiz_id2]])
print("\nReport total sales (Mon-Sun):", f"{data2['total_sales']:,.2f}")
print("Total orders count (Mon-Sun):", data2['total_orders'])
