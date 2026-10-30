import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('166.1.227.63', username='root', password='kz@j8PbU77r9GZ')
sftp = ssh.open_sftp()
script = """
import xmlrpc.client
models = xmlrpc.client.ServerProxy('http://localhost:8071/xmlrpc/2/object')
common = xmlrpc.client.ServerProxy('http://localhost:8071/xmlrpc/2/common')
uid = common.authenticate('Stephans', 'info@stephanspetstore.co.tz', 'Stephan@3202', {})
if uid:
    print("Authenticated with uid:", uid)
    module_id = models.execute_kw('Stephans', uid, 'Stephan@3202', 'ir.module.module', 'search', [[('name', '=', 'grooming')]])
    if module_id:
        models.execute_kw('Stephans', uid, 'Stephan@3202', 'ir.module.module', 'button_immediate_upgrade', [module_id])
        print("Module upgraded via XMLRPC.")
    else:
        print("Module not found.")
else:
    print("Authentication failed.")
"""
with sftp.file('/tmp/upgrade_rpc.py', 'w') as f:
    f.write(script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("python3 /tmp/upgrade_rpc.py")
print("Output:", stdout.read().decode())
print("Error:", stderr.read().decode())
ssh.close()
