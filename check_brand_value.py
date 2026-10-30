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

res = models.execute_kw(db, uid, password, 'product.template', 'search_read', [[]], {'limit': 1, 'fields': ['name']})
try:
    res = models.execute_kw(db, uid, password, 'product.template', 'search_read', [[]], {'limit': 1, 'fields': ['brand_id']})
    print("brand_id field data:", res)
except Exception as e:
    print("ERROR accessing brand_id:", str(e))
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/check_brand_value.py', 'w') as f:
    f.write(script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('python3 /tmp/check_brand_value.py')
print(stdout.read().decode())
print(stderr.read().decode())
ssh.close()
