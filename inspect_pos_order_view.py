import paramiko

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD)
    
    # Get the search view for pos.order
    sql = """
    SELECT id, name, key, type, arch_db FROM ir_ui_view 
    WHERE model = 'pos.order' AND type = 'search';
    """
    
    cmd = f"su - postgres -c \"psql Stephans -c \\\"{sql}\\\"\""
    
    print("Fetching pos.order search view...")
    stdin, stdout, stderr = client.exec_command(cmd)
    print(stdout.read().decode())
    
    client.close()

if __name__ == "__main__":
    main()
