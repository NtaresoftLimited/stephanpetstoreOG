#!/usr/bin/env python3
import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def main():
    print(f"Inspecting POS config fields on {HOST}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=10)

    queries = [
        # List all fields of pos.config that might be related to access or users
        ("POS Config Fields (Access related)", """
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'pos_config' 
            AND (column_name ILIKE '%user%' OR column_name ILIKE '%access%' OR column_name ILIKE '%group%' OR column_name ILIKE '%employee%' OR column_name ILIKE '%authorized%');
        """),
        
        # List all stores (pos.config)
        ("List of Stores (pos.config)", """
            SELECT id, name::text, active 
            FROM pos_config;
        """),
        
        # Check if there is a module or specific field for 'Assign Access Control'
        ("Fields containing 'access' in ir_model_fields for pos.config", """
            SELECT name, field_description::text 
            FROM ir_model_fields 
            WHERE model = 'pos.config' AND (name ILIKE '%access%' OR field_description::text ILIKE '%access%');
        """),
        
        # Check for related models that might handle employee access to POS
        ("Models related to POS and Employees/Users", """
            SELECT model, name::text 
            FROM ir_model 
            WHERE model ILIKE 'pos%' AND (model ILIKE '%user%' OR model ILIKE '%employee%' OR model ILIKE '%access%');
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
