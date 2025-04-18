#!/bin/bash

set -eu
set -o pipefail

# Install kayobe and its dependencies in a virtual environment.

PARENT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

source "${PARENT}/functions"

SERVICES_TO_RESTART=$1

function main {
    echo "Migrating to RabbitMQ quorum queues"

    config_init

    environment_setup

    control_host_bootstrap

    sed -i -e '$aom_enable_queue_manager: True' ${KAYOBE_CONFIG_SOURCE_PATH}/etc/kayobe/kolla/globals.yml
    sed -i -e '$aom_enable_rabbitmq_quorum_queues: True' ${KAYOBE_CONFIG_SOURCE_PATH}/etc/kayobe/kolla/globals.yml
    sed -i -e '$aom_enable_rabbitmq_transient_quorum_queue: True' ${KAYOBE_CONFIG_SOURCE_PATH}/etc/kayobe/kolla/globals.yml
    sed -i -e '$aom_enable_rabbitmq_stream_fanout: True' ${KAYOBE_CONFIG_SOURCE_PATH}/etc/kayobe/kolla/globals.yml

    kayobe overcloud service configuration generate --node-config-dir /etc/kolla --kolla-skip-tags rabbitmq-ha-precheck

    kayobe kolla ansible run "stop --yes-i-really-really-mean-it" -kt $SERVICES_TO_RESTART

    kayobe kolla ansible run rabbitmq-reset-state

    kayobe kolla ansible run deploy -kt $SERVICES_TO_RESTART
}

main
