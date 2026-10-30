#!/usr/bin/env python3
import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def main():
    print(f"Checking Jonas M user ID and current rules on {HOST}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=10)

    queries = [
        ("Check Jonas M User ID", "SELECT id, user_id, name::text FROM hr_employee WHERE id = 2;"),
        ("Check User login", "SELECT id, login FROM res_users WHERE id = (SELECT user_id FROM hr_employee WHERE id = 2);"),
        ("Check Record Rules for pos.config", "SELECT id, name::text, active FROM ir_rule WHERE model_id = (SELECT id FROM ir_model WHERE model = 'pos.config');"),
        ("Check Rules Content", "SELECT name::text, domain_force FROM ir_rule WHERE model_id = (SELECT id FROM ir_model WHERE model = 'pos.config');"),
        ("Check POS HR basic rel", "SELECT * FROM pos_hr_basic_employee_hr_employee WHERE hr_employee_id = 2;"),
        ("Check POS HR advanced rel", "SELECT * FROM pos_hr_advanced_employee_hr_employee WHERE hr_employee_id = 2;"),
    ]

    for name, query in queries:
        print(f"\n{'='*60}")
        print(f">>> {name}")
        print(f"{'='*60}")
        clean_query = ' '.join(query.split())
        cmd = f"su - postgres -c \"psql Stephans -c \\\"{clean_query}\\\"\""
        stdin, stdout, stderr = client.exec_command(cmd)
        out = stdout.read().decode('utf-8', errors='replace').strip()
        err = stderr.read().decode('utf-8', errors='replace').strip()
        if out:
            print(out)
        if err and "ERROR" in err:
            print(f"STDERR: {err}")

    client.close()

if __name__ == "__main__":
    main()
