import paramiko

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD)
    
    # List all columns
    sql = """
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_name = 'product_template'
    ORDER BY column_name;
    """
    
    print("Listing all columns in product_template...")
    cmd = f"su - postgres -c \"psql Stephans -c \\\"{sql}\\\"\""
    stdin, stdout, stderr = client.exec_command(cmd)
    
    out = stdout.read().decode()
    if out:
        print(out)
    else:
        print("NO OUTPUT? stderr:", stderr.read().decode())
    
    client.close()

if __name__ == "__main__":
    main()
