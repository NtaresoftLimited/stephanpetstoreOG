import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('166.1.227.63', username='root', password='wpo,,CWc2VH^PZ')

print("Custom addons with 'approval':")
cmd = "grep -ril 'approval' /opt/odoo/custom-addons/"
stdin, stdout, stderr = ssh.exec_command(cmd)
print(stdout.read().decode())

print("Custom addons with 'approve':")
cmd = "grep -ril 'approve' /opt/odoo/custom-addons/"
stdin, stdout, stderr = ssh.exec_command(cmd)
print(stdout.read().decode())
