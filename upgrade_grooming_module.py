
import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"
DB_NAME = "Stephans"
MODULE = "grooming"

def run_cmd(client, cmd, timeout=120):
    print(f"Executing: {cmd}")
    try:
        stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
        exit_status = stdout.channel.recv_exit_status()
        out = stdout.read().decode('utf-8', errors='replace')
        err = stderr.read().decode('utf-8', errors='replace')
        return out, err, exit_status
    except Exception as e:
        return "", str(e), -1

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(HOST, username=USER, password=PASSWORD, timeout=30)
        
        # 1. Stop service
        print("Stopping odoo service...")
        run_cmd(client, "systemctl stop odoo")
        
        # 2. Check file
        out, err, code = run_cmd(client, "ls -l /opt/odoo/custom-addons/grooming/data/grooming_data.xml")
        print(f"File check: {out.strip()} (Code: {code})")
        if code != 0:
            print(f"Error checking file: {err}")
            print("File missing! Aborting upgrade.") 
            return

        # 3. Check ownership and fix permissions
        out, _, _ = run_cmd(client, "stat -c '%U:%G' /opt/odoo/custom-addons/grooming/data/grooming_data.xml")
        print(f"File owner: {out.strip()}")
        print("Fixing ownership...")
        run_cmd(client, "chown -R odoo:odoo /opt/odoo/custom-addons/grooming")
        
        # 4. Diagnose via Shell
        odoo_bin = "/opt/odoo/odoo-server/odoo-bin"
        odoo_conf = "/etc/odoo.conf"
        
        print(">>> Diagnosing via odoo-bin shell:")
        diagnosis_code = "m = env['ir.module.module'].search([('name','=','grooming')]); print(f'Module Found: {m.name}, State: {m.state}, Version: {m.latest_version}')"
        shell_cmd = f"echo \"{diagnosis_code}\" | su -s /bin/bash odoo -c '{odoo_bin} shell -c {odoo_conf} -d {DB_NAME}'"
        
        print(f"Running Shell Command: {shell_cmd}")
        out, err, code = run_cmd(client, shell_cmd, timeout=60)
        print(f"Shell Output:\n{out}")
        print(f"Shell Error:\n{err}")

        # Re-run upgrade regardless
        upgrade_cmd = f"su -s /bin/bash odoo -c '{odoo_bin} -c {odoo_conf} -d {DB_NAME} -u {MODULE} --stop-after-init'"
        print(f"Running Upgrade Command: {upgrade_cmd}")
        run_cmd(client, upgrade_cmd)

        # 5. Start service

        # 5. Start Service
        print("Starting odoo service...")
        run_cmd(client, "systemctl start odoo")
        print("Done.")

    except Exception as e:
        print(f"Connection Failed: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    main()
