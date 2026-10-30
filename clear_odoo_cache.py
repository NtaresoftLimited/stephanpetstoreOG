
import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def main():
    print(f"Connecting to {HOST}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=10)

    print("\n" + "="*60)
    print("CLEARING ODOO CACHE AND RESTARTING")
    print("="*60)

    # Clear Odoo assets cache
    print("\n>> Clearing ir.attachment assets...")
    sql = "DELETE FROM ir_attachment WHERE name LIKE '%assets%' OR res_model = 'ir.ui.view';"
    cmd = f'su - odoo -c "psql -d Stephans -c \\"{sql}\\""'
    stdin, stdout, stderr = client.exec_command(cmd)
    print(stdout.read().decode())

    # Invalidate session caches
    print("\n>> Clearing web sessions...")
    sql = "DELETE FROM ir_sessions;"
    cmd = f'su - odoo -c "psql -d Stephans -c \\"{sql}\\""'
    stdin, stdout, stderr = client.exec_command(cmd)
    print(stdout.read().decode())

    # Restart Odoo
    print("\n>> Restarting Odoo...")
    stdin, stdout, stderr = client.exec_command("systemctl restart odoo")
    print("Odoo restarted.")

    import time
    time.sleep(3)

    # Check it's running
    stdin, stdout, stderr = client.exec_command("systemctl is-active odoo")
    status = stdout.read().decode().strip()
    print(f"Odoo status: {status}")

    client.close()
    print("\nDone! You MUST log out and log back in.")

if __name__ == "__main__":
    main()
