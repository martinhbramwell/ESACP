#!/usr/bin/env python3
"""install_specific.py — Differentiate a generic ERPNext VM into a ce_sri site.

Subcommands (called by differentiate.sh at the right pipeline stages):
  phase1          BaRe clone, envars symlink, bash_aliases
  gate            handleBackup (first run) or handleRestore (subsequent)
  before-install  File patches: ce_sri.conf, site_config, nginx, Procfile, supervisor
  after-restart   API work: custom scripts, logo, naming series, test data

Runs standalone as the bench user — NOT via bench execute.
Config comes from envars.sh (sourced into env) + JSON files on disk.
"""

import argparse
import base64
import configparser
import getpass
import json
import os
import subprocess
import sys
from pathlib import Path
from string import Template
from urllib.error import HTTPError, URLError
from urllib.parse import quote as urlquote
from urllib.request import Request, urlopen


# ---------------------------------------------------------------------------
# Environment helpers
# ---------------------------------------------------------------------------

def env(key, fallback=None):
    """Read an environment variable; abort if required and missing."""
    val = os.environ.get(key, fallback)
    if val is None:
        print(f"[FAIL] Required env var {key} is not set")
        sys.exit(1)
    return val


def bench_dir():
    return env("TARGET_BENCH", os.path.expanduser("~/frappe-bench"))


def user_home():
    """Derive home dir from TARGET_BENCH (immune to sudo HOME pollution)."""
    bd = bench_dir()
    # TARGET_BENCH = /home/<user>/frappe-bench-XXX → parent is /home/<user>
    return str(Path(bd).parent)


def site_url():
    return env("ERPNEXT_SITE_URL")


def erp_user():
    return getpass.getuser()


# ---------------------------------------------------------------------------
# HTTP helpers (stdlib only — no requests dependency)
# ---------------------------------------------------------------------------

def _http(method, url, headers, data=None):
    """Low-level HTTP helper. Returns parsed JSON or raises."""
    body = data.encode("utf-8") if data else None
    req = Request(url, data=body, headers=headers, method=method)
    with urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


_HOST_SITE = None  # set by _load_globals(); sent as Host header


def _auth_headers(api_key):
    hdrs = {
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": f"token {api_key}",
    }
    if _HOST_SITE:
        hdrs["Host"] = _HOST_SITE
    return hdrs


def api_get(url, api_key):
    return _http("GET", url, _auth_headers(api_key))


def api_post(url, api_key, payload):
    return _http("POST", url, _auth_headers(api_key), json.dumps(payload))


def api_put(url, api_key, payload):
    return _http("PUT", url, _auth_headers(api_key), json.dumps(payload))


def api_delete(url, api_key):
    return _http("DELETE", url, _auth_headers(api_key))


# ---------------------------------------------------------------------------
# phase1 — BaRe infrastructure
# ---------------------------------------------------------------------------

def ensure_bare(bd):
    """Clone BaRe into bench/BaRe if .git missing, else git pull."""
    bare_dir = Path(bd) / "BaRe"
    if (bare_dir / ".git").is_dir():
        subprocess.run(["git", "pull"], cwd=bare_dir, check=True)
        print("  [OK] BaRe pulled")
    else:
        if bare_dir.exists():
            import shutil
            shutil.rmtree(bare_dir)
        subprocess.run(
            ["git", "clone", "https://github.com/martinhbramwell/BaRe.git", "BaRe"],
            cwd=bd, check=True,
        )
        print("  [OK] BaRe cloned")


def ensure_envars_symlink(bd):
    """Create BaRe/envars.sh -> /opt/ce_sri/envars.sh symlink."""
    link = Path(bd) / "BaRe" / "envars.sh"
    target = Path("/opt/ce_sri/envars.sh")
    if not target.exists():
        print(f"[FAIL] {target} does not exist")
        sys.exit(1)
    link.unlink(missing_ok=True)
    link.symlink_to(target)
    print(f"  [OK] BaRe/envars.sh -> {target}")


def render_bash_aliases(bd, su):
    """Render bash_aliases from Jinja2 template (or fallback to params)."""
    site_cfg_path = Path(bd) / "sites" / su / "site_config.json"
    db_name = "unknown_db"
    if site_cfg_path.exists():
        db_name = json.loads(site_cfg_path.read_text()).get("db_name", "unknown_db")

    template_path = Path("/tmp/templates/bash_aliases.j2")
    params_path = Path("/tmp/rendered/params.json")
    output_path = Path(user_home()) / ".bash_aliases"

    if template_path.exists() and params_path.exists():
        try:
            import jinja2
        except ImportError:
            subprocess.run([sys.executable, "-m", "pip", "install", "--quiet", "jinja2"],
                           check=True)
            import jinja2
        params = json.loads(params_path.read_text())
        params["db_name"] = db_name
        jenv = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(template_path.parent)),
            keep_trailing_newline=True,
            undefined=jinja2.StrictUndefined,
        )
        rendered = jenv.get_template(template_path.name).render(**params)
        output_path.write_text(rendered)
        print(f"  [OK] .bash_aliases rendered (db_name={db_name})")
    else:
        print("  [SKIP] bash_aliases templates not found at /tmp/")


def cmd_phase1():
    """Subcommand: deploy BaRe, envars symlink, bash_aliases."""
    bd, su = bench_dir(), site_url()
    print("=== Phase 1: BaRe infrastructure ===")
    ensure_bare(bd)
    ensure_envars_symlink(bd)
    render_bash_aliases(bd, su)
    print("=== Phase 1 complete ===")


# ---------------------------------------------------------------------------
# gate — golden backup decision
# ---------------------------------------------------------------------------

def cmd_gate():
    """Subcommand: handleBackup (first run) or handleRestore (subsequent)."""
    bd = bench_dir()
    backup_txt = Path(bd) / "BKP" / "BACKUP.txt"

    if not backup_txt.exists():
        print("=== Gate: no golden backup — running handleBackup ===")
        result = subprocess.run(
            ["bash", "BaRe/handleBackup.sh", "golden generic snapshot"],
            cwd=bd,
        )
        if result.returncode != 0:
            print(f"[FAIL] handleBackup.sh exited {result.returncode}")
            sys.exit(1)
        print("  [OK] Golden backup captured.")
        print("  Copy BKP/*.tgz to controller, then re-run with handleRestore.")
        sys.exit(0)
    else:
        tgz = backup_txt.read_text().strip()
        print(f"=== Gate: golden backup found ({tgz}) — running handleRestore ===")
        result = subprocess.run(["bash", "BaRe/handleRestore.sh"], cwd=bd)
        if result.returncode != 0:
            print(f"[FAIL] handleRestore.sh exited {result.returncode}")
            sys.exit(1)
        print("  [OK] Database restored.")


# ---------------------------------------------------------------------------
# before-install — file patches (no gunicorn needed)
# ---------------------------------------------------------------------------

def read_apikey(bd, su):
    """Read key:secret from apikey.sh."""
    apikey_path = Path(bd) / "sites" / su / "private" / "files" / "apikey.sh"
    if not apikey_path.exists():
        print(f"[FAIL] {apikey_path} not found")
        sys.exit(1)
    line = apikey_path.read_text().strip()
    # Format: KEYS="key:secret" or export KEYS="key:secret"
    for part in line.replace('"', "=").replace("'", "=").split("="):
        if ":" in part and len(part) > 10:
            return part
    print(f"[FAIL] Could not parse API key from {apikey_path}")
    sys.exit(1)


def read_common_site_config(bd):
    """Read webserver_port from common_site_config.json."""
    csc = Path(bd) / "sites" / "common_site_config.json"
    if csc.exists():
        return json.loads(csc.read_text()).get("webserver_port", "8000")
    return "8000"


def write_cesri_conf(bd, su, api_key, port, parms):
    """Write config/ce_sri.conf (ConfigParser INI)."""
    conf_path = Path(bd) / "config" / "ce_sri.conf"
    parser = configparser.ConfigParser()

    # Seed defaults
    parms_dir = str(Path(user_home()) / ".ssh" / "secrets")
    parser["DEFAULT"] = {
        "user_parameters_file_location": parms_dir,
        "certificate_location": parms_dir,
        "nodejs_service_repo": "git@ce_sri_svc.gh:martinhbramwell/ce_sri_svc.git",
        "nodejs_service_name": "electronic_vouchers",
        "nodejs_service_port": "5000",
        "nodejs_service_locator": "ce_sri_svc",
        "nginx_virtual_host_file_name": "nginx.conf",
        "nginx_virtual_host_file_location": str(Path(bd) / "config"),
        "webserver_port": str(port),
        "webserver_protocol": "http",
        "socketio_port": "9000",
        "value_added_tax_rate": "0.12",
        "test_or_production_mode": "1",
    }
    parser["erpnext_api"] = {"erpnext_api_key": api_key, "local_site": su}
    parser["revenue_service"] = {}
    parser["email"] = {}
    parser["pre_install"] = {}
    parser["nodejs_service"] = {}
    parser["http_server"] = {}
    parser["electronic_signature"] = {}
    parser["environment"] = {}

    # Overlay values from ce_sri_parms.json
    _overlay_parms(parser, parms)

    conf_path.parent.mkdir(parents=True, exist_ok=True)
    with open(conf_path, "w") as f:
        parser.write(f)
    print(f"  [OK] {conf_path} written")
    return parser


def _overlay_parms(parser, parms):
    """Copy ce_sri_parms.json sections into the ConfigParser."""
    section_map = {
        "http_server": ["nginx_virtual_host_file_location",
                        "nginx_virtual_host_file_name"],
        "nodejs_service": ["nodejs_service_name", "nodejs_service_repo",
                           "nodejs_service_port"],
        "revenue_service": ["value_added_tax_rate", "test_or_production_mode"],
        "electronic_signature": ["certificate_location", "cert_pwd", "sri_p12_cert"],
        "environment": ["company_tax_id", "company_logo", "company_logo_location",
                        "legal_company_name", "legal_head_office_address",
                        "legal_branch_office_address", "pretty_company_name",
                        "local_site_nickname", "bold_company_name"],
        "email": ["test_destination", "send_from", "send_sender", "send_bcc",
                  "send_replyto", "gmail_smtp_uid", "gmail_smtp_app_pwd"],
    }
    for section, keys in section_map.items():
        if section not in parms:
            continue
        for key in keys:
            val = parms[section].get(key)
            if val is not None and val != "DEFAULT":
                parser.set(section, key, str(val))


def patch_site_config(bd, su):
    """Set developer_mode and ce_sri_url in site_config.json."""
    scfg = Path(bd) / "sites" / su / "site_config.json"
    if not scfg.exists():
        print(f"[FAIL] {scfg} not found")
        sys.exit(1)
    cfg = json.loads(scfg.read_text())
    cfg["developer_mode"] = 1
    cfg["ce_sri_url"] = f"http://{su}:5000"
    scfg.write_text(json.dumps(cfg, indent=1))
    print("  [OK] site_config.json patched (developer_mode, ce_sri_url)")


def _nginx_upstream_block(marker, port):
    """Generate the nginx upstream block for ce_sri_svc."""
    return (
        f"\nupstream {marker} {{\n"
        f"  server 127.0.0.1:{port} fail_timeout=0;\n"
        f"}}\n\n"
    )


def _nginx_location_block(marker, locator):
    """Generate the nginx location block for ce_sri_svc."""
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
    """Insert ce_sri_svc upstream + location blocks into config/nginx.conf."""
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


def patch_procfile(bd, cfg):
    """Add ce_sri_svc line to Procfile if missing."""
    procfile = Path(bd) / "Procfile"
    if not procfile.exists():
        print("  [SKIP] Procfile not found")
        return
    locator = cfg.get("nodejs_service", "nodejs_service_locator",
                       fallback="ce_sri_svc")
    content = procfile.read_text()
    if locator in content:
        print("  [SKIP] Procfile already contains ce_sri_svc")
        return
    line = f"\n# {locator}: apps/ce_sri/services/{locator}/go.sh\n"
    procfile.write_text(content + line)
    print("  [OK] Procfile patched")


def patch_supervisor_conf(bd, cfg):
    """Add ce_sri_svc program section to supervisor.conf if missing."""
    conf = Path(bd) / "config" / "supervisor.conf"
    if not conf.exists():
        print("  [SKIP] config/supervisor.conf not found")
        return
    content = conf.read_text()
    if "electronic_vouchers-service" in content:
        print("  [SKIP] supervisor.conf already patched")
        return
    nickname = cfg.get("environment", "local_site_nickname", fallback="GENERIC")
    svc_dir = str(Path(bd) / "apps" / "ce_sri" / "services" / "ce_sri_svc")
    section = (
        f"\n[program:electronic_vouchers-service-{nickname}]\n"
        f"command={svc_dir}/go.sh\n"
        f"priority=3\nautostart=true\nautorestart=true\n"
        f"stdout_logfile={bd}/logs/ce_sri_svc.log\n"
        f"stderr_logfile={bd}/logs/ce_sri_svc.error.log\n"
        f"user={erp_user()}\ndirectory={svc_dir}\n\n"
    )
    # Insert before the first [program: line
    if "[program:" in content:
        content = content.replace("[program:", f"{section}[program:", 1)
    else:
        content += section
    conf.write_text(content)
    print("  [OK] supervisor.conf patched")


def verify_p12_cert(cfg):
    """Check the P12 certificate exists."""
    cert_path = cfg.get("electronic_signature", "certificate_location",
                        fallback=str(Path(user_home()) / ".ssh" / "secrets"))
    cert_name = cfg.get("electronic_signature", "sri_p12_cert", fallback="")
    if not cert_name:
        print("  [SKIP] no sri_p12_cert configured")
        return
    full = Path(cert_path) / cert_name
    if full.exists():
        print(f"  [OK] P12 cert found: {full}")
    else:
        print(f"  [WARN] P12 cert not found: {full}")


def cmd_before_install():
    """Subcommand: file patches — no gunicorn needed."""
    bd, su = bench_dir(), site_url()
    print("=== before-install: file patches ===")

    api_key = read_apikey(bd, su)
    port = read_common_site_config(bd)

    # Load ce_sri_parms.json
    parms_path = Path(user_home()) / ".ssh" / "secrets" / "ce_sri_parms.json"
    parms = {}
    if parms_path.exists():
        parms = json.loads(parms_path.read_text())
    else:
        print(f"  [WARN] {parms_path} not found — using defaults")

    cfg = write_cesri_conf(bd, su, api_key, port, parms)
    verify_p12_cert(cfg)
    patch_site_config(bd, su)
    patch_nginx_conf(bd, cfg)
    patch_procfile(bd, cfg)
    patch_supervisor_conf(bd, cfg)
    print("=== before-install complete ===")


# ---------------------------------------------------------------------------
# after-restart — API work (gunicorn must be running)
# ---------------------------------------------------------------------------

def _load_globals(bd, su):
    """Load ce_sri.conf and derive API URLs + key.

    URLs use localhost (gunicorn binds 127.0.0.1); the site name is
    stored in _HOST_SITE so _auth_headers adds it as Host header for
    Frappe multi-tenant routing.
    """
    global _HOST_SITE
    cfg = configparser.ConfigParser()
    conf_path = Path(bd) / "config" / "ce_sri.conf"
    if not conf_path.exists():
        print(f"[FAIL] {conf_path} not found — run before-install first")
        sys.exit(1)
    cfg.read(conf_path)
    site = cfg.get("erpnext_api", "local_site", fallback=su)
    port = cfg.get("erpnext_api", "webserver_port", fallback="8000")
    key = cfg.get("erpnext_api", "erpnext_api_key")
    _HOST_SITE = site
    base = f"http://localhost:{port}/api"
    return cfg, key, f"{base}/resource", f"{base}/method"


def confirm_api_connection(rsrc_url, api_key):
    """GET /api/resource/Company — verify ERPNext API is reachable."""
    url = f"{rsrc_url}/Company"
    try:
        resp = api_get(url, api_key)
        name = resp["data"][0]["name"]
        print(f"  [OK] ERPNext API connected — company: {name}")
        return True
    except (URLError, HTTPError, KeyError, IndexError) as e:
        print(f"[FAIL] ERPNext API unreachable: {e}")
        sys.exit(1)


def install_custom_scripts(bd, rsrc_url, api_key):
    """DELETE + POST the Sales_Invoice-Form Client Script."""
    dt = "Sales Invoice"
    record = f"{dt}-Form"
    script_type = "Client Script"
    api_url = f"{rsrc_url}/{urlquote(script_type)}"
    encoded_record = urlquote(record)

    # Find the JS file in the ce_sri app
    js_path = Path(bd) / "apps" / "ce_sri" / "ce_sri" / "frags" / "Sales_Invoice-Form.js"
    if not js_path.exists():
        print(f"  [SKIP] {js_path} not found")
        return

    script_text = js_path.read_text()
    try:
        api_delete(f"{api_url}/{encoded_record}", api_key)
        print(f"  [OK] Deleted previous Client Script '{record}'")
    except (URLError, HTTPError):
        print(f"  [INFO] No previous Client Script '{record}' to delete")

    payload = {"dt": dt, "enabled": 1, "script": script_text, "doctype": script_type}
    resp = api_post(api_url, api_key, payload)
    print(f"  [OK] Created Client Script '{resp['data']['name']}'")


def install_company_logo(rsrc_url, mthd_url, api_key, cfg):
    """Upload logo, set Website Settings and Company logo."""
    logo_dir = cfg.get("environment", "company_logo_location", fallback="")
    logo_file = cfg.get("environment", "company_logo", fallback="")
    if not logo_dir or not logo_file:
        print(f"  [SKIP] Logo config missing (dir={logo_dir!r}, file={logo_file!r})")
        return
    logo_path = Path(logo_dir) / logo_file
    if not logo_path.exists():
        print(f"  [SKIP] Logo not found at {logo_path}")
        return

    logo_name = logo_path.name
    b64 = base64.b64encode(logo_path.read_bytes()).decode("utf-8")

    # Upload via frappe.client.attach_file
    attach_url = f"{mthd_url}/frappe.client.attach_file"
    api_post(attach_url, api_key, {
        "doctype": "Website Settings",
        "docname": "Website Settings",
        "filename": logo_name,
        "decode_base64": 1,
        "filedata": b64,
    })
    print(f"  [OK] Logo uploaded: {logo_name}")

    # Set Website Settings
    ws_url = f"{rsrc_url}/{urlquote('Website Settings')}/{urlquote('Website Settings')}"
    api_put(ws_url, api_key, {
        "banner_image": f"/files/{logo_name}",
        "brand_html": f'<img src="/files/{logo_name}" style="max-height: 80px;">',
    })

    # Set Company logo
    company = cfg.get("environment", "pretty_company_name", fallback="")
    if company:
        co_url = f"{rsrc_url}/Company/{urlquote(company)}"
        api_put(co_url, api_key, {"company_logo": f"/files/{logo_name}"})
    print("  [OK] Website branding installed")


def get_starting_number():
    """Fetch + increment the shared invoice counter."""
    url = "https://json.extendsclass.com/bin/2ac2f4154c43"
    headers = {"Security-key": "4ba0d416-d78f-11ec-b943-0242ac110002"}
    req = Request(url, headers=headers)
    with urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read())
    starting = data["nxt"]
    # Increment
    body = json.dumps({"nxt": starting + 1}).encode()
    put_req = Request(url, data=body, headers={**headers,
                      "Content-Type": "application/json"}, method="PUT")
    urlopen(put_req, timeout=15)
    print(f"  [OK] Starting number: {starting}")
    return starting


def install_naming_series(rsrc_url, mthd_url, api_key, test_suc_pde, starting):
    """Set up the SRI-mandated naming series for Sales Invoice."""
    srvr_url = f"{mthd_url}/runserverobj"

    # Get Naming Series modified date
    ns_url = f"{rsrc_url}/{urlquote('Naming Series')}/{urlquote('Naming Series')}"
    resp = api_get(ns_url, api_key)
    modified = resp["data"]["modified"]

    # Create series
    series = test_suc_pde
    api_post(srvr_url, api_key, {
        "method": "update_series",
        "docs": {
            "name": "Naming Series", "prefix": "001-001-.#########",
            "doctype": "Naming Series",
            "select_doc_for_series": "Sales Invoice",
            "set_options": f"001-001-.#########\n{series}-.#########",
            "modified": modified,
        },
    })
    print(f"  [OK] Naming series '{series}' created")

    # Set start value
    api_post(srvr_url, api_key, {
        "method": "update_series_start",
        "docs": {
            "name": "Naming Series", "doctype": "Naming Series",
            "select_doc_for_series": "Sales Invoice",
            "prefix": f"{series}-.#########",
            "current_value": starting,
            "modified": modified,
        },
    })
    print(f"  [OK] Series start value set to {starting}")


def install_test_data(rsrc_url, api_key, test_suc_pde):
    """Idempotently create test Customer, Item, Address, Invoice."""
    datasets = [
        ("Item Group", "Grupo de Prueba", {
            "parent": "Todos los Grupos de Artículos",
            "item_group_name": "Grupo de Prueba",
            "parent_item_group": "Todos los Grupos de Artículos",
        }),
        ("Customer Group", "Grupo de Prueba", {
            "parent_customer_group": "Todas las categorías de clientes",
            "customer_group_name": "Grupo de Prueba",
        }),
        ("Item", "Item de Prueba", {
            "item_code": "Item de Prueba",
            "item_group": "Grupo de Prueba",
        }),
        ("Customer", "Cliente de Prueba", {
            "customer_name": "Cliente de Prueba",
            "tax_id": "1793141528001",
            "customer_details": "id_bapu = '0'",
            "territory": "Ecuador",
            "customer_group": "Grupo de Prueba",
        }),
        ("Address", "Cliente de Prueba-Postal", {
            "address_line1": "10123 Avenida de Pruebas",
            "city": "Pruebaburgo",
            "email_id": "prueba.cliente@hotmail.com",
            "phone": "2376543",
            "address_type": "Postal",
            "links": [{"link_doctype": "Customer", "link_name": "Cliente de Prueba"}],
        }),
        ("Sales Invoice", f"{test_suc_pde}-000000000", {
            "naming_series": f"{test_suc_pde}-.#########",
            "customer": "Cliente de Prueba",
            "tax_id": "1793141528001",
            "due_date": "2028-05-24",
            "items": [{"item_code": "Item de Prueba", "qty": 1, "rate": 1}],
        }),
    ]
    _create_test_records(rsrc_url, api_key, datasets)


def _create_test_records(rsrc_url, api_key, datasets):
    """GET-then-POST each record; skip if it already exists."""
    for doc_type, doc_name, record in datasets:
        post_url = f"{rsrc_url}/{urlquote(doc_type)}"
        get_url = f"{post_url}/{urlquote(doc_name)}"
        try:
            resp = api_get(get_url, api_key)
            if "exc_type" in resp and resp["exc_type"] == "DoesNotExistError":
                raise URLError("not found")
            print(f"  [OK] {doc_type} '{resp['data']['name']}' exists")
        except (URLError, HTTPError, KeyError):
            resp = api_post(post_url, api_key, record)
            print(f"  [OK] Created {doc_type} '{resp['data']['name']}'")


def cmd_after_restart():
    """Subcommand: API work — gunicorn must be running."""
    bd, su = bench_dir(), site_url()
    print("=== after-restart: API configuration ===")

    cfg, api_key, rsrc_url, mthd_url = _load_globals(bd, su)
    test_suc_pde = "001-004"

    confirm_api_connection(rsrc_url, api_key)
    install_custom_scripts(bd, rsrc_url, api_key)
    install_company_logo(rsrc_url, mthd_url, api_key, cfg)

    try:
        starting = get_starting_number()
    except (URLError, HTTPError) as e:
        print(f"  [WARN] Could not reach starting number service: {e}")
        starting = 0

    install_naming_series(rsrc_url, mthd_url, api_key, test_suc_pde, starting)
    install_test_data(rsrc_url, api_key, test_suc_pde)
    print("=== after-restart complete ===")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("phase1", help="BaRe clone, envars symlink, bash_aliases")
    sub.add_parser("gate", help="handleBackup (first run) or handleRestore")
    sub.add_parser("before-install", help="File patches (no gunicorn needed)")
    sub.add_parser("after-restart", help="API work (gunicorn must be running)")
    args = parser.parse_args()

    commands = {
        "phase1": cmd_phase1,
        "gate": cmd_gate,
        "before-install": cmd_before_install,
        "after-restart": cmd_after_restart,
    }
    fn = commands.get(args.command)
    if fn is None:
        parser.print_help()
        sys.exit(1)
    fn()


if __name__ == "__main__":
    main()
