import paramiko

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD)
    
    # Check installed modules
    sql_mods = "SELECT name, state FROM ir_module_module WHERE name = 'product';"
    print("Checking 'product' module state...")
    cmd = f"su - postgres -c \"psql Stephans -c \\\"{sql_mods}\\\"\""
    stdin, stdout, stderr = client.exec_command(cmd)
    print(stdout.read().decode())
    
    # Check if 'product_template' table exists at all
    sql_tbl = "SELECT to_regclass('product_template');"
    print("Checking 'product_template' table...")
    cmd2 = f"su - postgres -c \"psql Stephans -c \\\"{sql_tbl}\\\"\""
    stdin, stdout, stderr = client.exec_command(cmd2)
    print(stdout.read().decode())

    client.close()

if __name__ == "__main__":
    main()
