#!/usr/bin/env python3
import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def main():
    print(f"Checking NGINX, Cloudflare & WebSocket on {HOST}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(HOST, username=USER, password=PASSWORD, timeout=10)
    except Exception as e:
        print(f"SSH Failed: {e}")
        sys.exit(1)

    commands = [
        # 1. Check if NGINX is installed and running
        ("NGINX Status", "systemctl status nginx --no-pager 2>&1 || echo 'NGINX not installed'"),
        
        # 2. NGINX Config Test
        ("NGINX Config Test", "nginx -t 2>&1 || echo 'NGINX config test failed or not installed'"),
        
        # 3. Check NGINX sites-enabled
        ("NGINX Sites Enabled", "ls -la /etc/nginx/sites-enabled/ 2>/dev/null || echo 'No sites-enabled dir'"),
        
        # 4. Check for Cloudflare IPs in config (common pattern)
        ("Cloudflare in NGINX Config", "grep -r 'cloudflare\\|real_ip\\|cf-connecting-ip' /etc/nginx/ 2>/dev/null | head -5 || echo 'No Cloudflare config found'"),
        
        # 5. Check WebSocket upgrade headers in NGINX
        ("WebSocket Config in NGINX", "grep -r 'upgrade\\|Upgrade\\|websocket' /etc/nginx/ 2>/dev/null | head -10 || echo 'No WebSocket config found'"),
        
        # 6. Check ports listening (80, 443, 8069)
        ("Ports Listening", "ss -tuln | grep -E ':80|:443|:8069'"),
        
        # 7. Check current NGINX main site config
        ("Main Site Config", "cat /etc/nginx/sites-enabled/default 2>/dev/null || cat /etc/nginx/sites-enabled/*.conf 2>/dev/null | head -50 || echo 'No config found'"),
        
        # 8. Test local connection to Odoo
        ("Local Odoo Test", "curl -sI http://127.0.0.1:8069/ | head -5"),
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
        if err:
            print(f"STDERR: {err}")

    client.close()

if __name__ == "__main__":
    main()
