#!/usr/bin/env python3
import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def main():
    print(f"Final verification on {HOST}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=10)

    checks = [
        ("Ports Listening", "ss -tuln | grep -E ':80|:8069|:8072'"),
        ("NGINX Status", "systemctl is-active nginx"),
        ("Odoo Status", "systemctl is-active odoo"),
        ("Test Main Site via NGINX", "curl -sI http://127.0.0.1/ | head -3"),
        ("Test Longpolling via NGINX", "curl -sI http://127.0.0.1/longpolling/poll | head -3"),
        ("Test WebSocket Upgrade Headers in NGINX", "grep -E 'Upgrade|upgrade|websocket' /etc/nginx/sites-available/odoo | head -5"),
        ("Test Cloudflare Headers in NGINX", "grep -E 'real_ip|CF-Connecting' /etc/nginx/sites-available/odoo | head -3"),
    ]

    for name, cmd in checks:
        print(f"\n>>> {name}")
        stdin, stdout, stderr = client.exec_command(cmd)
        print(stdout.read().decode('utf-8', errors='replace').strip())

    client.close()
    
    print("\n" + "="*60)
    print("VERIFICATION COMPLETE!")
    print("="*60)

if __name__ == "__main__":
    main()
