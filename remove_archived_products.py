
import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"
DB_NAME = "Stephans"

def run_cmd(client, cmd, timeout=120):
    print(f"Executing: {cmd}")
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    exit_code = stdout.channel.recv_exit_status()
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    return out, err, exit_code

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(HOST, username=USER, password=PASSWORD, timeout=30)
        
        # Stop Odoo service first
        print(">>> Stopping Odoo service...")
        run_cmd(client, "systemctl stop odoo")
        
        odoo_bin = "/opt/odoo/odoo-server/odoo-bin"
        odoo_conf = "/etc/odoo.conf"
        
        # Python code to run in Odoo shell
        python_code = '''
# Find all archived products
archived = env['product.template'].with_context(active_test=False).search([('active', '=', False)])
print(f"Found {len(archived)} archived products")

deleted = 0
failed = []
for prod in archived:
    try:
        name = prod.name
        prod_id = prod.id
        prod.unlink()
        print(f"Deleted: {prod_id}")
        deleted += 1
    except Exception as e:
        failed.append((prod.id, str(e)[:50]))

print(f"\\nDeleted: {deleted}")
print(f"Failed: {len(failed)}")
for f in failed:
    print(f"  {f[0]}: {f[1]}")

env.cr.commit()

# Verify
remaining = env['product.template'].with_context(active_test=False).search([('active', '=', False)])
print(f"\\nRemaining archived: {len(remaining)}")
'''
        
        # Write Python code to a temp file on server
        print(">>> Uploading deletion script to server...")
        sftp = client.open_sftp()
        with sftp.file('/tmp/delete_archived.py', 'w') as f:
            f.write(python_code)
        sftp.close()
        
        # Run via Odoo shell (service is stopped, so port should be free)
        print(">>> Running deletion via Odoo shell...")
        shell_cmd = f"su -s /bin/bash odoo -c 'cat /tmp/delete_archived.py | {odoo_bin} shell -c {odoo_conf} -d {DB_NAME}'"
        
        out, err, code = run_cmd(client, shell_cmd, timeout=180)
        
        print("\nOutput:")
        print(out)
        if "Error" in err or "Traceback" in err:
            print("\nErrors:")
            print(err[-2000:])
        
        # Start Odoo service again
        print("\n>>> Starting Odoo service...")
        run_cmd(client, "systemctl start odoo")
        print("Done.")
        
    except Exception as e:
        print(f"Error: {e}")
        # Try to restart service even if error
        try:
            run_cmd(client, "systemctl start odoo")
        except:
            pass
    finally:
        client.close()

if __name__ == "__main__":
    main()
