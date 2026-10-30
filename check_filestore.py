#!/usr/bin/env python3
import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def main():
    print(f"Checking filestore permissions on {HOST}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=10)

    checks = [
        # 1. Check filestore ownership
        ("Filestore Ownership", "ls -la /var/lib/odoo/.local/share/Odoo/filestore/"),
        
        # 2. Check Stephans filestore permissions
        ("Stephans Filestore", "ls -la /var/lib/odoo/.local/share/Odoo/filestore/Stephans/ | head -10"),
        
        # 3. Check data_dir in config
        ("Data Dir Config", "grep data_dir /etc/odoo.conf"),
        
        # 4. Check actual files in filestore
        ("Sample Files", "find /var/lib/odoo/.local/share/Odoo/filestore/Stephans -type f | head -5"),
        
        # 5. Check if files are readable
        ("File Permissions Sample", "ls -la /var/lib/odoo/.local/share/Odoo/filestore/Stephans/00/ 2>/dev/null | head -5 || ls -la /var/lib/odoo/.local/share/Odoo/filestore/Stephans/*/ 2>/dev/null | head -10"),
        
        # 6. Count attachments in DB vs filestore
        ("Attachments in DB", "su - postgres -c \"psql Stephans -c \\\"SELECT count(*) FROM ir_attachment WHERE store_fname IS NOT NULL;\\\"\""),
        
        # 7. Check parent directory permissions
        ("Parent Dir Perms", "ls -la /var/lib/odoo/.local/share/Odoo/"),
        
        # 8. Check Odoo user
        ("Odoo User", "id odoo"),
    ]

    for name, cmd in checks:
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
