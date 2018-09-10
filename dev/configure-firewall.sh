#!/bin/bash

set -eu
set -o pipefail

# Simple script to configure the firewall. This should be
# executed from within the VM.

PARENT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

source "${PARENT}/functions"


function main {
    config_init
    configure_iptables
}

main "$@"
