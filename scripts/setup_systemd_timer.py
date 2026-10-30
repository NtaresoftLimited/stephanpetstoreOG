import paramiko

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "wpo,,CWc2VH^PZ"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASSWORD)

service_unit = """[Unit]
Description=Automated Odoo to Sanity Price and Product Sync
After=network.target odoo-stephans.service

[Service]
Type=oneshot
User=root
ExecStart=/opt/scripts/sync_odoo_sanity_prices.py
StandardOutput=journal
StandardError=journal
TimeoutSec=120
"""

timer_unit = """[Unit]
Description=Run Odoo to Sanity Price Sync Every 10 Minutes

[Timer]
OnBootSec=1min
OnUnitActiveSec=10min
Persistent=true

[Install]
WantedBy=timers.target
"""

logrotate_config = """/var/log/odoo-sanity-sync.log {
    weekly
    rotate 4
    compress
    missingok
    notifempty
}
"""

sftp = ssh.open_sftp()
with sftp.file("/etc/systemd/system/odoo-sanity-price-sync.service", "w") as f:
    f.write(service_unit)

with sftp.file("/etc/systemd/system/odoo-sanity-price-sync.timer", "w") as f:
    f.write(timer_unit)

with sftp.file("/etc/logrotate.d/odoo-sanity-sync", "w") as f:
    f.write(logrotate_config)

sftp.close()

# Reload systemd daemon, enable & start timer
commands = [
    "systemctl daemon-reload",
    "systemctl enable --now odoo-sanity-price-sync.timer",
    "systemctl start odoo-sanity-price-sync.service",
    "systemctl is-active odoo-sanity-price-sync.timer",
    "systemctl list-timers --all | grep odoo-sanity-price-sync"
]

print("=== ENABLING SYSTEMD TIMER ===")
for cmd in commands:
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    print(f"[{cmd}] => {out if out else err}")

ssh.close()
