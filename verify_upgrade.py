
import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"
DB_NAME = "Stephans"

def run_cmd(client, cmd):
    print(f"Executing: {cmd}")
    stdin, stdout, stderr = client.exec_command(cmd)
    return stdout.read().decode('utf-8', errors='replace').strip()

def run_psql(client, query):
    cmd = f'su - postgres -c "psql {DB_NAME} -t -c \\"{query}\\""'
    stdin, stdout, stderr = client.exec_command(cmd)
    return stdout.read().decode('utf-8', errors='replace').strip()

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(HOST, username=USER, password=PASSWORD, timeout=10)
        
        print(">>> Listing Databases (via shell):")
        dbs = run_cmd(client, "su - postgres -c 'psql -l'")
        print(dbs)
        
        print("\n>>> Checking 'grooming' module state:")
        q = "SELECT name, state, latest_version FROM ir_module_module WHERE name='grooming';"
        print(run_psql(client, q))
        
        print("\n>>> Checking ir_model_data for ANY grooming data (Limit 10):")
        q = "SELECT name, model, res_id FROM ir_model_data WHERE module='grooming' ORDER BY id DESC LIMIT 10;"
        res = run_psql(client, q)
        print(res if res else "NO XML IDs FOUND.")

        print("\n>>> Checking product_template by name pattern:")
        q = "SELECT id, name, default_code FROM product_template WHERE name LIKE '%Grooming%';"
        res = run_psql(client, q)
        print(res if res else "NO PRODUCTS FOUND.")

    except Exception as e:
        print(f"Connection Failed: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    main()
