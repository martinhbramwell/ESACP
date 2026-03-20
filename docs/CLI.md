# ESACP CLI Reference — tools/esacp.py

Single entry point for the full lab lifecycle. Run from the project root:

```
python tools/esacp.py <subcommand> [options]
```

All defaults are read from `hosts_map.yml` and `ansible/group_vars/`. No environment
variables required beyond the SOPS age key at `~/.config/sops/age/keys.txt`.

---

## Subcommands

| Subcommand | What it does |
|---|---|
| `confirmPrerequisites` | Checks required tools and files; offers to `apt install` missing packages |
| `validateKeys` | SOPS-decrypts `config/wireguard/keys.sops.yml`; verifies all key blocks exist |
| `clearKnownHosts` | Removes stale `~/.ssh/known_hosts` entries for all ESACP VMs (hostnames, nicknames, IPs) |
| `destroyVM <vm>` | Shows what will be deleted, asks for confirmation, then destroys VM + all storage |
| `buildVM <vm>` | Builds seed ISO → creates VM → polls for autoinstall completion → polls SSH |
| `provisionVM <vm>` | SSH check → Fresh Install snapshot → Ansible (task names + changes only) → Baseline snapshot |
| `verifyVPN` | Pings each VM's WireGuard IP; shows `wg show` on hub; cross-VM pings |
| `validateObservability` | Auto-retrieves Grafana creds (env → saconsole .env → prompt); runs 27-check suite |
| `snapShotVM <vm> [name]` | Creates a named snapshot; if name omitted, lists existing snapshots |
| `displayConfiguration` | Rich tree of all user-alterable settings, each annotated with its source file |

---

## Non-obvious behaviours

**`provisionVM` Ansible output filter**: shows PLAY headers, ✓ ok tasks, ★ changed
tasks, ❌ fatal errors, and the PLAY RECAP summary. All other Ansible output is suppressed.

**`validateObservability` credential resolution order**:
1. `GRAFANA_ADMIN_USER` / `GRAFANA_ADMIN_PASSWORD` environment variables
2. SSH to saconsole → read `/opt/observability/.env`
3. Interactive prompt

All check targets (jobs, nodenames, datasource UIDs, dashboard titles) are derived
from the project's own config files — nothing is hardcoded in the script.

**`snapShotVM` is KVM-only**: hardwired to `platforms/kvm/snapshot.py` → `virsh`.

---

## Observability validation flags

```bash
python3 orchestration/validate_observability.py            # auto-detects saconsole
python3 orchestration/validate_observability.py --obs-host <name>   # explicit host
python3 orchestration/validate_observability.py -v         # verbose (show passing detail)
```
