import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('166.1.227.63', username='root', password='kz@j8PbU77r9GZ')
script = """
import xmlrpc.client
models = xmlrpc.client.ServerProxy('http://localhost:8071/xmlrpc/2/object')
fields = models.execute_kw('Stephans', 1, 'kz@j8PbU77r9GZ', 'stock.warehouse.orderpoint', 'fields_get', [], {'attributes': ['type', 'string']})
print("qty_to_order exists:", 'qty_to_order' in fields)
"""

stdin, stdout, stderr = ssh.exec_command(f'python3 -c "{script}"')
print("Output:", stdout.read().decode())
print("Error:", stderr.read().decode())
ssh.close()
