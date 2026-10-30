#!/usr/bin/env python3
import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def main():
    print(f"Checking employees and POS configs on {HOST}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=10)

    queries = [
        ("Administrator (User 2) Groups", "SELECT g.id, g.name::text FROM res_groups g JOIN res_groups_users_rel r ON r.gid = g.id WHERE r.uid = 2 AND g.category_id = 49;"),
        ("All stores and basic employees", "SELECT pc.name::text, e.name::text FROM pos_hr_basic_employee_hr_employee rel JOIN pos_config pc ON pc.id = rel.pos_config_id JOIN hr_employee e ON e.id = rel.hr_employee_id;"),
        ("All stores and advanced employees", "SELECT pc.name::text, e.name::text FROM pos_hr_advanced_employee_hr_employee rel JOIN pos_config pc ON pc.id = rel.pos_config_id JOIN hr_employee e ON e.id = rel.hr_employee_id;"),
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
