import paramiko

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"
FOOTER_TEXT = "Note: No cash refund, call for item exchange within 24hrs."

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD)
    
    # Update all POS configs that are active (or just all for simplicity)
    # We use a single query to set the footer
    sql = f"UPDATE pos_config SET receipt_footer = '{FOOTER_TEXT}';"
    cmd = f"su - postgres -c \"psql Stephans -c \\\"{sql}\\\"\""
    
    print(f"Executing: {cmd}")
    stdin, stdout, stderr = client.exec_command(cmd)
    print(stdout.read().decode())
    print(stderr.read().decode())
    
    # Verify
    cmd_verify = "su - postgres -c \"psql Stephans -c 'SELECT name, receipt_footer FROM pos_config;'\""
    stdin, stdout, stderr = client.exec_command(cmd_verify)
    print(stdout.read().decode())
    
    client.close()

if __name__ == "__main__":
    main()
