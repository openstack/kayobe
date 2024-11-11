#!/bin/bash

set -eu
set -o pipefail

# Bounces a given interface on hosts matching the supplied limit.
# Positional arguments:
# arg0: Ansible limit
# arg1: Interface to bounce

PARENT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

source "${PARENT}/functions"


function main {
    config_init
    overcloud_test_bounce_interface controllers "${@}"
}

main "${@:1}"
