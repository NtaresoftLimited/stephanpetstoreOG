#!/usr/bin/env bash
# Cutover: Odoo 18 (odoo-stephans, DB Stephans) -> Odoo 20 (odoo20-staging, DB stephans_odoo20).
#
# PREPARED, NOT YET RUN. Run one phase at a time, as root on the VPS, reading the output before
# moving on:
#     CONFIRM=yes ./cutover_odoo20.sh <phase>
# Phases, in order:
#     preflight  read-only checks; refuses to continue while a blocker remains
#     backup     dumps both databases and saves every file this script edits
#     freeze     stops Odoo 18 so no more sales are rung up there
#     sync       final POS/stock/settings sync Odoo 18 -> 20, then the independent check
#     settings   web.base.url, WhatsApp key, outgoing mail server on Odoo 20
#     server     Odoo 20 multi-process config (workers + gevent port), restart
#     routing    nginx (site + /websocket) and the Sanity sync env -> Odoo 20
#     verify     smoke checks through nginx
#     rollback   puts nginx, the sanity env and the Odoo 20 config back and restarts Odoo 18
# Manual steps the script cannot do (see the end of preflight's output):
#     Cloudflare dashboard: tunnel hostname erp.stephanspetstore.co.tz -> Odoo 20
#     Vercel: ODOO_URL / ODOO_DB of the Next.js storefront
set -euo pipefail

[[ "${CONFIRM:-}" == "yes" ]] || { echo "Set CONFIRM=yes to run a phase."; exit 2; }
PHASE="${1:?phase required}"

SCRIPTS=/var/tmp/stephans_cutover_scripts        # copy of the repo's scripts/ directory
STATE=/opt/odoo/backups/cutover_$(date +%Y%m%d)   # backups and saved files of this cutover
O18_DB=Stephans
O20_DB=stephans_odoo20
O18_SVC=odoo-stephans
O20_SVC=odoo20-staging
O18_BIN="/usr/bin/python3 /opt/odoo/odoo-server/odoo-bin"
O20_BIN="/opt/odoo/venv-odoo20/bin/python3 /opt/odoo/odoo20-community/odoo-bin"
O18_CONF=/etc/odoo/odoo_stephans.conf
O20_CONF=/etc/odoo/odoo20_stephans.conf
NGINX_SITE=/etc/nginx/sites-available/stephans_odoo18_web.conf
SANITY_ENV=/etc/odoo-sanity-sync.env
ERP_URL=https://erp.stephanspetstore.co.tz
O20_HTTP_PORT=8079
O20_GEVENT_PORT=8075          # 8072 belongs to the legacy "odoo" service, 8074 to Odoo 18
O20_WORKERS=2                 # server has 1 CPU / ~1 GB RAM; raise only with more memory
BIND_LOCAL="${BIND_LOCAL:-0}" # 1 = Odoo 20 listens on 127.0.0.1 only; only if the Cloudflare tunnel origin is localhost
WHATSAPP_KEY_FILE=/root/stephans_whatsapp_api_key   # root-only file holding the WaSender key (one line)
POS_CONFIGS="5,7"             # live Odoo 18 tills: Masaki, Mikocheni

ro_psql() { sudo -u postgres env PGOPTIONS='-c default_transaction_read_only=on' psql -At -d "$1" -c "$2"; }
o18_shell() { sudo -u odoo env PGOPTIONS='-c default_transaction_read_only=on' $O18_BIN shell -c "$O18_CONF" -d "$O18_DB" --no-http --log-level=error; }
o20_shell() { sudo -u odoo env PYTHONUNBUFFERED=1 "$@" $O20_BIN shell -c "$O20_CONF" -d "$O20_DB" --no-http --log-level=error; }
die() { echo "ABORT: $*" >&2; exit 1; }

case "$PHASE" in

preflight)
    blockers=0
    pgv=$(sudo -u postgres psql -At -c "show server_version_num")
    if (( pgv < 160000 )); then echo "BLOCKER PostgreSQL is $pgv; Odoo 20 needs 16+"; blockers=$((blockers+1)); fi
    open=$(ro_psql "$O18_DB" "select count(*) from pos_session where state <> 'closed' and config_id in ($POS_CONFIGS)")
    if (( open > 0 )); then echo "BLOCKER $open Odoo 18 till session(s) still open (close them in Odoo 18 first)"; blockers=$((blockers+1)); fi
    stale=$(ro_psql "$O18_DB" "select string_agg(name, ', ') from pos_session where state <> 'closed' and config_id not in ($POS_CONFIGS)")
    [[ -n "$stale" ]] && echo "NOTE  old sessions on retired tills still open (not migrated): $stale"
    groom=$(ro_psql "$O18_DB" "select count(*) from grooming_appointment where state not in ('completed','cancelled')")
    if (( groom > 0 )); then echo "BLOCKER $groom grooming booking(s) still open in Odoo 18 (finish or migrate them)"; blockers=$((blockers+1)); fi
    skew=$(ro_psql "$O18_DB" "select count(*) from pos_order where create_date > now() - interval '1 day' and abs(extract(epoch from date_order - create_date)) > 3600")
    if (( skew > 0 )) && [[ "${SKIP_CLOCK_CHECK:-}" != 1 ]]; then
        echo "BLOCKER $skew order(s) in the last day with a till clock off by >1h (fix the Masaki device clock; SKIP_CLOCK_CHECK=1 once fixed)"; blockers=$((blockers+1)); fi
    o20open=$(ro_psql "$O20_DB" "select count(*) from pos_session where state <> 'closed'")
    if (( o20open > 0 )); then echo "BLOCKER $o20open Odoo 20 session(s) open (test sessions must be closed; the import refuses otherwise)"; blockers=$((blockers+1)); fi
    inactive=$(ro_psql "$O20_DB" "select string_agg(login, ', ') from res_users where login in ('salesmasaki@stephanspetstore.co.tz','salesmikocheni@stephanspetstore.co.tz','info@stephanspetstore.co.tz') and not active")
    if [[ -n "$inactive" ]]; then echo "BLOCKER store logins still archived in Odoo 20: $inactive"; blockers=$((blockers+1)); fi
    suser=$(grep -E '^ODOO_USER=' "$SANITY_ENV" | cut -d= -f2-)
    sactive=$(ro_psql "$O20_DB" "select count(*) from res_users where login = '$suser' and active")
    if (( sactive != 1 )); then echo "BLOCKER Sanity sync user is not an active Odoo 20 login (set its password in Odoo 20)"; blockers=$((blockers+1)); fi
    if [[ ! -s "$WHATSAPP_KEY_FILE" ]] || [[ $(stat -c %a "$WHATSAPP_KEY_FILE") != 600 ]]; then
        echo "BLOCKER $WHATSAPP_KEY_FILE missing or not mode 600 (put the WaSender key there)"; blockers=$((blockers+1)); fi
    [[ -d "$SCRIPTS" ]] || { echo "BLOCKER $SCRIPTS missing (upload the repo's scripts/ directory)"; blockers=$((blockers+1)); }
    ro_psql "$O20_DB" "select 'chart: ' || chart_template from res_company"
    systemctl is-active --quiet "$O20_SVC" || { echo "BLOCKER $O20_SVC not running"; blockers=$((blockers+1)); }
    df -h /opt/odoo/backups | tail -1
    free -m | sed -n 2p
    echo "MANUAL before 'routing': Cloudflare tunnel hostname erp.stephanspetstore.co.tz must be pointed at http://localhost:$O20_HTTP_PORT"
    echo "MANUAL after  'routing': Vercel ODOO_URL=$ERP_URL ODOO_DB=$O20_DB for the storefront, then redeploy"
    (( blockers == 0 )) || die "$blockers blocker(s)"
    echo "PREFLIGHT OK"
    ;;

backup)
    mkdir -p "$STATE"; chmod 700 "$STATE"
    sudo -u postgres pg_dump -Fc -d "$O18_DB" > "$STATE/${O18_DB}.dump"
    sudo -u postgres pg_dump -Fc -d "$O20_DB" > "$STATE/${O20_DB}.dump"
    cp -a "$NGINX_SITE" "$STATE/nginx_site.conf"
    cp -a "$SANITY_ENV" "$STATE/sanity-sync.env"
    cp -a "$O20_CONF" "$STATE/odoo20.conf"
    ls -la "$STATE"
    ;;

freeze)
    systemctl stop "$O18_SVC"
    systemctl is-active --quiet "$O18_SVC" && die "$O18_SVC still running"
    echo "Odoo 18 stopped. Sales must now wait for Odoo 20."
    ;;

sync)
    systemctl is-active --quiet "$O18_SVC" && die "run 'freeze' first"
    cd /tmp
    o18_shell < "$SCRIPTS/export_pos_inventory_odoo18.py" | grep -E 'EXPORT|TOTAL'
    o18_shell < "$SCRIPTS/export_config_odoo18.py" | grep -E 'EXPORT'
    o20_shell MIG_COMMIT=1 < "$SCRIPTS/import_pos_inventory_odoo20.py" | grep -E 'CHECK|STATS|WARN|COMMITTED'
    o20_shell MIG_COMMIT=1 < "$SCRIPTS/sync_config_odoo20.py" | grep -E 'CHANGE|COMMITTED'
    report=$(sudo -u postgres /usr/bin/python3 "$SCRIPTS/verify_pos_migration.py" "$O18_DB" "$O20_DB")
    echo "$report" | sed -n '/^PRODUCTS/,$p'
    # Only the known catalogue note (shared product codes) may remain.
    if echo "$report" | grep -E '^== ' | grep -v 'product code used by several' ; then die "migration check found differences"; fi
    echo "SYNC OK"
    ;;

settings)
    o20_shell MIG_COMMIT=1 WHATSAPP_KEY_FILE="$WHATSAPP_KEY_FILE" ERP_URL="$ERP_URL" O18_DB="$O18_DB" <<'PY'
import os, psycopg2
P = env["ir.config_parameter"].sudo()
P.set_param("web.base.url", os.environ["ERP_URL"])
P.set_param("web.base.url.freeze", "True")
key = open(os.environ["WHATSAPP_KEY_FILE"]).read().strip()
assert key, "empty WhatsApp key file"
P.set_param("stephans_whatsapp.api_key", key)
# Outgoing mail: copy Odoo 18's server (password goes database to database, never printed).
src = psycopg2.connect(dbname=os.environ["O18_DB"]); src.set_session(readonly=True)
cur = src.cursor()
cur.execute("select name, smtp_host, smtp_port, smtp_encryption, smtp_user, smtp_pass, from_filter from ir_mail_server where active order by sequence, id limit 1")
row = cur.fetchone()
assert row, "Odoo 18 has no active mail server"
name, host, port, enc, user, password, from_filter = row
M = env["ir.mail_server"].sudo()
vals = {"name": name, "smtp_host": host, "smtp_port": port, "smtp_encryption": enc,
        "smtp_user": user, "smtp_pass": password, "from_filter": from_filter, "active": True}
if "smtp_authentication" in M._fields:
    vals["smtp_authentication"] = "login"
server = M.search([("smtp_host", "=", host)], limit=1)
server.write(vals) if server else M.create(vals)
env.cr.commit()
print("web.base.url", P.get_param("web.base.url"), "| whatsapp key set", bool(P.get_param("stephans_whatsapp.api_key")),
      "| mail server", host, port, enc)
try:
    (server or M.search([("smtp_host", "=", host)], limit=1)).test_smtp_connection()
except Exception as exc:  # test_smtp_connection reports success as an exception-like notification too
    print("SMTP test:", str(exc).splitlines()[0][:200])
PY
    ;;

server)
    cp -a "$O20_CONF" "$O20_CONF.precutover"
    python3 - "$O20_CONF" "$O20_WORKERS" "$O20_GEVENT_PORT" "$BIND_LOCAL" <<'PY'
import re, sys
path, workers, gevent, bind_local = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
text = open(path).read()
want = {"workers": workers, "gevent_port": gevent, "max_cron_threads": "1",
        "http_interface": "127.0.0.1",               # only nginx / the tunnel reach Odoo
        "limit_memory_soft": str(400 * 1024 * 1024), "limit_memory_hard": str(560 * 1024 * 1024),
        "limit_time_cpu": "600", "limit_time_real": "1200"}
if bind_local == "1":
    want["http_interface"] = "127.0.0.1"   # port 8079 is reachable from the internet today
for key, value in want.items():
    if re.search(r"^%s\s*=" % key, text, re.M):
        text = re.sub(r"^%s\s*=.*$" % key, "%s = %s" % (key, value), text, flags=re.M)
    else:
        text = text.rstrip("\n") + "\n%s = %s\n" % (key, value)
open(path, "w").write(text)
PY
    grep -E '^(workers|gevent_port|max_cron_threads|http_interface|http_port|limit_)' "$O20_CONF"
    systemctl restart "$O20_SVC"; sleep 10
    systemctl is-active --quiet "$O20_SVC" || die "$O20_SVC failed to start (restore $O20_CONF.precutover)"
    curl -fsS -o /dev/null -w "http %{http_code}\n" "http://127.0.0.1:$O20_HTTP_PORT/web/login"
    ss -ltn | grep -E ":($O20_HTTP_PORT|$O20_GEVENT_PORT) " || die "Odoo 20 ports not listening"
    ;;

routing)
    cp -a "$NGINX_SITE" "$NGINX_SITE.precutover"
    python3 - "$NGINX_SITE" "$O20_HTTP_PORT" "$O20_GEVENT_PORT" <<'PY'
import re, sys
path, http, gevent = sys.argv[1], sys.argv[2], sys.argv[3]
text = open(path).read()
assert "upstream odoo18_app" in text, "unexpected nginx site layout"
text = re.sub(r"upstream odoo18_app \{[^}]*\}",
              "upstream odoo20_app {\n    server 127.0.0.1:%s;\n}\nupstream odoo20_chat {\n    server 127.0.0.1:%s;\n}" % (http, gevent), text)
# /websocket goes to the gevent port, everything else to the HTTP port.
text = re.sub(r"(location /websocket \{[^}]*?proxy_pass )http://odoo18_app;", r"\1http://odoo20_chat;", text, flags=re.S)
text = text.replace("proxy_pass http://odoo18_app;", "proxy_pass http://odoo20_app;")
assert "odoo18_app" not in text
open(path, "w").write(text)
PY
    nginx -t || { cp -a "$NGINX_SITE.precutover" "$NGINX_SITE"; die "nginx config invalid, restored"; }
    systemctl reload nginx
    cp -a "$SANITY_ENV" "$SANITY_ENV.precutover"
    sed -i -E "s#^ODOO_URL=.*#ODOO_URL=http://127.0.0.1:$O20_HTTP_PORT#; s#^ODOO_DB=.*#ODOO_DB=$O20_DB#" "$SANITY_ENV"
    grep -E '^ODOO_(URL|DB)=' "$SANITY_ENV"
    systemctl restart odoo-sanity-picture-sync.timer odoo-sanity-price-sync.timer
    systemctl disable "$O18_SVC"
    echo "ROUTING OK - now do the Cloudflare and Vercel steps"
    ;;

verify)
    for host in www.stephanspetstore.co.tz stephanspetstore.co.tz; do
        curl -sS -o /dev/null -w "$host /web/login %{http_code}\n" -H "Host: $host" http://127.0.0.1/web/login
        curl -sS -o /dev/null -w "$host /websocket %{http_code} (101/400 = reached Odoo)\n" -H "Host: $host" \
             -H "Connection: Upgrade" -H "Upgrade: websocket" -H "Sec-WebSocket-Version: 13" \
             -H "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==" http://127.0.0.1/websocket || true
    done
    curl -sS -o /dev/null -w "erp (through Cloudflare) %{http_code}\n" "$ERP_URL/web/login"
    ro_psql "$O20_DB" "select key || '=' || value from ir_config_parameter where key = 'web.base.url'"
    journalctl -u "$O20_SVC" --since "-10 min" --no-pager | grep -E " ERROR | CRITICAL " | tail -5 || true
    ;;

rollback)
    [[ -f "$NGINX_SITE.precutover" ]] && cp -a "$NGINX_SITE.precutover" "$NGINX_SITE" && nginx -t && systemctl reload nginx
    [[ -f "$SANITY_ENV.precutover" ]] && cp -a "$SANITY_ENV.precutover" "$SANITY_ENV" && \
        systemctl restart odoo-sanity-picture-sync.timer odoo-sanity-price-sync.timer
    [[ -f "$O20_CONF.precutover" ]] && cp -a "$O20_CONF.precutover" "$O20_CONF" && systemctl restart "$O20_SVC"
    systemctl enable --now "$O18_SVC"
    echo "Rolled back to Odoo 18. Point the Cloudflare erp hostname back to Odoo 18 (port 8071) and revert Vercel."
    echo "Sales rung up on Odoo 20 in the meantime exist only in $O20_DB."
    ;;

*) die "unknown phase $PHASE" ;;
esac
