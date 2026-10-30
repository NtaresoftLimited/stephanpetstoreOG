#!/usr/bin/env python3
import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def main():
    print(f"Checking Point of Sale data on {HOST}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=10)

    queries = [
        # POS Sessions
        ("POS Sessions Count", "SELECT count(*) FROM pos_session;"),
        
        # POS Orders
        ("POS Orders Count", "SELECT count(*) FROM pos_order;"),
        
        # POS Order Lines
        ("POS Order Lines Count", "SELECT count(*) FROM pos_order_line;"),
        
        # POS Configs
        ("POS Configs", "SELECT id, name, active FROM pos_config;"),
        
        # Recent POS Orders (last 5)
        ("Recent POS Orders", "SELECT id, name, date_order, amount_total, state FROM pos_order ORDER BY id DESC LIMIT 5;"),
        
        # POS Payments
        ("POS Payments Count", "SELECT count(*) FROM pos_payment;"),
        
        # POS Payment Methods
        ("POS Payment Methods", "SELECT id, name FROM pos_payment_method LIMIT 10;"),
        
        # Products in POS
        ("Products Available", "SELECT count(*) FROM product_product WHERE active=true;"),
    ]

    for name, query in queries:
        print(f"\n{'='*60}")
        print(f">>> {name}")
        print(f"{'='*60}")
        cmd = f"su - postgres -c \"psql Stephans -c \\\"{query}\\\"\""
        stdin, stdout, stderr = client.exec_command(cmd)
        out = stdout.read().decode('utf-8', errors='replace').strip()
        err = stderr.read().decode('utf-8', errors='replace').strip()
        if out:
            print(out)
        if err and "NOTICE" not in err:
            print(f"STDERR: {err}")

    client.close()

if __name__ == "__main__":
    main()
