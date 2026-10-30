import paramiko

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD)
    
    # Check menus under Point of Sale (usually parent_id refers to the root menu)
    # We first find the root 'Point of Sale' menu
    sql_root = "SELECT id, name FROM ir_ui_menu WHERE name = 'Point of Sale' AND parent_id IS NULL;"
    print("Finding Root POS Menu...")
    stdin, stdout, stderr = client.exec_command(f"su - postgres -c \"psql Stephans -c \\\"{sql_root}\\\"\"")
    root_out = stdout.read().decode()
    print(root_out)
    
    # Assuming root is usually called "Point of Sale", let's list its children
    # If the above query works, we parse the ID. But a broader query is safer.
    
    sql_menus = """
    SELECT id, name, parent_id, action 
    FROM ir_ui_menu 
    WHERE name->>'en_US' ILIKE '%Point of Sale%' 
       OR name->>'en_US' ILIKE '%Dashboard%'
       OR name->>'en_US' ILIKE '%Reporting%'
    LIMIT 50;
    """
    
    print(f"Executing: {sql_menus}")
    cmd = f"su - postgres -c \"psql Stephans -c \\\"{sql_menus}\\\"\""
    stdin, stdout, stderr = client.exec_command(cmd)
    
    out = stdout.read().decode()
    err = stderr.read().decode()
    
    if out:
        print("STDOUT:\n", out)
    if err:
        print("STDERR:\n", err)
    
    client.close()

if __name__ == "__main__":
    main()
