import paramiko

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD)
    
    # Check for all views inheriting OrderReceipt
    sql = """
    SELECT v.id, v.name, v.key, v.active, m.name as module
    FROM ir_ui_view v
    LEFT JOIN ir_model_data d ON d.res_id = v.id AND d.model = 'ir.ui.view'
    LEFT JOIN ir_module_module m ON d.module = m.id
    WHERE v.inherit_id IN (
        SELECT id FROM ir_ui_view WHERE key = 'point_of_sale.OrderReceipt'
    );
    """
    print("Checking for ALL views inheriting OrderReceipt...")
    stdin, stdout, stderr = client.exec_command(f"su - postgres -c \"psql Stephans -c \\\"{sql}\\\"\"")
    print(stdout.read().decode())

    # Check the manifest of custom_pos_reports on server
    print("\nChecking server-side manifest...")
    stdin, stdout, stderr = client.exec_command("cat /opt/odoo/custom-addons/custom_pos_reports/__manifest__.py")
    print(stdout.read().decode())
    
    client.close()

if __name__ == "__main__":
    main()
