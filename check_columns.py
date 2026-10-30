import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('166.1.227.63', username='root', password='wpo,,CWc2VH^PZ')
sql = "SELECT column_name FROM information_schema.columns WHERE table_name = 'pos_payment_method';"
stdin, stdout, stderr = ssh.exec_command(f"sudo -u postgres psql Stephans -c \"{sql}\"")
print(stdout.read().decode())
ssh.close()
