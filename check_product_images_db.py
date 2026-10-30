import paramiko

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD)
    
    # Check products with/without images
    sql = "SELECT id, name, image_1920 IS NOT NULL as has_image FROM product_template LIMIT 10;"
    print("Product Image Check:")
    stdin, stdout, stderr = client.exec_command(f"su - postgres -c \"psql Stephans -c \\\"{sql}\\\"\"")
    print(stdout.read().decode())
    
    client.close()

if __name__ == "__main__":
    main()
