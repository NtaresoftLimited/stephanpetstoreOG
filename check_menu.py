import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('166.1.227.63', username='root', password='kz@j8PbU77r9GZ')
sql = "SELECT id, name::text, parent_id FROM ir_ui_menu WHERE name::text LIKE '%Replenishment%Approvals%';"
stdin, stdout, stderr = ssh.exec_command(f'sudo -u postgres psql Stephans -c "{sql}"')
print("STDOUT:", stdout.read().decode())
ssh.close()
