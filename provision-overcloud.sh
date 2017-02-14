#!/bin/bash

set -e

function run_kolla_ansible {
    export KOLLA_CONFIG_PATH=${KOLLA_CONFIG_PATH:-/etc/kolla}
    # Ansible fails silently if the inventory does not exist.
    test -e ${KOLLA_CONFIG_PATH}/inventory/seed
    KOLLA_VENV=$(pwd)/ansible/kolla-venv
    source ${KOLLA_VENV}/bin/activate
    kolla-ansible \
        --configdir ${KOLLA_CONFIG_PATH} \
        --passwords ${KOLLA_CONFIG_PATH}/passwords.yml \
        -i ${KOLLA_CONFIG_PATH}/inventory/seed \
        $@
    deactivate
}

function configure_network {
    echo "TODO: configure overcloud network"
}

function configure_bios_and_raid {
    echo "TODO: configure overcloud BIOS and RAID"
}

function deploy_servers {
    # Deploy servers with Bifrost
    run_kolla_ansible deploy-servers
}

function provision_overcloud {
    configure_network
    configure_bios_and_raid
    deploy_servers
}

###########################################################
# Main

function main {
    provision_overcloud
}

provision_overcloud
