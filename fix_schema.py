import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    ssh.connect('166.1.227.63', username='root', password='kz@j8PbU77r9GZ')
    print("Connected via SSH")
    
    commands = [
        "sudo -u postgres psql -d Stephans -c 'ALTER TABLE stock_picking ADD COLUMN IF NOT EXISTS custom_destination_warehouse_id int4;'",
        "sudo -u postgres psql -d Stephans -c 'ALTER TABLE stock_picking ADD COLUMN IF NOT EXISTS custom_source_warehouse_id int4;'"
    ]
    
    for cmd in commands:
        print(f"Executing: {cmd}")
        stdin, stdout, stderr = ssh.exec_command(cmd)
        print("STDOUT:", stdout.read().decode())
        print("STDERR:", stderr.read().decode())
        
finally:
    ssh.close()
