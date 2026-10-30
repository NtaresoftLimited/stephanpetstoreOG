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

views = models.execute_kw(db, uid, password, 'ir.ui.view', 'search_read', [[('model', '=', 'product.template'), ('arch_db', 'ilike', 'required')]], {'fields': ['id', 'name', 'arch_db']})
for v in views:
    if 'public_categ_ids' in v['arch_db']:
        print(f"FOUND public_categ_ids in view ID: {v['id']}, Name: {v['name']}")
        print(v['arch_db'])
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/find_required2.py', 'w') as f:
    f.write(script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('python3 /tmp/find_required2.py')
print(stdout.read().decode())
print(stderr.read().decode())
ssh.close()
