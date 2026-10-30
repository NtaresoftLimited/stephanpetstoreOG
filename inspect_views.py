import paramiko

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD)
    
    # Check for inherited views on point_of_sale.OrderReceipt
    # The base view ID for OrderReceipt is needed
    sql = """
    SELECT v.id, v.name, v.key, v.active 
    FROM ir_ui_view v 
    JOIN ir_ui_view p ON v.inherit_id = p.id 
    WHERE p.key = 'point_of_sale.OrderReceipt' OR p.name = 'point_of_sale.OrderReceipt';
    """
    
    cmd = f"su - postgres -c \"psql Stephans -c \\\"{sql}\\\"\""
    
    print("Checking for inherited views on OrderReceipt...")
    stdin, stdout, stderr = client.exec_command(cmd)
    print(stdout.read().decode())
    
    # Also check for views belonging to custom_pos_reports
    sql2 = "SELECT id, name, key FROM ir_ui_view WHERE key LIKE '%%custom_pos_reports%%';"
    cmd2 = f"su - postgres -c \"psql Stephans -c \\\"{sql2}\\\"\""
    print("\nChecking for views with 'custom_pos_reports' in key...")
    stdin, stdout, stderr = client.exec_command(cmd2)
    print(stdout.read().decode())
    
    client.close()

if __name__ == "__main__":
    main()
