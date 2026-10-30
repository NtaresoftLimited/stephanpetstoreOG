#!/usr/bin/env python3
import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def main():
    print(f"Checking employees and access for stores on {HOST}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=10)

    # We found basic_employee_ids and advanced_employee_ids in ir_model_fields for pos.config
    # These are likely Many2many fields. Let's find the relation tables.
    
    queries = [
        # Find the relation tables for these M2M fields
        ("M2M Relation Tables for Employees", """
            SELECT relation 
            FROM ir_model_fields 
            WHERE model = 'pos.config' AND name IN ('basic_employee_ids', 'advanced_employee_ids');
        """),
        
        # Check all relation tables for pos_config to see if we missed any
        ("All Relation Tables for pos_config", """
            SELECT tablename 
            FROM pg_tables 
            WHERE tablename LIKE 'pos_config_%_rel' OR tablename LIKE '%pos_config%';
        """),
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

    # Now let's try to query the content of those fields if we find the tables
    # Based on naming convention they might be pos_config_hr_employee_basic_rel etc.
    # But let's check first.
    
    # Also list some employees to see who they are
    print(f"\n{'='*60}")
    print(">>> List of Employees")
    print(f"{'='*60}")
    cmd = "su - postgres -c \"psql Stephans -c \\\"SELECT id, name::text FROM hr_employee WHERE active = t LIMIT 20;\\\"\""
    stdin, stdout, stderr = client.exec_command(cmd)
    print(stdout.read().decode('utf-8', errors='replace').strip())

    client.close()

if __name__ == "__main__":
    main()
