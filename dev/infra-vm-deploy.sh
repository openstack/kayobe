#!/bin/bash

set -eu
set -o pipefail

# Simple script to stand up a development environment for infra VMs using
# kayobe.  This should be executed from the hypervisor.

PARENT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

source "${PARENT}/functions"


function main {
    config_init
    infra_vm_deploy
}

main
