#!/usr/bin/env python3
"""
Fix Missing POS Order Error

This script investigates and fixes the "Missing Record: pos.order(1,)" error
by checking if the order exists and providing solutions.
"""
import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"
DB_NAME = "Stephans"

def run_psql(client, query):
    """Execute a PostgreSQL query and return the output."""
    cmd = f'su - postgres -c "psql {DB_NAME} -t -c \\"{query}\\""'
    stdin, stdout, stderr = client.exec_command(cmd)
    return stdout.read().decode('utf-8', errors='replace').strip()

def main():
    print(f"Connecting to {HOST}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=10)

    print("\n" + "="*60)
    print("INVESTIGATING MISSING POS ORDER ISSUE")
    print("="*60)

    # Check min/max order IDs
    print("\n>> Checking order ID range...")
    result = run_psql(client, "SELECT MIN(id), MAX(id), COUNT(*) FROM pos_order;")
    print(f"   Min ID, Max ID, Count: {result}")

    # Check if order ID 1 exists
    print("\n>> Checking if order ID 1 exists...")
    result = run_psql(client, "SELECT id, name, state FROM pos_order WHERE id = 1;")
    if result:
        print(f"   Order 1 exists: {result}")
    else:
        print("   Order ID 1 does NOT exist in the database!")

    # Check for draft orders that might be causing issues
    print("\n>> Checking for draft orders...")
    result = run_psql(client, "SELECT id, name, date_order, amount_total FROM pos_order WHERE state = 'draft' ORDER BY id DESC LIMIT 10;")
    if result:
        print(f"   Draft orders found:\n{result}")
    else:
        print("   No draft orders found.")

    # Check current open POS sessions
    print("\n>> Checking open POS sessions...")
    result = run_psql(client, "SELECT id, name, state, user_id FROM pos_session WHERE state = 'opened' ORDER BY id DESC;")
    if result:
        print(f"   Open sessions:\n{result}")
    else:
        print("   No open sessions.")

    # Check latest session orders
    print("\n>> Latest session with orders...")
    result = run_psql(client, """
        SELECT ps.id as session_id, ps.name as session_name, po.id as order_id, po.name as order_name, po.state
        FROM pos_session ps
        LEFT JOIN pos_order po ON po.session_id = ps.id
        WHERE ps.state = 'opened'
        ORDER BY po.id DESC LIMIT 5;
    """)
    if result:
        print(f"   Session orders:\n{result}")
    
    # THE FIX: Clear browser local storage reference by updating the POS config
    print("\n" + "="*60)
    print("RECOMMENDED FIX")
    print("="*60)
    print("""
The error "pos.order(1,)" refers to an order cached in the browser's 
local storage that no longer exists in the database.

Solutions:
1. QUICK FIX - Clear Browser Data:
   - In the browser, press F12 to open Developer Tools
   - Go to Application > Local Storage
   - Clear all entries for erp.stephanspetstore.co.tz
   - Refresh the POS

2. VIA ODOO - Delete local draft orders:
   - Close the current POS session
   - Re-open the POS (this resets the local cache)
   
3. DATABASE FIX - Create a placeholder order (NOT RECOMMENDED):
   - This would create order ID 1 just to satisfy the reference
   
Let me check if we can reset the POS session state...
""")

    # Check for problematic references in the current session
    print("\n>> Checking for orders with invalid references...")
    result = run_psql(client, """
        SELECT po.id, po.name, po.session_id, ps.name as session_name, ps.state as session_state
        FROM pos_order po
        LEFT JOIN pos_session ps ON po.session_id = ps.id
        WHERE po.state = 'draft'
        ORDER BY po.id DESC LIMIT 10;
    """)
    if result:
        print(f"   Draft orders in sessions:\n{result}")

    # Auto-fix: Delete orphaned draft orders that may cause issues
    print("\n" + "="*60)
    print("ATTEMPTING AUTO-FIX")
    print("="*60)
    
    # Check if there are any orders with id=1 that are soft-deleted or similar
    result = run_psql(client, "SELECT id, name, state FROM pos_order WHERE id < 10 ORDER BY id;")
    print(f"\n>> Orders with ID < 10: {result if result else 'None'}")

    # The real fix - restart Odoo to clear any stale cache
    print("\n>> Restarting Odoo service to clear server-side caches...")
    stdin, stdout, stderr = client.exec_command("systemctl restart odoo18")
    import time
    time.sleep(5)
    
    # Check Odoo status
    stdin, stdout, stderr = client.exec_command("systemctl status odoo18 | head -20")
    status = stdout.read().decode('utf-8', errors='replace')
    print(f"\n   Odoo service status:\n{status}")

    print("\n" + "="*60)
    print("NEXT STEPS FOR USER")
    print("="*60)
    print("""
1. Clear your browser's local storage for the POS site:
   - Press F12 > Application > Local Storage > Clear
   
2. Hard refresh the POS page: Ctrl+Shift+R

3. If the issue persists, close and reopen the POS session.

The Odoo service has been restarted to clear server caches.
""")

    client.close()
    print("\nDone!")

if __name__ == "__main__":
    main()
