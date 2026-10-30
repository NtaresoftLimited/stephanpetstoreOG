import paramiko

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD)
    
    # 1. Search for custom_pos_reports views
    # 2. Search for OrderReceipt views
    sql = """
    SELECT id, name, key, arch_db FROM ir_ui_view 
    WHERE (key LIKE '%%custom_pos_reports%%' OR name LIKE '%%OrderReceipt%%') 
      AND active = true;
    """
    
    cmd = f"su - postgres -c \"psql Stephans -c \\\"{sql}\\\"\""
    
    print("Checking for custom views in DB...")
    stdin, stdout, stderr = client.exec_command(cmd)
    output = stdout.read().decode()
    print(output)
    
    # 3. If found, generate DELETE commands
    if "custom_pos_reports" in output:
        print("\nLINGERING VIEWS DETECTED. Deleting...")
        # Delete only the ones related to our custom module to be safe
        delete_sql = "DELETE FROM ir_ui_view WHERE key LIKE '%%custom_pos_reports.OrderReceipt%%';"
        cmd_del = f"su - postgres -c \"psql Stephans -c \\\"{delete_sql}\\\"\""
        stdin, stdout, stderr = client.exec_command(cmd_del)
        print(stdout.read().decode())
    
    client.close()

if __name__ == "__main__":
    main()
