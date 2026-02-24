#!/usr/bin/env python3
"""
ESACP Provisioning Orchestrator
Manages VM lifecycle and Ansible provisioning

Usage:
    python3 provision.py --target dev                # Provision dev VM
    python3 provision.py --target dev --revert       # Revert to baseline first
    python3 provision.py --target dev --check        # Dry run
"""

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent
ANSIBLE_DIR = PROJECT_ROOT / "ansible"
ORCHESTRATION_DIR = PROJECT_ROOT / "orchestration"

# VM configurations
# DEV_VM_HOSTNAME and SNAPSHOT_NAME are read from environment variables so they
# match the values set in the operator's shell session (see SETUP_GUIDE.md).
# PROD_HOSTNAME is separate — production targets are VPSes, not local VMs.
VM_CONFIGS = {
    "dev": {
        "name": os.environ.get("VM_HOSTNAME", "esacp-dev"),
        "inventory": "dev.yml",
        "snapshot": os.environ.get("SNAPSHOT_NAME", "baseline"),
        "description": "VirtualBox development VM"
    },
    "prod": {
        "name": os.environ.get("PROD_HOSTNAME", "esacp-prod"),
        "inventory": "prod.yml",
        "snapshot": None,  # Production VPSes don't use snapshots
        "description": "Production VPS deployment"
    }
}


def print_banner(message):
    """Print a formatted banner message"""
    width = max(60, len(message) + 4)
    print("\n" + "=" * width)
    print(f"  {message}")
    print("=" * width + "\n")


def run_command(cmd, check=True, capture_output=False):
    """Run a shell command"""
    print(f"→ Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            check=check,
            capture_output=capture_output,
            text=True
        )
        return result
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed with exit code {e.returncode}")
        if capture_output:
            print(f"STDOUT: {e.stdout}")
            print(f"STDERR: {e.stderr}")
        sys.exit(1)


def check_prerequisites():
    """Verify required tools are installed"""
    print_banner("Checking Prerequisites")
    
    required_tools = {
        "ansible": "ansible --version",
        "ansible-playbook": "ansible-playbook --version",
        "sops": "sops --version",
        "age": "age --version",
    }
    
    missing = []
    for tool, check_cmd in required_tools.items():
        try:
            subprocess.run(
                check_cmd.split(),
                check=True,
                capture_output=True
            )
            print(f"✓ {tool} found")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(f"✗ {tool} not found")
            missing.append(tool)
    
    if missing:
        print(f"\n❌ Missing required tools: {', '.join(missing)}")
        print("Please install them before continuing.")
        sys.exit(1)
    
    print("\n✅ All prerequisites satisfied")


def revert_vm_to_baseline(vm_name, snapshot_name):
    """Revert VM to baseline snapshot"""
    print_banner(f"Reverting {vm_name} to snapshot: {snapshot_name}")
    
    # Check if revertToBaseline.py exists
    revert_script = ORCHESTRATION_DIR / "revertToBaseline.py"
    if not revert_script.exists():
        print(f"⚠️  revertToBaseline.py not found at {revert_script}")
        print("    Skipping snapshot revert")
        return False
    
    # Run revert script
    run_command([
        "python3",
        str(revert_script),
        "--vm", vm_name,
        "--snapshot", snapshot_name
    ])
    
    print(f"✅ VM reverted to {snapshot_name}")
    return True


def wait_for_ssh(inventory_file, timeout=300):
    """Wait for SSH to become available"""
    print_banner("Waiting for SSH Connection")
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            result = subprocess.run(
                [
                    "ansible",
                    "all",
                    "-i", str(ANSIBLE_DIR / "inventory" / inventory_file),
                    "-m", "ping",
                    "--one-line"
                ],
                check=True,
                capture_output=True,
                text=True
            )
            
            if "SUCCESS" in result.stdout:
                print("✅ SSH connection established")
                return True
        except subprocess.CalledProcessError:
            pass
        
        print(".", end="", flush=True)
        time.sleep(5)
    
    print(f"\n❌ SSH connection timeout after {timeout} seconds")
    return False


def run_ansible_playbook(inventory_file, check_mode=False, tags=None):
    """Execute Ansible playbook"""
    print_banner("Running Ansible Playbook")

    # Ensure ansible.cfg is loaded from ansible/ regardless of CWD
    env = os.environ.copy()
    env["ANSIBLE_CONFIG"] = str(ANSIBLE_DIR / "ansible.cfg")

    # SSH key: honour SSH_KEY_PATH env var, fall back to default
    ssh_key_path = os.environ.get("SSH_KEY_PATH", os.path.expanduser("~/.ssh/id_ed25519"))
    env["ANSIBLE_PRIVATE_KEY_FILE"] = ssh_key_path

    # Remote user: honour ADMIN_USER_NAME env var if set (inventory takes precedence
    # at the host level, but this provides a controller-wide fallback)
    admin_user = os.environ.get("ADMIN_USER_NAME")
    if admin_user:
        env["ANSIBLE_REMOTE_USER"] = admin_user

    cmd = [
        "ansible-playbook",
        "-i", str(ANSIBLE_DIR / "inventory" / inventory_file),
        str(ANSIBLE_DIR / "site.yml"),
        "-v"
    ]

    if check_mode:
        cmd.append("--check")
        print("ℹ️  Running in CHECK mode (dry run)")

    if tags:
        cmd.extend(["--tags", tags])
        print(f"ℹ️  Running only tags: {tags}")

    print(f"→ Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, check=True, env=env, text=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ ansible-playbook failed with exit code {e.returncode}")
        sys.exit(1)
    print("\n✅ Ansible playbook completed successfully")


def main():
    parser = argparse.ArgumentParser(
        description="ESACP Provisioning Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--target",
        choices=["dev", "prod"],
        required=True,
        help="Target environment to provision"
    )
    
    parser.add_argument(
        "--revert",
        action="store_true",
        help="Revert VM to baseline snapshot before provisioning"
    )
    
    parser.add_argument(
        "--check",
        action="store_true",
        help="Run in check mode (dry run, no changes)"
    )
    
    parser.add_argument(
        "--tags",
        help="Only run specific Ansible tags (comma-separated)"
    )
    
    parser.add_argument(
        "--skip-ssh-wait",
        action="store_true",
        help="Skip waiting for SSH (use if VM is already running)"
    )
    
    args = parser.parse_args()
    
    # Get VM configuration
    config = VM_CONFIGS[args.target]
    
    print_banner(f"ESACP Provisioner - {config['description']}")
    print(f"Target: {args.target}")
    print(f"VM: {config['name']}")
    print(f"Inventory: {config['inventory']}")
    if args.revert:
        print(f"Snapshot: {config['snapshot']}")
    
    # Step 1: Check prerequisites
    check_prerequisites()
    
    # Step 2: Revert VM to baseline (if requested and supported)
    if args.revert:
        if config["snapshot"]:
            revert_vm_to_baseline(config["name"], config["snapshot"])
        else:
            print(f"⚠️  Snapshot revert not supported for {args.target}")
    
    # Step 3: Wait for SSH (if not skipped)
    if not args.skip_ssh_wait:
        if not wait_for_ssh(config["inventory"]):
            print("❌ Cannot proceed without SSH access")
            sys.exit(1)
    
    # Step 4: Run Ansible playbook
    run_ansible_playbook(
        config["inventory"],
        check_mode=args.check,
        tags=args.tags
    )
    
    # Done
    print_banner("✅ Provisioning Complete!")
    print(f"\nYour {args.target} environment is ready.")
    print(f"\nAccess services:")
    print(f"  Grafana: https://<VM_IP>/grafana/")
    print(f"  Prometheus: http://<VM_IP>:9090")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
