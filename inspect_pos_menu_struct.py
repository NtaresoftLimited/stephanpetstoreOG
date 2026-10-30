import paramiko

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD)
    
    sql_children = """
    SELECT id, name, action 
    FROM ir_ui_menu 
    WHERE parent_id = 431
    ORDER BY sequence;
    """
    
    print("Listing Children of Reporting (431)...")
    cmd = f"su - postgres -c \"psql Stephans -c \\\"{sql_children}\\\"\""
    stdin, stdout, stderr = client.exec_command(cmd)
    print(stdout.read().decode())
    
    # 2. Check details of Action 695 and NEW Dashboard menu
    sql_action = """
    SELECT id, name, action 
    FROM ir_ui_menu 
    WHERE parent_id = 431 AND name->>'en_US' = 'Dashboard';
    """
    print("\nChecking for NEW Dashboard Menu...")
    cmd2 = f"su - postgres -c \"psql Stephans -c \\\"{sql_action}\\\"\""
    stdin, stdout, stderr = client.exec_command(cmd2)
    print(stdout.read().decode())

    client.close()

if __name__ == "__main__":
    main()
