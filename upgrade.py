import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('166.1.227.63', username='root', password='kz@j8PbU77r9GZ')

print("=== STEP 1: Stop Odoo ===")
stdin, stdout, stderr = ssh.exec_command('systemctl stop odoo')
stdout.channel.recv_exit_status()
time.sleep(3)

print("=== STEP 2: Check port 8069 is free ===")
stdin, stdout, stderr = ssh.exec_command('ss -tlnp | grep 8069')
print(stdout.read().decode() or "Port 8069 is FREE - good!")

print("=== STEP 3: Upgrade grooming module ===")
# db_host=False means Unix socket auth - must run as 'odoo' user using su
cmd = "su odoo -s /bin/bash -c '/usr/bin/python3 /opt/odoo/odoo-server/odoo-bin -c /etc/odoo.conf -u grooming -d Stephans --stop-after-init'"
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=120)
exit_code = stdout.channel.recv_exit_status()
out = stdout.read().decode()
err = stderr.read().decode()
print("Exit code:", exit_code)
print("Stdout:", out[-2000:] if len(out) > 2000 else out)
# Check for errors and success
if 'ERROR' in err:
    lines = [l for l in err.split('\n') if 'ERROR' in l or 'error' in l.lower()]
    print("ERRORS FOUND:")
    for l in lines[:20]:
        print(l)
else:
    print("Stderr (last 1000):", err[-1000:] if len(err) > 1000 else err)

print("=== STEP 4: Start Odoo ===")
ssh.exec_command('systemctl start odoo')
time.sleep(3)

print("=== STEP 5: Check Odoo is running ===")
stdin, stdout, stderr = ssh.exec_command('systemctl is-active odoo')
print("Odoo status:", stdout.read().decode().strip())

ssh.close()
