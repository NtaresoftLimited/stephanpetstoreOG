#!/usr/bin/env python3
import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def main():
    print(f"Detailed NGINX & WebSocket Check on {HOST}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=10)

    commands = [
        # Full Odoo site config
        ("Odoo NGINX Config", "cat /etc/nginx/sites-available/odoo"),
        
        # Check SSL certificates
        ("SSL Certificates", "ls -la /etc/letsencrypt/live/ 2>/dev/null || ls -la /etc/nginx/ssl/ 2>/dev/null || echo 'No SSL certs found'"),
        
        # Check if longpolling port is configured (for WebSocket/live chat)
        ("Odoo Longpolling Check", "grep -i 'longpoll\\|8072\\|gevent' /etc/odoo.conf /etc/nginx/sites-available/odoo 2>/dev/null || echo 'No longpolling config'"),
        
        # DNS resolution test from server
        ("DNS Test", "curl -sI https://stephanspetstore.co.tz 2>&1 | head -10 || echo 'Domain not accessible'"),
    ]

    for name, cmd in commands:
        print(f"\n{'='*60}")
        print(f">>> {name}")
        print(f"{'='*60}")
        stdin, stdout, stderr = client.exec_command(cmd)
        out = stdout.read().decode('utf-8', errors='replace').strip()
        err = stderr.read().decode('utf-8', errors='replace').strip()
        if out:
            print(out)
        if err and "No such file" not in err:
            print(f"STDERR: {err}")

    client.close()

if __name__ == "__main__":
    main()
