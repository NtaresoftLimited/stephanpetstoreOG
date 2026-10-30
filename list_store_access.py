#!/usr/bin/env python3
import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def main():
    print(f"Listing store access control details on {HOST}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=10)

    queries = [
        # Get employees names
        ("All Employees", "SELECT id, name::text FROM hr_employee;"),
        
        # Get Basic Access employees per store
        ("Basic Access Employees per Store", """
            SELECT pc.name::text as store, e.name::text as employee
            FROM pos_hr_basic_employee_hr_employee rel
            JOIN pos_config pc ON pc.id = rel.pos_config_id
            JOIN hr_employee e ON e.id = rel.hr_employee_id;
        """),
        
        # Get Advanced Access employees per store
        ("Advanced Access Employees per Store", """
            SELECT pc.name::text as store, e.name::text as employee
            FROM pos_hr_advanced_employee_hr_employee rel
            JOIN pos_config pc ON pc.id = rel.pos_config_id
            JOIN hr_employee e ON e.id = rel.hr_employee_id;
        """),
        
        # Check active stores
        ("Active Stores", "SELECT id, name::text FROM pos_config WHERE active = t;"),
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
