# erpnext-v13.pkr.hcl — Packer build definition for undifferentiated ERPNext v13 image
#
# Strategy: null builder — the build VM is created and destroyed by build.sh;
# Packer's only job is to SSH in, run the provisioner scripts, and exit cleanly.
#
# "Undifferentiated" means: Ubuntu 22.04 + MariaDB + frappe-bench + frappe + erpnext.
# No site. No bespoke apps. No production data.
# Everything site-specific is applied at deploy time from the Cytoscape stockroom.
#
# Run via: bash platforms/packer/build.sh
# Do NOT run packer directly — build.sh creates the VM and passes VM_IP.

packer {
  required_version = ">= 1.9.0"
}

# ── Variables ──────────────────────────────────────────────────────────────────

variable "vm_ip" {
  type        = string
  description = "IP of the packer-build VM on toshiba's virbr0 (set by build.sh)"
  default     = "192.168.122.20"
}

variable "ssh_username" {
  type    = string
  default = "you"
}

variable "ssh_private_key_file" {
  type        = string
  description = "Path to saconsole's SSH private key (absolute)"
  default     = "/home/you/.ssh/id_ed25519"
}

variable "frappe_branch" {
  type    = string
  default = "version-13"
}

variable "erpnext_branch" {
  type    = string
  default = "version-13"
}

# ── Source: null builder ───────────────────────────────────────────────────────
#
# The null builder does not create or manage a VM — build.sh handles that.
# Packer opens an SSH connection to vm_ip and runs the provisioners.

source "null" "erpnext-v13" {
  communicator         = "ssh"
  ssh_host             = var.vm_ip
  ssh_username         = var.ssh_username
  ssh_private_key_file = var.ssh_private_key_file
  ssh_timeout          = "90m"   # ERPNext v13 bench init can take 30-45 min
  ssh_handshake_attempts = 20
}

# ── Build ──────────────────────────────────────────────────────────────────────

build {
  name    = "erpnext-v13"
  sources = ["source.null.erpnext-v13"]

  # Phase 1: OS preparation
  # Installs system packages, MariaDB, NodeJS, wkhtmltopdf, creates bench user 'adm'.
  # Reboots the VM at the end — Packer waits for SSH to return before proceeding.
  provisioner "shell" {
    script          = "${path.root}/scripts/01_os_prep.sh"
    execute_command = "sudo bash {{ .Path }}"
    expect_disconnect = true   # VM reboots at end of this script
    pause_after     = "30s"
  }

  # Phase 2: Bench + frappe + erpnext apps
  # bench init → bench get-app frappe → bench get-app erpnext → bench setup requirements
  # Stops BEFORE bench new-site — no site, no data.
  provisioner "shell" {
    script          = "${path.root}/scripts/02_bench_install.sh"
    execute_command = "sudo -Hu adm bash {{ .Path }}"
    environment_vars = [
      "FRAPPE_BRANCH=${var.frappe_branch}",
      "ERPNEXT_BRANCH=${var.erpnext_branch}",
    ]
    timeout = "60m"
  }

  # Phase 3: Frappe v13 dependency fix
  # uv pip install in phase 2 pulls incompatible versions; this pins them correctly.
  # See feedback_frappe_v13_deps.md for full explanation.
  provisioner "shell" {
    script          = "${path.root}/scripts/03_dep_fix.sh"
    execute_command = "sudo -Hu adm bash {{ .Path }}"
  }

  # Phase 4: Cleanup — remove SSH host keys, machine-id, apt caches
  # Ensures each VM deployed from this image gets a fresh identity.
  provisioner "shell" {
    script          = "${path.root}/scripts/04_generalise.sh"
    execute_command = "sudo bash {{ .Path }}"
  }
}
