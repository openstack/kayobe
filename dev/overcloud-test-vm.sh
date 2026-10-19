#!/bin/bash

set -eu
set -o pipefail

PARENT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

source "${PARENT}/functions"


function main {
    config_init
    overcloud_test vm1 m1.tiny demo-net
    if is_cinder_enabled; then
        # Boot a server from a Cinder volume to test the block storage backend.
        overcloud_test vm2 m1.tiny demo-net true
    fi
}

main
