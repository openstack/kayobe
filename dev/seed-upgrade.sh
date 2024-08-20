#!/bin/bash

set -eu
set -o pipefail

# Simple script to upgrade a development environment for a seed VM using
# kayobe.  This should be executed from the hypervisor.

PARENT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

source "${PARENT}/functions"


function main {
    config_init
    # NOTE(wszusmki): Dependencies such as python can change across versions
    install_dependencies
    seed_upgrade
}

main
