import paramiko

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD)
    
    # 1. Check views in 'custom_receipts_for_pos'
    sql1 = """
    SELECT v.id, v.name, v.key, v.active, v.arch_db 
    FROM ir_ui_view v 
    JOIN ir_model_data d ON d.res_id = v.id AND d.model = 'ir.ui.view'
    WHERE d.module = 'custom_receipts_for_pos';
    """
    print("Views in 'custom_receipts_for_pos':")
    stdin, stdout, stderr = client.exec_command(f"su - postgres -c \"psql Stephans -c \\\"{sql1}\\\"\"")
    print(stdout.read().decode())

    # 2. Check assets in 'custom_receipts_for_pos'
    sql2 = """
    SELECT name, path_db 
    FROM ir_asset 
    WHERE path_db LIKE '%%custom_receipts_for_pos%%';
    """
    print("\nAssets in 'custom_receipts_for_pos':")
    stdin, stdout, stderr = client.exec_command(f"su - postgres -c \"psql Stephans -c \\\"{sql2}\\\"\"")
    print(stdout.read().decode())

    client.close()

if __name__ == "__main__":
    main()
