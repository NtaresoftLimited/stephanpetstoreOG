import paramiko

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD)
    
    # Check IR_MODEL_DATA for 2067 again, broadly
    sql = "SELECT module, name FROM ir_model_data WHERE res_id = 2067 AND model = 'ir.ui.view';"
    print("Checking ir_model_data for 2067...")
    stdin, stdout, stderr = client.exec_command(f"su - postgres -c \"psql Stephans -c \\\"{sql}\\\"\"")
    print(stdout.read().decode())

    # Check priorities
    sql_prio = "SELECT id, name, priority FROM ir_ui_view WHERE model = 'pos.order' AND type = 'search' ORDER BY priority, id;"
    print("Checking view priorities...")
    stdin, stdout, stderr = client.exec_command(f"su - postgres -c \"psql Stephans -c \\\"{sql_prio}\\\"\"")
    print(stdout.read().decode())
    
    client.close()

if __name__ == "__main__":
    main()
