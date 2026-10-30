import paramiko

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD)
    
    # Check columns of product_template
    sql = """
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_name = 'product_template' 
      AND column_name LIKE 'image%';
    """
    
    cmd = f"su - postgres -c \"psql Stephans -c \\\"{sql}\\\"\""
    stdin, stdout, stderr = client.exec_command(cmd)
    
    print(stdout.read().decode())
    
    client.close()

if __name__ == "__main__":
    main()
