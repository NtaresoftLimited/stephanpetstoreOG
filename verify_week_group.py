import paramiko

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD)
    
    # Check context of pos.order actions with xml_id
    sql = """
    SELECT a.id, m.name || '.' || d.name AS xml_id, a.context 
    FROM ir_act_window a
    LEFT JOIN ir_model_data d ON d.res_id = a.id AND d.model = 'ir.actions.act_window'
    LEFT JOIN ir_module_module m ON d.module = m.id
    WHERE a.res_model = 'pos.order';
    """
    print("Checking POS Order Actions Context...")
    cmd = f"su - postgres -c \"psql Stephans -c \\\"{sql}\\\"\""
    
    stdin, stdout, stderr = client.exec_command(cmd)
    print(stdout.read().decode())
    
    client.close()

if __name__ == "__main__":
    main()
