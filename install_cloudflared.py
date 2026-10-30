#!/usr/bin/env python3
import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def main():
    print(f"Installing Cloudflare Tunnel on {HOST}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=30)

    commands = [
        # 1. Add GPG key
        ("Adding GPG Key", "mkdir -p --mode=0755 /usr/share/keyrings && curl -fsSL https://pkg.cloudflare.com/cloudflare-public-v2.gpg | tee /usr/share/keyrings/cloudflare-public-v2.gpg >/dev/null"),
        
        # 2. Add Repo
        ("Adding Repository", "echo 'deb [signed-by=/usr/share/keyrings/cloudflare-public-v2.gpg] https://pkg.cloudflare.com/cloudflared any main' | tee /etc/apt/sources.list.d/cloudflared.list"),
        
        # 3. Update & Install
        ("Installing cloudflared", "apt-get update && apt-get install -y cloudflared"),
        
        # 4. Install Service (Token)
        ("Installing Service", "cloudflared service install eyJhIjoiNDA4MGE0ZWIzZjc3M2I3NTc5NTRhZjU0ZjkxMDgyMDkiLCJ0IjoiMDBlNjIwZDktNTRiZi00ZTRlLTkyZjctZGQ4OWEzZGUzYjkwIiwicyI6IlpXSTNaamxqTVRjdE5EZ3dNQzAwTWpVMkxUaG1Nak10WXpZNE1qbGtNelU1WkdJMSJ9"),
        
        # 5. Verify
        ("Verifying Service", "systemctl status cloudflared --no-pager")
    ]

    for name, cmd in commands:
        print(f"\n>>> {name}")
        stdin, stdout, stderr = client.exec_command(cmd)
        exit_code = stdout.channel.recv_exit_status()
        out = stdout.read().decode('utf-8', errors='replace').strip()
        err = stderr.read().decode('utf-8', errors='replace').strip()
        
        if out:
            print(out)
        if exit_code != 0:
            print(f"Exit Code: {exit_code}")
            if err:
                print(f"STDERR: {err}")
        elif err: # sometimes err has info even on success
             print(f"STDERR (Info): {err}")

    client.close()
    
    print("\n" + "="*60)
    print("CLOUDFLARE TUNNEL INSTALLED!")
    print("="*60)

if __name__ == "__main__":
    main()
