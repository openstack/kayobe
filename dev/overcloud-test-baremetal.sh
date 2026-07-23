#!/bin/bash

set -eu
set -o pipefail

PARENT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

source "${PARENT}/functions"


function main {
    config_init
    overcloud_test bm1 test-rc provision-net
    # Test Redfish as well
    overcloud_test bm2 test-rc-red provision-net
}

main
