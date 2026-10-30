import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('166.1.227.63', username='root', password='wpo,,CWc2VH^PZ')

script = """
import xmlrpc.client
url = 'https://erp.stephanspetstore.co.tz'
db = 'Stephans'
username = 'info@stephanspetstore.co.tz'
password = 'Stephan@3202'

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

# Find the group
group = models.execute_kw(db, uid, password, 'res.groups', 'search_read', [[('name', 'ilike', 'Product Approver')]], {'fields': ['id', 'name']})
if not group:
    # Try finding by external ID if name doesn't match
    group_data = models.execute_kw(db, uid, password, 'ir.model.data', 'search_read', [[('module', '=', 'product_auto_code'), ('name', '=', 'group_product_approver')]], {'fields': ['res_id']})
    if group_data:
        group_id = group_data[0]['res_id']
    else:
        print("Group not found!")
        group_id = None
else:
    group_id = group[0]['id']

if group_id:
    # Add user to the group
    models.execute_kw(db, uid, password, 'res.groups', 'write', [[group_id], {'users': [(4, uid)]}])
    print(f"Added user {uid} to group {group_id}")
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/assign_group.py', 'w') as f:
    f.write(script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('python3 /tmp/assign_group.py')
print(stdout.read().decode())
print(stderr.read().decode())
ssh.close()
