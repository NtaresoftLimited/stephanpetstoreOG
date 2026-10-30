
import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def run_cmd(client, cmd):
    print(f"Executing: {cmd}")
    stdin, stdout, stderr = client.exec_command(cmd)
    exit_status = stdout.channel.recv_exit_status()
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    print(f"STDOUT:\n{out}")
    if err:
        print(f"STDERR:\n{err}")
    return out

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(HOST, username=USER, password=PASSWORD, timeout=10)
        
        print(">>> Checking Systemd Services:")
        run_cmd(client, "systemctl list-units --type=service --all | grep odoo")
        
        print("\n>>> Checking Running Processes:")
        run_cmd(client, "ps aux | grep odoo")
        
        print("\n>>> Checking specific service names:")
        for svc in ["odoo", "odoo-server", "odoo18", "Stephans-odoo"]:
             run_cmd(client, f"systemctl status {svc} | head -3")

    except Exception as e:
        print(f"Connection Failed: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    main()
