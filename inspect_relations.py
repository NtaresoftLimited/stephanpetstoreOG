#!/usr/bin/env python3
import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def main():
    print(f"Inspecting employee and user relations on {HOST}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=10)

    # We found x_pos_config_res_users_rel and we want to check hr_employee list correctly.
    # The previous attempt to list hr_employee failed silently or with error.
    
    queries = [
        # List content of x_pos_config_res_users_rel
        ("POS Config to Users Relation (Custom)", "SELECT * FROM x_pos_config_res_users_rel;"),
        
        # Check if hr_employee table has any data
        ("Count of Employees", "SELECT count(*) FROM hr_employee;"),
        
        # Check columns of hr_employee
        ("Employee Table Columns", "SELECT column_name FROM information_schema.columns WHERE table_name = 'hr_employee' LIMIT 10;"),
        
        # Try to find if 'pos_config_hr_employee_rel' exists (maybe different naming)
        ("Relation tables with employee", "SELECT tablename FROM pg_tables WHERE tablename LIKE '%employee%' AND tablename LIKE '%pos%';"),
        
        # Check for field attributes of basic_employee_ids and advanced_employee_ids
        ("Employee Access Fields Details", """
            SELECT name, relation, relation_table, column1, column2 
            FROM ir_model_fields 
            WHERE model = 'pos.config' AND name IN ('basic_employee_ids', 'advanced_employee_ids');
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

    client.close()

if __name__ == "__main__":
    main()
