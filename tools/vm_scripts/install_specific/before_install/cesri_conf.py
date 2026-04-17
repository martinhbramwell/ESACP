"""Write config/ce_sri.conf from ce_sri_parms.json overlay."""

import configparser
from pathlib import Path

from .._env import user_home


_OVERLAY_SECTIONS = {
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


def _overlay_parms(parser, parms):
    """Copy ce_sri_parms.json sections into the ConfigParser."""
    for section, keys in _OVERLAY_SECTIONS.items():
        if section not in parms:
            continue
        for key in keys:
            val = parms[section].get(key)
            if val is not None and val != "DEFAULT":
                parser.set(section, key, str(val))


def _seed_defaults(bd, port):
    parms_dir = str(Path(user_home()) / ".ssh" / "secrets")
    return {
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


def write_cesri_conf(bd, su, api_key, port, parms):
    """Write config/ce_sri.conf (ConfigParser INI)."""
    conf_path = Path(bd) / "config" / "ce_sri.conf"
    parser = configparser.ConfigParser()
    parser["DEFAULT"] = _seed_defaults(bd, port)
    parser["erpnext_api"] = {"erpnext_api_key": api_key, "local_site": su}
    for sec in ("revenue_service", "email", "pre_install", "nodejs_service",
                "http_server", "electronic_signature", "environment"):
        parser[sec] = {}
    _overlay_parms(parser, parms)
    conf_path.parent.mkdir(parents=True, exist_ok=True)
    with open(conf_path, "w") as f:
        parser.write(f)
    print(f"  [OK] {conf_path} written")
    return parser
