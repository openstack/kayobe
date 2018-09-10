#!/bin/bash

set -eu
set -o pipefail

# Simple script to configure and deploy a Tenks cluster. This should be
# executed from within the VM. Arguments:
# $1: The path to the Tenks repo.

PARENT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

source "${PARENT}/functions"


function main {
    if [ -z ${1+x} ]; then
        echo "Usage: $0 <tenks repo path>"
        return 1
    fi
    tenks_path="$1"

    config_init
    tenks_deploy "$tenks_path"
}

main "$@"
