"""Insert ce_sri_svc upstream + location blocks into config/nginx.conf."""

from pathlib import Path


def _nginx_upstream_block(marker, port):
    return (
        f"\nupstream {marker} {{\n"
        f"  server 127.0.0.1:{port} fail_timeout=0;\n"
        f"}}\n\n"
    )


def _nginx_location_block(marker, locator):
    return (
        f"\n  location /{locator}/ {{\n"
        f"    proxy_http_version 1.1;\n"
        f"    proxy_set_header Upgrade $http_upgrade;\n"
        f'    proxy_set_header Connection "upgrade";\n'
        f"    proxy_set_header X-Frappe-Site-Name $host;\n"
        f"    proxy_set_header Origin $scheme://$http_host;\n"
        f"    proxy_set_header Host $host;\n\n"
        f"    proxy_pass http://{marker}/;\n"
        f"  }}\n\n"
    )


def patch_nginx_conf(bd, cfg):
    nginx_path = Path(bd) / "config" / "nginx.conf"
    if not nginx_path.exists():
        print("  [SKIP] config/nginx.conf not found")
        return

    svc_name = cfg.get("nodejs_service", "nodejs_service_name",
                       fallback="electronic_vouchers")
    svc_port = cfg.get("nodejs_service", "nodejs_service_port", fallback="5000")
    svc_locator = cfg.get("nodejs_service", "nodejs_service_locator",
                          fallback="ce_sri_svc")
    nickname = cfg.get("environment", "local_site_nickname", fallback="GENERIC")
    marker = f"{svc_name}-service-{nickname}"

    content = nginx_path.read_text()
    if marker in content:
        print("  [SKIP] nginx.conf already patched for ce_sri_svc")
        return

    content = content.replace("\nserver {",
                              f"{_nginx_upstream_block(marker, svc_port)}server {{", 1)
    content = content.replace("\n  location / {\n",
                              f"{_nginx_location_block(marker, svc_locator)}  location / {{\n", 1)

    nginx_path.write_text(content)
    print("  [OK] nginx.conf patched with ce_sri_svc upstream + location")
