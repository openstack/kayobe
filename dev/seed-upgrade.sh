#!/bin/bash

set -eu
set -o pipefail

# Simple script to upgrade a development environment for a seed VM using
# kayobe.  This should be executed from the hypervisor.

PARENT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

source "${PARENT}/functions"


function main {
    config_init
    seed_upgrade
}

main
