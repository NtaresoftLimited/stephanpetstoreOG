import paramiko
import time

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "wpo,,CWc2VH^PZ"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASSWORD)

print("Stopping odoo-stephans...")
stdin, stdout, stderr = ssh.exec_command("systemctl stop odoo-stephans")
stdout.channel.recv_exit_status()

print("Upgrading grooming module via odoo-bin...")
stdin, stdout, stderr = ssh.exec_command("su - odoo -c '/opt/odoo/odoo-server/odoo-bin -c /etc/odoo.conf -d Stephans -u grooming --stop-after-init'")
exit_code = stdout.channel.recv_exit_status()
print("Exit code:", exit_code)
out = stdout.read().decode()
err = stderr.read().decode()
if "ERROR" in out or "ERROR" in err or exit_code != 0:
    print("STDOUT:", out[-1000:])
    print("STDERR:", err[-1000:])
else:
    print("Upgrade successful!")

print("Starting odoo-stephans...")
stdin, stdout, stderr = ssh.exec_command("systemctl start odoo-stephans")
stdout.channel.recv_exit_status()
print("Service started successfully!")

ssh.close()
