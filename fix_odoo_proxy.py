import paramiko

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    print(f"Connecting to {HOST}...")
    client.connect(HOST, username=USER, password=PASSWORD, timeout=10)

    # Update odoo.conf to enable proxy_mode
    print(">>> Enabling proxy_mode in Odoo config...")
    cmd = "grep -q 'proxy_mode' /etc/odoo/odoo.conf && sed -i 's/.*proxy_mode.*/proxy_mode = True/' /etc/odoo/odoo.conf || sed -i '/\\[options\\]/a proxy_mode = True' /etc/odoo/odoo.conf"
    stdin, stdout, stderr = client.exec_command(cmd)
    
    # Also check if it exists in another location just in case
    cmd2 = "if [ -f /etc/odoo-server.conf ]; then grep -q 'proxy_mode' /etc/odoo-server.conf && sed -i 's/.*proxy_mode.*/proxy_mode = True/' /etc/odoo-server.conf || sed -i '/\\[options\\]/a proxy_mode = True' /etc/odoo-server.conf; fi"
    client.exec_command(cmd2)

    print(">>> Reading Odoo config...")
    stdin, stdout, stderr = client.exec_command("cat /etc/odoo/odoo.conf")
    print(stdout.read().decode())

    print(">>> Restarting Odoo...")
    client.exec_command("systemctl restart odoo")
    print("Done!")

except Exception as e:
    print(f"Error: {e}")
finally:
    client.close()
