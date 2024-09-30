#!/bin/bash

set -eu
set -o pipefail

# Install kayobe and its dependencies in a virtual environment.

PARENT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

source "${PARENT}/functions"

function main {
    echo "Upgrading RabbitMQ to version 3.13"

    config_init

    environment_setup

    control_host_bootstrap

    kayobe kolla ansible run "rabbitmq-upgrade 3.12"

    kayobe kolla ansible run "rabbitmq-upgrade 3.13"
}

main
