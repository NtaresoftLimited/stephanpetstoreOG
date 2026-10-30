import paramiko

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "wpo,,CWc2VH^PZ"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASSWORD)

print("Stopping odoo-stephans...")
stdin, stdout, stderr = ssh.exec_command("systemctl stop odoo-stephans")
stdout.channel.recv_exit_status()

print("Upgrading grooming module with correct config...")
stdin, stdout, stderr = ssh.exec_command("su - odoo -c '/opt/odoo/odoo-server/odoo-bin -c /etc/odoo/odoo_stephans.conf -d Stephans -u grooming --stop-after-init'")
exit_code = stdout.channel.recv_exit_status()
print("Exit code:", exit_code)
out = stdout.read().decode()
err = stderr.read().decode()
print("STDOUT tail:", out[-500:])
print("STDERR tail:", err[-500:])

print("Starting odoo-stephans...")
stdin, stdout, stderr = ssh.exec_command("systemctl start odoo-stephans")
stdout.channel.recv_exit_status()
print("Service started successfully!")

ssh.close()
