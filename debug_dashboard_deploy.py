import paramiko

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD)
    
    # 1. Check parent menu XML ID
    sql_parent = "SELECT module, name FROM ir_model_data WHERE res_id = 431 AND model = 'ir.ui.menu';"
    print("Parent Menu (431) XML ID:")
    stdin, stdout, stderr = client.exec_command(f"su - postgres -c \"psql Stephans -c \\\"{sql_parent}\\\"\"")
    print(stdout.read().decode())
    
    # 2. Check if Action was created
    sql_action = "SELECT id, name, tag FROM ir_act_client WHERE tag = 'custom_pos_dashboard';"
    print("\nClient Action 'custom_pos_dashboard':")
    stdin, stdout, stderr = client.exec_command(f"su - postgres -c \"psql Stephans -c \\\"{sql_action}\\\"\"")
    print(stdout.read().decode())
    
    # 3. Check if Menu exists (anywhere)
    sql_menu = "SELECT id, name, parent_id, action FROM ir_ui_menu WHERE name->>'en_US' = 'Dashboard' ORDER BY id DESC LIMIT 5;"
    print("\nUse of 'Dashboard' in Menus (Newest first):")
    stdin, stdout, stderr = client.exec_command(f"su - postgres -c \"psql Stephans -c \\\"{sql_menu}\\\"\"")
    print(stdout.read().decode())

    client.close()

if __name__ == "__main__":
    main()
