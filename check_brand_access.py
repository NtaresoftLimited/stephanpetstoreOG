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

access = models.execute_kw(db, uid, password, 'ir.model.access', 'search_read', [[('model_id.model', '=', 'product.brand')]])
print("product.brand access:", access)
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/check_brand_access.py', 'w') as f:
    f.write(script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('python3 /tmp/check_brand_access.py')
print(stdout.read().decode())
print(stderr.read().decode())
ssh.close()
