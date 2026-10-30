import paramiko

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD)
    
    # Check ir_model_fields for image_1920
    sql = """
    SELECT name, model, store, type 
    FROM ir_model_fields 
    WHERE model = 'product.template' AND name LIKE 'image%';
    """
    
    print("Checking image fields in ir_model_fields...")
    cmd = f"su - postgres -c \"psql Stephans -c \\\"{sql}\\\"\""
    stdin, stdout, stderr = client.exec_command(cmd)
    print(stdout.read().decode())
    
    client.close()

if __name__ == "__main__":
    main()
