
import paramiko

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def main():
    print(f"Connecting to {HOST}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(HOST, username=USER, password=PASSWORD)
        
        print("Restarting Odoo service...")
        commands = [
            "systemctl restart odoo",
            "systemctl status odoo --no-pager"
        ]
        
        for cmd in commands:
            print(f"Exec: {cmd}")
            stdin, stdout, stderr = client.exec_command(cmd)
            out = stdout.read().decode().strip()
            err = stderr.read().decode().strip()
            if out: print(out)
            if err: print(f"Error/Log: {err}")

        client.close()
        print("Restart Complete.")
    except Exception as e:
        print(f"Failed to restart Odoo: {e}")

if __name__ == "__main__":
    main()
