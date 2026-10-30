import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('166.1.227.63', username='root', password='wpo,,CWc2VH^PZ')
cmd = "cat /opt/odoo/custom-addons/custom_pos_reports/wizard/pos_details.py"
stdin, stdout, stderr = ssh.exec_command(cmd)
code = stdout.read().decode()
if "User-Agent" in code:
    print("User-Agent is PRESENT")
else:
    print("User-Agent is MISSING")

if "raise_for_status" in code:
    print("raise_for_status is PRESENT")
else:
    print("raise_for_status is MISSING")
