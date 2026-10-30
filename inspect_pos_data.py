#!/usr/bin/env python3
import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"
DB_NAME = "Stephans"

def run_psql(client, query):
    cmd = f'su - postgres -c "psql {DB_NAME} -t -c \\"{query}\\""'
    stdin, stdout, stderr = client.exec_command(cmd)
    return stdout.read().decode('utf-8', errors='replace').strip()

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=10)
    
    print(">>> 1. Check positive statement lines (Cash In?):")
    # Check for positive amounts linked to a session
    q = "SELECT id, amount, payment_ref, pos_session_id FROM account_bank_statement_line WHERE amount > 0 AND pos_session_id IS NOT NULL ORDER BY id DESC LIMIT 10;"
    print(run_psql(client, q))

    print("\n>>> 2. Check if POS Orders have discounts:")
    q = "SELECT name, price_unit, discount FROM pos_order_line WHERE discount > 0 LIMIT 5;"
    print(run_psql(client, q))
    
    print("\n>>> 3. Check POS Order Session Control info:")
    q = "SELECT id, name, amount_total FROM pos_order ORDER BY id DESC LIMIT 3;"
    print(run_psql(client, q))
    
    client.close()

if __name__ == "__main__":
    main()
