#!/bin/bash

set -eu
set -o pipefail

# Simple script to upgrade a development environment for an OpenStack
# controller in a Vagrant VM using kayobe.  This should be executed from within
# the VM.

PARENT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

source "${PARENT}/functions"


function main {
    config_init
    # NOTE(wszusmki): Dependencies such as python can change across versions
    install_dependencies
    overcloud_upgrade
}

main
