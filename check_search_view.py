import paramiko

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD)
    
    # 1. Check search_view_id of the action
    sql_action = """
    SELECT a.name, a.search_view_id 
    FROM ir_act_window a 
    JOIN ir_model_data d ON d.res_id = a.id 
    WHERE d.module = 'point_of_sale' AND d.name = 'action_pos_pos_form';
    """
    print("Checking Action search_view_id...")
    stdin, stdout, stderr = client.exec_command(f"su - postgres -c \"psql Stephans -c \\\"{sql_action}\\\"\"")
    print(stdout.read().decode())

    # 2. Find external ID for view with id 2067 (pos.order.list.select) which we saw earlier
    sql_view = """
    SELECT m.name || '.' || d.name AS external_id 
    FROM ir_model_data d
    JOIN ir_module_module m ON d.module = m.id
    WHERE d.res_id = 2067 AND d.model = 'ir.ui.view';
    """
    print("Finding XML ID for view 2067...")
    stdin, stdout, stderr = client.exec_command(f"su - postgres -c \"psql Stephans -c \\\"{sql_view}\\\"\"")
    print(stdout.read().decode())
    
    client.close()

if __name__ == "__main__":
    main()
