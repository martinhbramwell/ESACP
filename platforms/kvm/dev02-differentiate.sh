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

echo "=== A3: start bench services (supervisor) ==="
# Packer template never ran 'bench setup supervisor' — do it now before any bench commands
sudo -u "$ERP_USER" bash -c "cd $BENCH_DIR && bench setup supervisor --yes"
sudo cp "$BENCH_DIR/config/supervisor.conf" /etc/supervisor/conf.d/frappe-bench.conf
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

echo "=== C: BaRe/envars.sh symlink ==="
sudo -u "$ERP_USER" ln -sf /opt/ce_sri/envars.sh "$BENCH_DIR/BaRe/envars.sh"
echo "  [OK] BaRe/envars.sh -> /opt/ce_sri/envars.sh"

echo "=== D: bench new-site + install-app erpnext ==="
echo "  site: $SITE_URL  bench: $BENCH_DIR"
sudo -u "$ERP_USER" bash -c "
  cd $BENCH_DIR
  bench new-site $SITE_URL \
    --mariadb-root-password $MYPWD \
    --admin-password $ERP_USER_PWD
  bench --site $SITE_URL install-app erpnext
"
echo "  [OK] site created, erpnext installed"

echo "=== E: place ddlViews.sql ==="
sudo -u "$ERP_USER" mkdir -p "$BENCH_DIR/sites/$SITE_URL/private/files"
  sudo -u erpadm cp /tmp/ddlViews.sql /home/erpadm/frappe-bench-D2IRBL/sites/dev02.iridium.blue/private/files/ddlViews.sql
  rm -f /tmp/ddlViews.sql
  echo '  [OK] ddlViews.sql placed'

echo "=== F: installApps.sh ==="
sudo -u "$ERP_USER" bash -c "cd $BENCH_DIR && bash BaRe/installApps.sh"
echo "  [OK] installApps.sh complete"

echo "=== G: handleRestore.sh ==="
sudo -u "$ERP_USER" bash -c "cd $BENCH_DIR && bash BaRe/handleRestore.sh"
echo "  [OK] database restored"

echo "=== H: supervisor reload (post-restore) ==="
sudo supervisorctl reread
sudo supervisorctl update
echo "  [OK] supervisor updated"

echo "=== H2: bench restart ==="
sudo -u "$ERP_USER" bash -c "cd $BENCH_DIR && bench restart || true"
echo "  [OK] bench restarted"

echo "=== H3: reset admin password (bench restore overwrites it) ==="
sudo -u "$ERP_USER" bash -c "cd $BENCH_DIR && bench --site $SITE_URL set-admin-password $ERP_USER_PWD"
echo "  [OK] admin password reset to ERP_USER_PWD"

echo "=== I: install TLS cert ==="
sudo mkdir -p /etc/nginx/certs/iridium.blue
sudo cp /tmp/fullchain.pem /etc/nginx/certs/iridium.blue/fullchain.pem
sudo cp /tmp/privkey.pem   /etc/nginx/certs/iridium.blue/privkey.pem
sudo chmod 600 /etc/nginx/certs/iridium.blue/privkey.pem
sudo rm -f /tmp/fullchain.pem /tmp/privkey.pem /tmp/cert.pem
echo "  [OK] certs installed to /etc/nginx/certs/iridium.blue"

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
    echo "  Generating DH params (2048-bit) ..."
    sudo openssl dhparam -out /etc/nginx/dhparam.pem 2048
fi
sudo ln -sf /etc/nginx/sites-available/dev02.iridium.blue /etc/nginx/sites-enabled/dev02.iridium.blue
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx
echo "  [OK] nginx reloaded with SSL site"

echo "=== Done ==="
