
import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def main():
    print(f"Fixing Configuration on {HOST}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=10)

    # 1. Update odoo.conf for proxy_mode
    print("\n>>> Checking proxy_mode in odoo.conf...")
    stdin, stdout, stderr = client.exec_command("grep 'proxy_mode' /etc/odoo.conf")
    result = stdout.read().decode().strip()
    
    if "proxy_mode = True" in result:
        print("proxy_mode is already enabled.")
    else:
        print("Enabling proxy_mode...")
        # Backup
        client.exec_command("cp /etc/odoo.conf /etc/odoo.conf.bak")
        # Append or replace
        # If proxy_mode is explicitly False, replace it. If missing, append to [options]
        if "proxy_mode" in result:
            # Replace
             client.exec_command("sed -i 's/proxy_mode = False/proxy_mode = True/g' /etc/odoo.conf")
        else:
            # Append to end (simplified) or better, ensure it is in [options]
            # Just appending should work if file ends with newline, but safer to sed after [options]
            # Actually, standard sed append is easy.
            client.exec_command("sed -i '/^\[options\]/a proxy_mode = True' /etc/odoo.conf")
        
        print("Updated odoo.conf.")

    # 2. Fix web.base.url in Database
    print("\n>>> Fixing web.base.url...")
    sql_base = "UPDATE ir_config_parameter SET value = 'https://erp.stephanspetstore.co.tz' WHERE key = 'web.base.url';"
    sql_freeze = "INSERT INTO ir_config_parameter (key, value) VALUES ('web.base.url.freeze', 'True') ON CONFLICT (key) DO UPDATE SET value = 'True';"
    
    cmd = f"su - postgres -c \"psql Stephans -c \\\"{sql_base}\\\"\""
    client.exec_command(cmd)
    
    cmd = f"su - postgres -c \"psql Stephans -c \\\"{sql_freeze}\\\"\""
    client.exec_command(cmd)
    
    print("Database parameters updated.")

    # 3. Restart Odoo
    print("\n>>> Restarting Odoo Service...")
    client.exec_command("systemctl restart odoo")
    
    print("Done.")
    client.close()

if __name__ == "__main__":
    main()
