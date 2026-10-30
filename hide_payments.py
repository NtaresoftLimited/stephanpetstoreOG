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

def hide_menu(xml_id):
    module, name = xml_id.split('.')
    menu_data = models.execute_kw(db, uid, password, 'ir.model.data', 'search_read', [[('module', '=', module), ('name', '=', name)]], {'fields': ['res_id']})
    if menu_data:
        res_id = menu_data[0]['res_id']
        models.execute_kw(db, uid, password, 'ir.ui.menu', 'write', [[res_id], {'active': False}])
        print(f'Deactivated {xml_id}')
    else:
        print(f'Menu {xml_id} not found')

hide_menu('point_of_sale.menu_pos_payment')
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/hide_payments.py', 'w') as f:
    f.write(script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('python3 /tmp/hide_payments.py')
print(stdout.read().decode())
print(stderr.read().decode())
ssh.close()
