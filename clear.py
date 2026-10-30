import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('166.1.227.63', username='root', password='kz@j8PbU77r9GZ')
cmd = "su - postgres -c 'psql Stephans -c \"DELETE FROM ir_attachment WHERE url LIKE '\\''%/web/assets/%'\\'';\"'"
stdin, stdout, stderr = ssh.exec_command(cmd)
print("Deleted assets:", stdout.read().decode())
print(stderr.read().decode())

print("Restarting...")
ssh.exec_command('systemctl restart odoo')
ssh.close()
