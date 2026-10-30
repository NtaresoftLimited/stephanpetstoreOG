import paramiko

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD)
    
    # 1. Check POS Config Footers
    sql1 = "SELECT name, receipt_footer FROM pos_config;"
    print("POS Config Footers:")
    stdin, stdout, stderr = client.exec_command(f"su - postgres -c \"psql Stephans -c \\\"{sql1}\\\"\"")
    print(stdout.read().decode())

    # 2. Check for any non-standard modules installed
    sql2 = "SELECT name, state FROM ir_module_module WHERE state = 'installed' AND author NOT LIKE 'Odoo%%' AND author NOT LIKE '%%Antigravity%%' AND author NOT LIKE '%%Odoo S.A.%%';"
    print("\nNon-Standard Installed Modules:")
    stdin, stdout, stderr = client.exec_command(f"su - postgres -c \"psql Stephans -c \\\"{sql2}\\\"\"")
    print(stdout.read().decode())
    
    # 3. Check for any views with 'OrderReceipt' in their name but NOT in our module
    sql3 = "SELECT id, name, key FROM ir_ui_view WHERE (name ILIKE '%%OrderReceipt%%' OR arch_db ILIKE '%%OrderReceipt%%') AND key NOT LIKE '%%custom_pos_reports%%' AND key NOT LIKE 'point_of_sale.OrderReceipt';"
    print("\nOther Potential OrderReceipt Overrides:")
    stdin, stdout, stderr = client.exec_command(f"su - postgres -c \"psql Stephans -c \\\"{sql3}\\\"\"")
    print(stdout.read().decode())

    client.close()

if __name__ == "__main__":
    main()
