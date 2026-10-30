import paramiko

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD)
    
    # helper to find external id
    sql = """
    SELECT m.name || '.' || d.name AS external_id, v.name AS view_name, v.type
    FROM ir_ui_view v
    JOIN ir_model_data d ON d.res_id = v.id AND d.model = 'ir.ui.view'
    JOIN ir_module_module m ON d.module = m.id
    WHERE v.model = 'pos.order'
    ORDER BY v.type;
    """
    
    print("Listing POS Order Views...")
    stdin, stdout, stderr = client.exec_command(f"su - postgres -c \"psql Stephans -c \\\"{sql}\\\"\"")
    print(stdout.read().decode())
    
    sql_action = """
    SELECT m.name || '.' || d.name AS external_id, a.name AS action_name
    FROM ir_act_window a
    JOIN ir_model_data d ON d.res_id = a.id AND d.model = 'ir.actions.act_window'
    JOIN ir_module_module m ON d.module = m.id
    WHERE a.res_model = 'pos.order';
    """
    print("\nListing POS Order Actions...")
    stdin, stdout, stderr = client.exec_command(f"su - postgres -c \"psql Stephans -c \\\"{sql_action}\\\"\"")
    print(stdout.read().decode())

    client.close()

if __name__ == "__main__":
    main()
