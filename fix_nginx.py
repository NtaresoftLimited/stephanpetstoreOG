
import paramiko
import sys

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

NGINX_CONFIG = """upstream odoo {
    server 127.0.0.1:8069;
}
upstream odoochat {
    server 127.0.0.1:8072;
}

server {
    listen 80;
    server_name _;
    
    # Proxy Headers
    proxy_read_timeout 720s;
    proxy_connect_timeout 720s;
    proxy_send_timeout 720s;
    
    # Common Headers
    proxy_set_header X-Forwarded-Host $host;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto https;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header Host $host;

    # Gzip
    gzip on;
    gzip_types text/css text/less text/plain text/xml application/xml application/json application/javascript;

    # Websocket / Longpolling
    location /websocket {
        proxy_pass http://odoochat;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header Host $host;
    }

    # Main Odoo
    location / {
        proxy_pass http://odoo;
        proxy_redirect off;
    }
}
"""

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print(f"Connecting to {HOST}...")
        client.connect(HOST, username=USER, password=PASSWORD, timeout=10)
        
        # 1. Write Nginx Config
        print(">>> Writing new Nginx config...")
        sftp = client.open_sftp()
        with sftp.file("/etc/nginx/sites-enabled/odoo", "w") as f:
            f.write(NGINX_CONFIG)
        sftp.close()
        
        # 2. Test Nginx Config
        print(">>> Testing Nginx configuration...")
        stdin, stdout, stderr = client.exec_command("nginx -t")
        print(stdout.read().decode())
        print(stderr.read().decode())
        
        # 3. Reload Nginx
        print(">>> Reloading Nginx...")
        client.exec_command("systemctl reload nginx")
        
        # 4. Restart Odoo (to clear any stuck workers)
        print(">>> Restarting Odoo...")
        client.exec_command("systemctl restart odoo")
        
        print("Done! Websockets should now be routed to port 8072.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    main()
