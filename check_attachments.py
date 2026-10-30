import paramiko

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD)
    
    # Check ir_attachment for product images
    # We look for attachments linked to product.template and field image_1920
    sql = """
    SELECT count(id) as total_attachments
    FROM ir_attachment
    WHERE res_model = 'product.template' 
      AND (res_field LIKE 'image%' OR name LIKE '%.png' OR name LIKE '%.jpg');
    """
    
    print("Checking ir_attachment for Product Images...")
    cmd = f"su - postgres -c \"psql Stephans -c \\\"{sql}\\\"\""
    stdin, stdout, stderr = client.exec_command(cmd)
    
    out = stdout.read().decode()
    print(out)
    
    # Just list a few to see what they look like
    sql_list = """
    SELECT id, name, res_field, res_model, mimetype, file_size 
    FROM ir_attachment 
    WHERE res_model = 'product.template' 
    LIMIT 10;
    """
    cmd2 = f"su - postgres -c \"psql Stephans -c \\\"{sql_list}\\\"\""
    stdin, stdout, stderr = client.exec_command(cmd2)
    print(stdout.read().decode())

    client.close()

if __name__ == "__main__":
    main()
