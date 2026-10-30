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
            <!-- Make Internal Reference readonly -->
            <field name="default_code" position="attributes">
                <attribute name="readonly">1</attribute>
                <attribute name="force_save">0</attribute>
            </field>

            <!-- Add approval field next to Internal Reference -->
            <field name="default_code" position="after">
                <field name="approval_state" readonly="1"/>
            </field>

            <!-- Add Approve / Reset buttons in the header -->
            <header position="inside">
                <button name="action_approve_product" string="Approve" type="object" class="btn btn-primary" invisible="approval_state == 'approved'" groups="base.group_system"/>
                <button name="action_set_to_draft" string="Reset to Draft" type="object" class="btn btn-secondary" invisible="approval_state == 'draft'" groups="base.group_system"/>
            </header>
        </data>'''

models.execute_kw(db, uid, password, 'ir.ui.view', 'write', [[14139], {'arch_db': arch_db}])
print('Successfully updated view 14139 to restrict Approve button to Admins only.')
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/update_view2.py', 'w') as f:
    f.write(script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('python3 /tmp/update_view2.py')
print(stdout.read().decode())
print(stderr.read().decode())
ssh.close()
