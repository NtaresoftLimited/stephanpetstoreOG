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

fields = models.execute_kw(db, uid, password, 'ir.model.fields', 'search_read', [[('model', '=', 'product.template'), ('name', '=', 'public_categ_ids')]], {'fields': ['required', 'field_description']})
print("public_categ_ids:", fields)
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/check_field.py', 'w') as f:
    f.write(script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('python3 /tmp/check_field.py')
print(stdout.read().decode())
print(stderr.read().decode())
ssh.close()
