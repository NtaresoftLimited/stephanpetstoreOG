import paramiko
import sys

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def run_remote_cmd(cmd):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(HOST, username=USER, password=PASSWORD, timeout=15)
        stdin, stdout, stderr = client.exec_command(cmd)
        out = stdout.read().decode()
        err = stderr.read().decode()
        print(f"COMMAND: {cmd}")
        if out: print(f"STDOUT:\n{out}")
        if err: print(f"STDERR:\n{err}")
        client.close()
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    # Check hostname, odoo service status, and odoo config
    # run_remote_cmd("mkdir -p /opt/odoo/custom-addons; chown -R odoo:odoo /opt/odoo/custom-addons; sed -i 's|addons_path = .*|addons_path = /opt/odoo/odoo-server/odoo/addons,/opt/odoo/custom-addons|' /etc/odoo.conf; systemctl restart odoo")
    run_remote_cmd("ls -l /tmp/Stephans_2026-01-23_20-49-23.zip; ls -l /tmp/addons.zip; ls -l /opt/odoo/custom-addons")
