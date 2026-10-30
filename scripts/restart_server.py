import paramiko
import time

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "wpo,,CWc2VH^PZ"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASSWORD)

print("Clearing temporary cache files and restarting odoo-stephans...")
ssh.exec_command("rm -rf /tmp/odoo* /tmp/test*")
ssh.exec_command("systemctl restart odoo-stephans")

time.sleep(5)
stdin, stdout, stderr = ssh.exec_command("systemctl status odoo-stephans")
print(stdout.read().decode())
ssh.close()
