#!/bin/bash

set -eu
set -o pipefail

# Script to run a custom playbook

PARENT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

source "${PARENT}/functions"

function main {
    local playbook_path
    playbook=$1
    args=("${@:2}")
    shift $#
    config_init
    environment_setup
    # Use eval so we can do something like: playbook-run.sh '$KAYOBE_CONFIG_PATH/ansible/test.yml'
    # NOTE: KAYOBE_CONFIG_PATH gets defined by kayobe_init
    playbook_path="$(eval echo $playbook)"
    if ! is_absolute_path "$playbook_path"; then
        # Default to a path relative to repository root
        playbook_path="$KAYOBE_CONFIG_ROOT/$playbook_path"
    fi
    if [ ! -f "$playbook_path" ]; then
        die $LINENO "Playbook path does not exist: $playbook_path"
    fi
    run_kayobe playbook run "$playbook_path" "${args[@]}"
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    if [ "$#" -lt 1 ]; then
        die $LINENO "Error: You must provide a playbook to run." \
            "Usage: playbook-run.sh <playbook>"
    fi
    main "${@:1}"
fi
