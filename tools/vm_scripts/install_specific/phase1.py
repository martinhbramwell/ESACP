"""phase1 — Clone BaRe, symlink envars.sh, render bash_aliases."""

import json
import shutil
import subprocess
import sys
from pathlib import Path

from ._env import bench_dir, site_url, user_home


def ensure_bare(bd):
    """Clone BaRe into bench/BaRe if .git missing, else git pull."""
    bare_dir = Path(bd) / "BaRe"
    if (bare_dir / ".git").is_dir():
        subprocess.run(["git", "pull"], cwd=bare_dir, check=True)
        print("  [OK] BaRe pulled")
    else:
        if bare_dir.exists():
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
    bd, su = bench_dir(), site_url()
    print("=== Phase 1: BaRe infrastructure ===")
    ensure_bare(bd)
    ensure_envars_symlink(bd)
    render_bash_aliases(bd, su)
    print("=== Phase 1 complete ===")
