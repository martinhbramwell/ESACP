"""install_specific — Differentiate a generic ERPNext VM into a ce_sri site.

Subcommands re-exported for the thin entry at tools/install_specific.py:
  cmd_phase1          BaRe clone, envars symlink, bash_aliases
  cmd_gate            handleBackup (first run) or handleRestore
  cmd_before_install  File patches: ce_sri.conf, site_config, nginx, Procfile, supervisor
  cmd_after_restart   API work: Client Scripts, logo, naming series, test data

Runs standalone as the bench user — NOT via bench execute. Config from
envars.sh (sourced into env) + JSON files on disk. Stdlib only.
"""

from .after_restart import cmd_after_restart
from .before_install import cmd_before_install
from .gate import cmd_gate
from .phase1 import cmd_phase1

__all__ = ["cmd_phase1", "cmd_gate", "cmd_before_install", "cmd_after_restart"]
