import paramiko

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD)
    
    # Check specific external IDs
    sql = """
    SELECT module, name, model, res_id 
    FROM ir_model_data 
    WHERE module = 'point_of_sale' 
      AND name IN ('view_pos_order_search', 'action_pos_pos_form');
    """
    
    print("Verifying External IDs...")
    stdin, stdout, stderr = client.exec_command(f"su - postgres -c \"psql Stephans -c \\\"{sql}\\\"\"")
    print(stdout.read().decode())
    
    client.close()

if __name__ == "__main__":
    main()
