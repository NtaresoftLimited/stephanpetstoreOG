#!/usr/bin/env python3
import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"
SEARCH_PATH = "/opt/odoo/custom-addons/custom_pos_reports"

def main():
    print(f"Checking Python syntax on {HOST}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=10)

    # Check syntax of all .py files in the module
    print(f"\n>>> Compiling .py files in {SEARCH_PATH}...")
    cmd = f"find {SEARCH_PATH} -name '*.py' -exec python3 -m py_compile {{}} \\;"
    stdin, stdout, stderr = client.exec_command(cmd)
    
    out = stdout.read().decode('utf-8', errors='replace').strip()
    err = stderr.read().decode('utf-8', errors='replace').strip()
    
    if out: print("STDOUT:", out)
    if err: 
        print("SYNTAX ERRORS FOUND:")
        print(err)
    else:
        print("No Python syntax errors found.")

    client.close()

if __name__ == "__main__":
    main()
