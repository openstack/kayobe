#!/bin/bash

set -eu
set -o pipefail

# Simple script to configure a development environment as an Ansible control host.

PARENT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

source "${PARENT}/functions"


function main {
    config_init
    ansible_control_host_configure
}

main
