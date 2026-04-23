#!/usr/bin/env bash
# Shared bash helpers for stage_6 section scripts. Sourced, not executed.

# _gh_clone CMD — run a git command as ERP_USER with the GitHub deploy-key
# askpass flow configured. Needs env: ERP_USER.
_gh_clone() {
    sudo -u "$ERP_USER" bash -c "
        export DISPLAY=:0
        export SSH_ASKPASS=/home/$ERP_USER/.ssh/gh_askpass.sh
        export SSH_ASKPASS_REQUIRE=force
        export GIT_SSH_COMMAND='ssh -o StrictHostKeyChecking=no'
        $1
    "
}
