#!/usr/bin/env bash
set -euo pipefail

BENCH_DIR_ORIG="/home/erpadm/frappe-bench"
BENCH_DIR="/home/erpadm/frappe-bench-D2IRBL"
SITE_URL="dev02.iridium.blue"
ERP_USER="erpadm"
MYPWD="erpnext_build"
ERP_USER_PWD="sasa"

echo "=== A: /opt/ce_sri/ + envars.sh ==="
sudo mkdir -p /opt/ce_sri
sudo chmod 755 /opt/ce_sri
sudo tee /opt/ce_sri/envars.sh > /dev/null << 'ENVEOF'
#!/usr/bin/env bash
export ERP_USER_PWD="sasa"
export MYPWD="erpnext_build"
export ERPNEXT_SITE="dev02"
export ERPNEXT_DNS="dev02"
export ERPNEXT_TLD="blue"
export ERPNEXT_DOMAIN="dev02.iridium.blue"
export ERPNEXT_SITE_URL="dev02.iridium.blue"
export ERP_USER_NAME="erpadm"
export ERPNEXT_SITE_NICKNAME="D2IRBL"
export TARGET_BENCH_NAME="frappe-bench-D2IRBL"
export TARGET_BENCH="$HOME/frappe-bench-D2IRBL"
export RESTORE_SITE_CONFIG="no"
export KEEP_SITE_PASSWORD="yes"
ENVEOF
sudo chmod 644 /opt/ce_sri/envars.sh
echo "  [OK] /opt/ce_sri/envars.sh"

echo "=== A2: rename bench dir ==="
if sudo test -d "$BENCH_DIR_ORIG" && ! sudo test -L "$BENCH_DIR"; then
    sudo -u "$ERP_USER" ln -sf "$BENCH_DIR_ORIG" "$BENCH_DIR"
    echo "  [OK] symlinked frappe-bench -> frappe-bench-D2IRBL (venv paths preserved)"
elif sudo test -L "$BENCH_DIR"; then
    echo "  [OK] frappe-bench-D2IRBL symlink already exists — skipping"
else
    echo "  [ERROR] Neither $BENCH_DIR_ORIG nor $BENCH_DIR found"
    exit 1
fi

echo "=== A2b: patch Procfile for ce_sri_svc + production worker queues ==="
PROCFILE="$BENCH_DIR/Procfile"
if ! grep -q 'ce_sri_svc' "$PROCFILE" 2>/dev/null; then
  cat > "$PROCFILE" << 'PROCEOF'
redis_cache: redis-server config/redis_cache.conf
redis_queue: redis-server config/redis_queue.conf

web: bench serve --port 8000

socketio: /usr/bin/node apps/frappe/socketio.js
ce_sri_svc: apps/ce_sri/services/ce_sri_svc/go.sh

watch: bench watch

schedule: bench schedule
worker_short: bench worker --queue short 1>> logs/worker.log 2>> logs/worker.error.log
worker_long: bench worker --queue long 1>> logs/worker.log 2>> logs/worker.error.log
worker_default: bench worker --queue default 1>> logs/worker.log 2>> logs/worker.error.log
PROCEOF
  chown $ERP_USER:$ERP_USER "$PROCFILE"
  echo "  [OK] Procfile patched with ce_sri_svc + split worker queues"
else
  echo "  [OK] Procfile already contains ce_sri_svc — skipping"
fi

echo "=== A3: start bench services (supervisor) ==="
# Packer template never ran 'bench setup supervisor' — do it now before any bench commands
sudo -u "$ERP_USER" bash -c "cd $BENCH_DIR && bench setup supervisor --yes"
sudo cp "$BENCH_DIR/config/supervisor.conf" /etc/supervisor/conf.d/frappe-bench.conf
echo "=== A3b: supervisor conf for ce_sri_svc (separate — survives bench setup supervisor) ==="
cat > /etc/supervisor/conf.d/ce-sri-svc.conf << CESRIEOF
[program:frappe-bench-ce-sri-svc]
command=$BENCH_DIR/apps/ce_sri/services/ce_sri_svc/go.sh
environment=PATH="$BENCH_DIR/apps/ce_sri/services/ce_sri_svc/node_modules/.bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
priority=4
autostart=true
autorestart=true
user=$ERP_USER
directory=$BENCH_DIR/apps/ce_sri/services/ce_sri_svc
startretries=10
startsecs=5
stopwaitsecs=10
stdout_logfile=$BENCH_DIR/logs/ce_sri_svc.log
stderr_logfile=$BENCH_DIR/logs/ce_sri_svc.error.log
CESRIEOF
echo "  [OK] /etc/supervisor/conf.d/ce-sri-svc.conf created"

sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start all || true
echo "  Waiting 20s for Redis to be ready..."
sleep 20
echo "  [OK] bench services started"
# nginx (www-data) must be able to traverse /home/$ERP_USER to serve static assets
sudo chmod o+x /home/"$ERP_USER"
echo "  [OK] /home/$ERP_USER world-traversable for nginx"

echo "=== B: fix ownership of rsynced dirs ==="
sudo chown -R "$ERP_USER:$ERP_USER" $BENCH_DIR/apps/ce_sri $BENCH_DIR/apps/returnable $BENCH_DIR/apps/route_planner $BENCH_DIR/BaRe $BENCH_DIR/BKP
echo "  [OK] ownership -> $ERP_USER"

echo "=== B2: enforce AMBIENTE=1 (Pruebas) for ce_sri ==="
_CESRI_SVC="$BENCH_DIR/apps/ce_sri/services/ce_sri_svc"
if [ -f "$_CESRI_SVC/setTESTMODE.sh" ]; then
  sudo -u "$ERP_USER" bash -c "cd $_CESRI_SVC && bash setTESTMODE.sh"
  sudo -u "$ERP_USER" sed -i "s|^export ERP_HOST=.*|export ERP_HOST=$SITE_URL|" "$_CESRI_SVC/.env"
  echo "  [OK] setTESTMODE.sh applied, ERP_HOST=$SITE_URL"
else
  echo "  [SKIP] setTESTMODE.sh not found"
fi

echo "=== B2b: npm install for ce_sri_svc ==="
if [ -f "$_CESRI_SVC/package.json" ]; then
  sudo -u "$ERP_USER" bash -c "cd $_CESRI_SVC && npm install 2>&1"
  echo "  [OK] npm install completed for ce_sri_svc"
else
  echo "  [SKIP] no package.json in ce_sri_svc"
fi

echo "=== C: BaRe/envars.sh symlink ==="
sudo -u "$ERP_USER" ln -sf /opt/ce_sri/envars.sh "$BENCH_DIR/BaRe/envars.sh"
echo "  [OK] BaRe/envars.sh -> /opt/ce_sri/envars.sh"

echo "=== D: bench new-site + install-app erpnext ==="
echo "  site: $SITE_URL  bench: $BENCH_DIR"
if sudo -u "$ERP_USER" bash -c "cd $BENCH_DIR && bench --site $SITE_URL doctor" 2>/dev/null; then
  echo "  [SKIP] site $SITE_URL already exists"
else
  sudo -u "$ERP_USER" bash -c "
    cd $BENCH_DIR
    bench new-site $SITE_URL \
      --mariadb-root-password $MYPWD \
      --admin-password $ERP_USER_PWD
    bench --site $SITE_URL install-app erpnext
  "
  echo "  [OK] site created, erpnext installed"
fi

echo "=== E: place ddlViews.sql ==="
sudo -u "$ERP_USER" mkdir -p "$BENCH_DIR/sites/$SITE_URL/private/files"
  sudo -u erpadm cp /tmp/ddlViews.sql /home/erpadm/frappe-bench-D2IRBL/sites/dev02.iridium.blue/private/files/ddlViews.sql
  rm -f /tmp/ddlViews.sql
  echo '  [OK] ddlViews.sql placed'

echo "=== F: installApps.sh ==="
sudo -u "$ERP_USER" bash -c "cd $BENCH_DIR && bash BaRe/installApps.sh"
echo "  [OK] installApps.sh complete"

echo "=== G-pre: strip DEFINER clauses from backup SQL ==="
_BKP_ARCHIVE=$(tr -d '\r\n' < "$BENCH_DIR/BKP/BACKUP.txt")
_BKP_PATH="$BENCH_DIR/BKP/$_BKP_ARCHIVE"
_SQL_ENTRY="${_BKP_ARCHIVE%.tgz}-database.sql.gz"
_WORK="/tmp/_definer_strip"
rm -rf "$_WORK" && mkdir -p "$_WORK"
tar -xzf "$_BKP_PATH" -C "$_WORK"
gunzip -c "$_WORK/$_SQL_ENTRY" \
  | sed 's/DEFINER=[^ ]*/DEFINER=CURRENT_USER/g' \
  | gzip > "$_WORK/${_SQL_ENTRY}.clean"
mv "$_WORK/${_SQL_ENTRY}.clean" "$_WORK/$_SQL_ENTRY"
(cd "$_WORK" && tar -czf "$_BKP_PATH" -- *)
rm -rf "$_WORK"
echo "  [OK] DEFINER stripped from $_SQL_ENTRY"

echo "=== G: handleRestore.sh ==="
sudo -u "$ERP_USER" bash -c "cd $BENCH_DIR && bash BaRe/handleRestore.sh"
echo "  [OK] database restored"

echo "=== H: supervisor reload (post-restore) ==="
sudo supervisorctl reread
sudo supervisorctl update
echo "  [OK] supervisor updated"

echo "=== H2: bench restart ==="
sudo -u "$ERP_USER" bash -c "cd $BENCH_DIR && bench restart || true"
sudo supervisorctl restart frappe-bench-ce-sri-svc || true
echo "  [OK] bench + ce_sri_svc restarted"

echo "=== H3: reset admin password (bench restore overwrites it) ==="
sudo -u "$ERP_USER" bash -c "cd $BENCH_DIR && bench --site $SITE_URL set-admin-password $ERP_USER_PWD"
echo "  [OK] admin password reset to ERP_USER_PWD"

echo "=== I: install TLS cert ==="
sudo mkdir -p /etc/nginx/certs/iridium.blue
if [ -f /tmp/fullchain.pem ]; then
  sudo cp /tmp/fullchain.pem /etc/nginx/certs/iridium.blue/fullchain.pem
  sudo cp /tmp/privkey.pem   /etc/nginx/certs/iridium.blue/privkey.pem
  sudo chmod 600 /etc/nginx/certs/iridium.blue/privkey.pem
  sudo rm -f /tmp/fullchain.pem /tmp/privkey.pem /tmp/cert.pem
  echo "  [OK] certs installed to /etc/nginx/certs/iridium.blue"
elif [ -f /etc/nginx/certs/iridium.blue/fullchain.pem ]; then
  echo "  [OK] certs already in place at /etc/nginx/certs/iridium.blue — skipping"
else
  echo "  [ERROR] no cert at /tmp/fullchain.pem and none at /etc/nginx/certs/iridium.blue"
  exit 1
fi

echo "=== J: generate nginx config ==="
sudo tee /etc/nginx/sites-available/dev02.iridium.blue > /dev/null << 'NGINXEOF'
upstream frappe-frappe-bench-D2IRBL-dev02.iridium.blue {
    server 127.0.0.1:8000;
}
upstream frappe-socketio-frappe-bench-D2IRBL {
    server 127.0.0.1:9000;
}

server {
    listen 80;
    server_name dev02.iridium.blue;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name dev02.iridium.blue;

    ssl_certificate      /etc/nginx/certs/iridium.blue/fullchain.pem;
    ssl_certificate_key  /etc/nginx/certs/iridium.blue/privkey.pem;
    ssl_dhparam          /etc/nginx/dhparam.pem;
    ssl_protocols        TLSv1.2 TLSv1.3;
    ssl_ciphers          ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache    shared:SSL:10m;
    ssl_session_timeout  1d;
    ssl_session_tickets  off;

    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
    add_header X-Frame-Options SAMEORIGIN always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml application/json application/javascript application/xml+rss application/atom+xml image/svg+xml;

    root /home/erpadm/frappe-bench-D2IRBL/sites;

    location /assets {
        try_files $uri =404;
    }

    location ~ ^/files/.*$ {
        try_files /dev02.iridium.blue/public$uri @webserver;
    }

    location /socket.io {
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_pass http://frappe-socketio-frappe-bench-D2IRBL;
    }

    location @webserver {
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Frappe-Site-Name dev02.iridium.blue;
        proxy_set_header X-Use-X-Accel-Redirect True;
        proxy_read_timeout 120;
        proxy_pass http://frappe-frappe-bench-D2IRBL-dev02.iridium.blue;
    }

    location / {
        rewrite ^(.+)/$ $1 permanent;
        try_files /dev02.iridium.blue/public$uri @webserver;
    }
}
NGINXEOF
echo "  [OK] /etc/nginx/sites-available/dev02.iridium.blue"

echo "=== K: DH params + enable site ==="
if [ ! -f /etc/nginx/dhparam.pem ]; then
    echo "  Generating DH params (2048-bit) — once per VM, reused on redeploy ..."
    sudo openssl dhparam -out /etc/nginx/dhparam.pem 2048 2>/dev/null
    echo "  [OK] DH params written to /etc/nginx/dhparam.pem"
fi
sudo ln -sf /etc/nginx/sites-available/dev02.iridium.blue /etc/nginx/sites-enabled/dev02.iridium.blue
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx
echo "  [OK] nginx reloaded with SSL site"

echo "=== L0: deploy stop.py to bench dir ==="
cat > $BENCH_DIR/stop.py << 'STOPPYEOF'
#!/usr/bin/env python3

"""stop.py — gracefully shut down bench Redis instances and free bound ports.

Reads the port suffix from ./config/redis_cache.conf, then for each known
bench port prefix (1100, 1200, 1300, 900, 800, 500) sends a Redis SHUTDOWN
via redis-cli.  Falls back to fuser -k for any port that remains in use.

Must be run from the bench directory (e.g. ~/frappe-bench).
"""

import os
import socket
import errno
import time

PORTS = [1100, 1200, 1300, 900, 800, 500]


def get_port_suffix():
    """Extract the last digit of the 'port' line from redis_cache.conf."""
    try:
        with open("./config/redis_cache.conf") as f:
            for line in f:
                key, _, value = line.partition(" ")
                if key.strip() == "port":
                    return value.strip()[-1:]
    except IOError:
        print("redis_cache.conf not found — are you in the bench directory?")
        raise SystemExit(1)
    print("No 'port' line found in redis_cache.conf")
    raise SystemExit(1)


def stop_port(port):
    """Attempt to free a single port: Redis SHUTDOWN first, then fuser -k."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(("127.0.0.1", port))
        print(f"Port {port} already closed")
    except socket.error as e:
        if e.errno == errno.EADDRINUSE:
            os.system(f"echo 'shutdown' | redis-cli -h 127.0.0.1 -p {port}")
            time.sleep(3)
            try:
                sock2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock2.bind(("127.0.0.1", port))
                sock2.close()
            except socket.error:
                os.system(f"fuser {port}/tcp -k")
    finally:
        sock.close()


def main():
    suffix = get_port_suffix()
    for prefix in PORTS:
        stop_port(int(f"{prefix}{suffix}"))
    print("bench stopped")


if __name__ == "__main__":
    main()
STOPPYEOF
chown $ERP_USER:$ERP_USER $BENCH_DIR/stop.py
chmod 755 $BENCH_DIR/stop.py
echo "  [OK] stop.py deployed to $BENCH_DIR"

echo "=== L: install bash aliases ==="
DB_NAME=$(python3 -c "import json; print(json.load(open('$BENCH_DIR/sites/$SITE_URL/site_config.json'))['db_name'])" 2>/dev/null || echo "unknown_db")
cat > /home/$ERP_USER/.bash_aliases << ALIASEOF
# Generated by differentiate.sh — do not edit on the VM.
# Source: platforms/kvm/bash_aliases.tmpl
# Variables expanded at script run time: BENCH_DIR, SITE_URL, ERP_USER, DB_NAME
alias TL="tail -fn 1000"
alias python=python3
alias dbch="cd $BENCH_DIR"
alias dbchd="cd $BENCH_DIR/BKP"
alias tailog="mkdir -p /dev/shm/erpnext; touch /dev/shm/erpnext/result.log; tail -f /dev/shm/erpnext/result.log"
alias erplog="mkdir -p /dev/shm/erpnext; cd /dev/shm/erpnext"
alias bnst="cd $BENCH_DIR && bench start"
alias bnrst="cd $BENCH_DIR && sudo -A supervisorctl stop all; python3 ./stop.py; suda chown -R $ERP_USER:$ERP_USER ./logs; bench start"
alias dsit="cd $BENCH_DIR/sites/$SITE_URL"
alias bare="cd $BENCH_DIR/BaRe"
alias ce="cd $BENCH_DIR/apps/ce_sri"
alias cesvc="cd $BENCH_DIR/apps/ce_sri/services/ce_sri_svc"
alias ced="cd $BENCH_DIR/apps/ce_sri/development"
alias cedi="cd $BENCH_DIR/apps/ce_sri/development/initialization"
alias ropl="cd $BENCH_DIR/apps/route_planner"
alias ropld="cd $BENCH_DIR/apps/route_planner/route_planner/planificador_de_rutas/doctype"
alias pced="cd /home/$ERP_USER/projects/ce_sri/development"
alias pcedi="cd /home/$ERP_USER/projects/ce_sri/development/initialization"
alias rtrn="cd $BENCH_DIR/apps/returnable"
alias prbk="cd $BENCH_DIR/sites/$SITE_URL/private/backups"
alias flush="bench --site $SITE_URL migrate; bench --site $SITE_URL clear-cache"
alias bnch="bench --site $SITE_URL "
alias spvstr="sudo -A supervisorctl start all"
alias spvstp="sudo -A supervisorctl stop all"
alias spvrst="sudo -A supervisorctl restart all"
alias cdtmp="cd /dev/shm"
alias shdwn="sudo -A shutdown -P now"
alias maria="mysql $DB_NAME"
alias qmaria="mysql -AD $DB_NAME"
alias nana="nano -c"
alias suda="sudo -A"
alias bert="suda su -"
alias BA="cat /home/$ERP_USER/.bash_aliases"
alias cuwk="cd /home/$ERP_USER/projects/Reports/"
alias chkwd='qmaria -e "select * from watchdog"'
alias wrk="cd /home/$ERP_USER/projects/FichasReconciliation"

ALIASEOF
echo "  [OK] .bash_aliases installed for $ERP_USER"

echo "=== Done ==="
