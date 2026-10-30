#!/usr/bin/env python3
"""
Remove Cloudflare config from NGINX - using echo instead of SFTP
"""
import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

# NGINX config WITHOUT Cloudflare - escaped for shell
NGINX_CONFIG = '''upstream odoo {
    server 127.0.0.1:8069;
}

upstream odoo-chat {
    server 127.0.0.1:8072;
}

map \\$http_upgrade \\$connection_upgrade {
    default upgrade;
    \\'\\'      close;
}

server {
    listen 80;
    server_name _;

    proxy_read_timeout 720s;
    proxy_connect_timeout 720s;
    proxy_send_timeout 720s;

    proxy_buffers 16 64k;
    proxy_buffer_size 128k;

    proxy_set_header X-Forwarded-Host \\$host;
    proxy_set_header X-Forwarded-For \\$proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto \\$scheme;
    proxy_set_header X-Real-IP \\$remote_addr;
    proxy_set_header Host \\$host;

    proxy_http_version 1.1;
    proxy_set_header Upgrade \\$http_upgrade;
    proxy_set_header Connection \\$connection_upgrade;

    location /longpolling {
        proxy_pass http://odoo-chat;
        proxy_redirect off;
    }

    location /websocket {
        proxy_pass http://odoo-chat;
        proxy_redirect off;
    }

    location / {
        proxy_pass http://odoo;
        proxy_redirect off;
    }

    gzip on;
    gzip_types text/css text/less text/plain text/xml application/xml application/json application/javascript;
}
'''

def main():
    print("Removing Cloudflare config from NGINX...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(HOST, username=USER, password=PASSWORD, timeout=30)
    except Exception as e:
        print(f"Connection failed: {e}")
        return

    # Write config using cat
    print(">>> Writing new NGINX config...")
    cmd = f"cat > /etc/nginx/sites-available/odoo << 'EOFCONFIG'\n{NGINX_CONFIG.replace(chr(92)+chr(36), chr(36)).replace(chr(92)+chr(39)+chr(92)+chr(39), chr(39)+chr(39))}\nEOFCONFIG"
    
    # Simpler approach - just write a basic config
    simple_config = """upstream odoo {
    server 127.0.0.1:8069;
}

server {
    listen 80;
    server_name _;

    proxy_read_timeout 720s;
    proxy_connect_timeout 720s;
    proxy_send_timeout 720s;

    proxy_set_header X-Forwarded-Host $host;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header Host $host;

    location / {
        proxy_pass http://odoo;
        proxy_redirect off;
    }

    gzip on;
    gzip_types text/css text/less text/plain text/xml application/xml application/json application/javascript;
}
"""
    
    stdin, stdout, stderr = client.exec_command("cat > /etc/nginx/sites-available/odoo << 'EOF'\n" + simple_config + "\nEOF")
    stdout.channel.recv_exit_status()
    print("   Done!")

    # Test
    print(">>> Testing NGINX...")
    stdin, stdout, stderr = client.exec_command("nginx -t")
    print(stderr.read().decode('utf-8', errors='replace').strip())

    # Reload
    print(">>> Reloading NGINX...")
    stdin, stdout, stderr = client.exec_command("systemctl reload nginx")
    stdout.channel.recv_exit_status()
    print("   Done!")

    client.close()
    
    print("\n" + "="*60)
    print("CLOUDFLARE REMOVED!")
    print("="*60)

if __name__ == "__main__":
    main()
