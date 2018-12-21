#!/bin/bash

set -eu
set -o pipefail

# Install kayobe and its dependencies in a virtual environment.

PARENT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

source "${PARENT}/functions"


function main {
    # Don't require kayobe configuration to exist for installation - it is not
    # required for the legacy manual deployment procedure.
    KAYOBE_CONFIG_REQUIRED=0
    config_init
    install_dependencies
    install_kayobe_dev_venv
}

main
