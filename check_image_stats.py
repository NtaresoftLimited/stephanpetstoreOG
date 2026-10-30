import paramiko

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD)
    
    # query to count products with images vs without
    sql = """
    SELECT count(id) as total, 
           count(case when image_1920 is not null then 1 end) as with_image 
    FROM product_template;
    """
    print(f"Executing: {sql}")
    cmd = f"su - postgres -c \"psql Stephans -c \\\"{sql}\\\"\""
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
