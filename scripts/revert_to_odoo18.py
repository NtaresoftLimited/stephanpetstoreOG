import paramiko
import sys
import time

HOST = '166.1.227.63'
USER = 'root'
PASSWORD = 'wpo,,CWc2VH^PZ'

def run():
    print(f"Attempting to connect to {HOST}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(HOST, port=22, username=USER, password=PASSWORD, timeout=10)
    except Exception as e:
        print(f"Connection failed: {e}")
        return False

    print("Connected successfully!")
    
    commands = [
        # 1. Stop and disable Odoo 20
        ("Stop Odoo 20", "systemctl stop odoo20-staging.service"),
        ("Disable Odoo 20", "systemctl disable odoo20-staging.service"),
        ("Check Odoo 20 status", "systemctl is-active odoo20-staging.service || true"),
        
        # 2. Check and start Odoo 18
        ("Check Odoo 18 status", "systemctl is-active odoo-stephans.service"),
        ("Restart Odoo 18", "systemctl restart odoo-stephans.service"),
        ("Verify Odoo 18 active", "systemctl is-active odoo-stephans.service"),
        
        # 3. Check Nginx config files
        ("List Nginx enabled sites", "ls -l /etc/nginx/sites-enabled/"),
        ("Check Nginx odoo20 config", "cat /etc/nginx/sites-enabled/stephans_odoo20_web.conf || true"),
    ]

    for label, cmd in commands:
        print(f"\n--- {label} ({cmd}) ---")
        stdin, stdout, stderr = ssh.exec_command(cmd)
        out = stdout.read().decode('utf-8', errors='ignore')
        err = stderr.read().decode('utf-8', errors='ignore')
        if out.strip():
            print(f"[STDOUT]\n{out.strip()}")
        if err.strip():
            print(f"[STDERR]\n{err.strip()}")

    # 4. Modify Nginx config to point stephanspetstore.co.tz directly to Odoo 18 (port 8071)
    reconfigure_nginx_script = r'''python3 -c "
import re

conf_path = '/etc/nginx/sites-available/stephans_odoo20_web.conf'
try:
    with open(conf_path, 'r') as f:
        content = f.read()
    
    # Replace 8079 with 8071
    content_new = re.sub(r'127\.0\.0\.1:8079', '127.0.0.1:8071', content)
    content_new = re.sub(r'odoo20_app', 'odoo18_app', content_new)
    
    with open(conf_path, 'w') as f:
        f.write(content_new)
    print('Updated Nginx config successfully.')
except Exception as e:
    print('Error modifying Nginx:', e)
"
'''
    print("\n--- Updating Nginx upstream to port 8071 (Odoo 18) ---")
    stdin, stdout, stderr = ssh.exec_command(reconfigure_nginx_script)
    print(stdout.read().decode())
    print(stderr.read().decode())

    # Test and reload Nginx
    stdin, stdout, stderr = ssh.exec_command("nginx -t && systemctl reload nginx")
    print("\n--- Nginx Test & Reload ---")
    print(stdout.read().decode())
    print(stderr.read().decode())

    # Check listening ports
    stdin, stdout, stderr = ssh.exec_command("ss -tlpn | grep -E '8071|8079|80|443'")
    print("\n--- Active Listening Ports ---")
    print(stdout.read().decode())

    # Test local curl to Odoo 18
    stdin, stdout, stderr = ssh.exec_command("curl -s -I http://127.0.0.1:8071/web/login | head -n 5")
    print("\n--- Odoo 18 Local HTTP Response ---")
    print(stdout.read().decode())

    ssh.close()
    return True

if __name__ == '__main__':
    run()
