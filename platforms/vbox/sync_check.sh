#!/usr/bin/env bash
# sync_check.sh — VBox platform sync session checklist
#
# Run at the start of every Windows/WSL session before doing any other work.
# Objective: verify environment matches memory, fix drift, commit, push.
# If any check fails, fix it before proceeding to a new session.
#
# Usage (from project root):
#   bash platforms/vbox/sync_check.sh

set -euo pipefail

PASS=0
FAIL=0
WARN=0

ok()   { echo "  ✅  $1"; PASS=$((PASS+1)); }
fail() { echo "  ❌  $1"; FAIL=$((FAIL+1)); }
warn() { echo "  ⚠️   $1"; WARN=$((WARN+1)); }
hdr()  { echo ""; echo "── $1 ──────────────────────────────────────────"; }

find_vboxmanage() {
    for candidate in "VBoxManage" "VBoxManage.exe" \
                     "/mnt/c/Program Files/Oracle/VirtualBox/VBoxManage.exe"; do
        if command -v "${candidate}" &>/dev/null || [[ -f "${candidate}" ]]; then
            echo "${candidate}"; return
        fi
    done
    echo ""
}

VBM="$(find_vboxmanage)"

echo ""
echo "ESACP VBox Platform — Sync Check"
echo "================================="

# ── 1. Git state ──────────────────────────────────────────────────────────────
hdr "1. Git"

cd "$(git rev-parse --show-toplevel)"

BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [[ "${BRANCH}" == "main" ]]; then
    ok "On main branch"
else
    warn "On branch '${BRANCH}' — expected main"
fi

git fetch --quiet origin 2>/dev/null
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/main 2>/dev/null || echo "unknown")
if [[ "${LOCAL}" == "${REMOTE}" ]]; then
    ok "Up to date with origin/main"
else
    warn "Local differs from origin/main — pull or push needed"
fi

DIRTY=$(git status --porcelain)
if [[ -z "${DIRTY}" ]]; then
    ok "Working tree clean"
else
    warn "Uncommitted changes present"
    git status --short
fi

# ── 2. SSH key ─────────────────────────────────────────────────────────────────
hdr "2. SSH key"

if [[ -f "${HOME}/.ssh/id_ed25519" ]]; then
    ok "~/.ssh/id_ed25519 exists"
else
    fail "~/.ssh/id_ed25519 missing — Ansible cannot connect"
fi

if [[ -f "${HOME}/.ssh/id_ed25519.pub" ]]; then
    ok "~/.ssh/id_ed25519.pub exists"
else
    fail "~/.ssh/id_ed25519.pub missing"
fi

# ── 3. SOPS / age key ─────────────────────────────────────────────────────────
hdr "3. SOPS / age"

if [[ -f "${HOME}/.config/sops/age/keys.txt" ]]; then
    ok "Age key exists at ~/.config/sops/age/keys.txt"
else
    fail "Age key missing — SOPS decryption will fail"
fi

if sops -d config/wireguard/keys.sops.yml &>/dev/null; then
    ok "keys.sops.yml decrypts successfully"
else
    fail "keys.sops.yml decryption failed"
fi

if sops -d ansible/group_vars/all.sops.yml &>/dev/null; then
    ok "all.sops.yml decrypts successfully"
else
    fail "all.sops.yml decryption failed"
fi

# ── 4. VBoxManage ─────────────────────────────────────────────────────────────
hdr "4. VBoxManage"

if [[ -n "${VBM}" ]]; then
    ok "VBoxManage found: ${VBM}"
else
    fail "VBoxManage not found — VirtualBox not installed or not on PATH"
fi

# ── 5. VMs registered and state ───────────────────────────────────────────────
hdr "5. VirtualBox VMs"

if [[ -n "${VBM}" ]]; then
    for vm in console target1 target2; do
        STATE=$("${VBM}" showvminfo "${vm}" --machinereadable 2>/dev/null \
            | grep '^VMState=' | sed 's/VMState="\(.*\)"/\1/' | tr -d '\r' || echo "not_found")
        if [[ "${STATE}" == "not_found" ]]; then
            fail "VM '${vm}' not registered in VirtualBox"
        else
            ok "VM '${vm}' registered (state: ${STATE})"
        fi
    done

    # NAT rules on targets
    for vm_port in "target1:2222" "target2:2223"; do
        vm="${vm_port%%:*}"
        port="${vm_port##*:}"
        RULE=$("${VBM}" showvminfo "${vm}" --machinereadable 2>/dev/null \
            | grep "^Forwarding" | grep ",${port}," || true)
        if [[ -n "${RULE}" ]]; then
            ok "NAT rule confirmed on ${vm} (port ${port})"
        else
            warn "NAT rule missing on ${vm} port ${port}"
            echo "      Fix: VBoxManage.exe modifyvm ${vm} --natpf1 \"ssh,tcp,,${port},,22\""
        fi
    done
fi

# ── 6. WSL2 networking ────────────────────────────────────────────────────────
hdr "6. WSL2 networking"

WSLCONFIG="/mnt/c/Users/$(cmd.exe /c echo %USERNAME% 2>/dev/null | tr -d '\r\n')/.wslconfig"
if [[ -f "${WSLCONFIG}" ]] && grep -q "networkingMode=mirrored" "${WSLCONFIG}" 2>/dev/null; then
    ok "WSL2 mirrored networking configured"
else
    warn "WSL2 mirrored networking not confirmed — SSH to VMs via 127.0.0.1 may fail"
    echo "      Fix: add [wsl2] / networkingMode=mirrored to %USERPROFILE%\\.wslconfig"
fi

# ── 7. SSH reachability (running VMs only) ────────────────────────────────────
hdr "7. SSH reachability"

if [[ -n "${VBM}" ]]; then
    for vm_port in "target1:2222" "target2:2223"; do
        vm="${vm_port%%:*}"
        port="${vm_port##*:}"
        STATE=$("${VBM}" showvminfo "${vm}" --machinereadable 2>/dev/null \
            | grep '^VMState=' | sed 's/VMState="\(.*\)"/\1/' | tr -d '\r' || echo "not_found")
        if [[ "${STATE}" == "running" ]]; then
            if ssh -p "${port}" \
                   -o StrictHostKeyChecking=no \
                   -o ConnectTimeout=5 \
                   -o BatchMode=yes \
                   you@127.0.0.1 true 2>/dev/null; then
                ok "SSH to ${vm} (port ${port}) — key auth working"
            else
                warn "SSH to ${vm} (port ${port}) — key auth failed (password auth may still work)"
                echo "      If 'banner exchange' timeout: UFW may be blocking 10.0.2.2 (VBox NAT gateway)"
                echo "      Fix: ensure allowed_ssh_ips in group_vars/vbox.yml includes 10.0.2.2"
                echo "      Then re-run: ansible-playbook site-vbox.yml --start-at-task 'Install UFW' ..."
            fi
        else
            warn "${vm} is not running (state: ${STATE}) — skipping SSH check"
        fi
    done

    # saconsole via LAN
    CONSOLE_IP=$(awk '/saconsole:/{found=1} found && /ansible_host:/{print $2; exit}' \
        ansible/inventory/dev.yml | tr -d '"')
    CONSOLE_STATE=$("${VBM}" showvminfo console --machinereadable 2>/dev/null \
        | grep '^VMState=' | sed 's/VMState="\(.*\)"/\1/' | tr -d '\r' || echo "not_found")
    if [[ "${CONSOLE_STATE}" == "running" ]]; then
        if [[ -n "${CONSOLE_IP}" ]]; then
            if ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 -o BatchMode=yes \
                   you@"${CONSOLE_IP}" true 2>/dev/null; then
                ok "SSH to saconsole (${CONSOLE_IP}) — key auth working"
            else
                warn "SSH to saconsole (${CONSOLE_IP}) — key auth failed"
                echo "      Check: is the operator SSH public key in saconsole's ~/.ssh/authorized_keys?"
            fi
        else
            warn "saconsole ansible_host not found in inventory/dev.yml"
        fi
    else
        warn "saconsole is not running (state: ${CONSOLE_STATE}) — skipping SSH check"
    fi
fi

# ── 8. Ansible ────────────────────────────────────────────────────────────────
hdr "8. Ansible"

if command -v ansible-playbook &>/dev/null; then
    VER=$(ansible --version | head -1)
    ok "Ansible available: ${VER}"
else
    fail "ansible-playbook not found"
fi

if [[ -f "ansible.cfg" ]]; then
    ok "ansible.cfg present"
else
    warn "ansible.cfg missing — sops vars plugin may not load"
fi

if grep -q "community.sops.sops" ansible.cfg 2>/dev/null; then
    ok "ansible.cfg: community.sops.sops vars plugin enabled"
else
    fail "ansible.cfg missing vars_plugins_enabled — SOPS secrets (Telegram token etc) will be undefined"
    echo "      Fix: add to ansible.cfg [defaults] section:"
    echo "        vars_plugins_enabled = host_group_vars,community.sops.sops"
fi

# ── 9. Base OVA ───────────────────────────────────────────────────────────────
hdr "9. Base OVA"

if [[ -f "/mnt/d/VM_images/esacp-base.ova" ]]; then
    SIZE=$(du -h /mnt/d/VM_images/esacp-base.ova | cut -f1)
    ok "esacp-base.ova present (${SIZE})"
else
    fail "esacp-base.ova missing — all VM rebuilds will fail"
    echo "      Rebuild: boot a clean Ubuntu 24.04 Server VM, then:"
    echo "        1. apt install virtualbox-guest-utils"
    echo "        2. Install operator SSH public key into ~/.ssh/authorized_keys"
    echo "        3. VBoxManage export <vm> --output D:\\VM_images\\esacp-base.ova --ovf20"
fi

if [[ -f "/mnt/d/VM_images/target1-base.ova" ]]; then
    warn "Stale target1-base.ova found — it has been superseded by esacp-base.ova"
    echo "      Safe to delete: rm /mnt/d/VM_images/target1-base.ova"
fi

# ── 10. Bridged adapter (saconsole) ───────────────────────────────────────────
hdr "10. Bridged adapter (saconsole)"

if [[ -n "${VBM}" ]]; then
    BRIDGED_ADAPTER="Intel(R) Wi-Fi 6E AX210 160MHz"
    if "${VBM}" list bridgedifs 2>/dev/null | grep -qF "${BRIDGED_ADAPTER}"; then
        ok "Bridged adapter found: ${BRIDGED_ADAPTER}"
        # Check if VBox filter driver is actually bound by probing the console VM's NIC config
        # (or if it's bridged to the right adapter if console is registered)
        CONSOLE_NIC=$("${VBM}" showvminfo console --machinereadable 2>/dev/null \
            | grep "^bridgeadapter1=" | sed 's/bridgeadapter1="\(.*\)"/\1/' | tr -d '\r' || true)
        if [[ -n "${CONSOLE_NIC}" && "${CONSOLE_NIC}" != "${BRIDGED_ADAPTER}" ]]; then
            warn "console VM is bridged to '${CONSOLE_NIC}' — expected '${BRIDGED_ADAPTER}'"
            echo "      Fix: VBoxManage.exe modifyvm console --bridgeadapter1 \"${BRIDGED_ADAPTER}\""
        fi
    else
        fail "Bridged adapter '${BRIDGED_ADAPTER}' not listed — create_console.sh will fail"
        echo "      Fix: ensure the adapter is connected and VirtualBox NDIS6 Bridged"
        echo "           Networking Driver is bound to it:"
        echo "           Windows → Network Connections → right-click adapter → Properties"
        echo "           → tick 'VirtualBox NDIS6 Bridged Networking Driver'"
    fi
fi

# ── Summary ───────────────────────────────────────────────────────────────────

echo ""
echo "═══════════════════════════════════════"
echo "  Passed: ${PASS}   Warnings: ${WARN}   Failed: ${FAIL}"
echo "═══════════════════════════════════════"
echo ""

if [[ ${FAIL} -gt 0 ]]; then
    echo "❌  Fix all failures before starting work."
    exit 1
elif [[ ${WARN} -gt 0 ]]; then
    echo "⚠️   Warnings present — review before proceeding."
    exit 0
else
    echo "✅  Environment clean. Safe to start a new session."
    exit 0
fi
