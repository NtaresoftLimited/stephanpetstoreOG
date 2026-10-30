#!/usr/bin/env python3
import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def main():
    print(f"Cleaning up and restarting Odoo on {HOST}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=10)

    commands = [
        # 1. Stop service
        "systemctl stop odoo",
        
        # 2. Kill ALL odoo processes
        "pkill -9 -f 'odoo-bin'",
        
        # 3. Wait a second
        "sleep 2",
        
        # 4. Verify no processes
        "pgrep -f 'odoo-bin' || echo 'No odoo processes running'",
        
        # 5. Check ports are free
        "ss -tuln | grep -E ':8069|:8072' || echo 'Ports 8069 and 8072 are free'",
        
        # 6. Start service properly
        "systemctl start odoo",
        
        # 7. Wait for startup
        "sleep 5",
        
        # 8. Verify status
        "systemctl status odoo --no-pager",
        
        # 9. Verify ports
        "ss -tuln | grep -E ':8069|:8072'"
    ]

    for cmd in commands:
        print(f"\n>>> {cmd}")
        stdin, stdout, stderr = client.exec_command(cmd)
        stdout.channel.recv_exit_status()  # Wait for command
        out = stdout.read().decode('utf-8', errors='replace').strip()
        err = stderr.read().decode('utf-8', errors='replace').strip()
        if out:
            print(out)
        if err:
            print(f"STDERR: {err}")

    client.close()
    print("\n" + "="*60)
    print("CLEANUP COMPLETE!")
    print("="*60)

if __name__ == "__main__":
    main()
