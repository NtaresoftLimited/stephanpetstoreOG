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

arch_db = '''<data>
            <xpath expr="//field[@name='categ_id']" position="attributes">
                <attribute name="required">1</attribute>
            </xpath>
            <xpath expr="//field[@name='is_storable']" position="attributes">
                <attribute name="required">1</attribute>
            </xpath>
        </data>'''

views = models.execute_kw(db, uid, password, 'ir.ui.view', 'search_read', [[('name', '=', 'product.template.form.view.inherit.brand')]], {'fields': ['id', 'arch_db']})
if views:
    view_id = views[0]['id']
    models.execute_kw(db, uid, password, 'ir.ui.view', 'write', [[view_id], {'arch_db': arch_db}])
    print('Successfully removed brand_id from view to prevent crash.')
else:
    print('View not found!')
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/remove_brand_view.py', 'w') as f:
    f.write(script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('python3 /tmp/remove_brand_view.py')
print(stdout.read().decode())
print(stderr.read().decode())
ssh.close()
