#!/bin/bash

set -e

function run_playbook {
    KAYOBE_CONFIG_PATH=${KAYOBE_CONFIG_PATH:-/etc/kayobe}
    # Ansible fails silently if the inventory does not exist.
    test -e ${KAYOBE_CONFIG_PATH}/inventory
    ansible-playbook \
        -i ${KAYOBE_CONFIG_PATH}/inventory \
        -e @${KAYOBE_CONFIG_PATH}/dns.yml \
        -e @${KAYOBE_CONFIG_PATH}/globals.yml \
        -e @${KAYOBE_CONFIG_PATH}/kolla.yml \
        -e @${KAYOBE_CONFIG_PATH}/networks.yml \
        -e @${KAYOBE_CONFIG_PATH}/network-allocation.yml \
        -e @${KAYOBE_CONFIG_PATH}/ntp.yml \
        -e @${KAYOBE_CONFIG_PATH}/seed-vm.yml \
        -e @${KAYOBE_CONFIG_PATH}/swift.yml \
        $@
}

function provision_seed_vm {
    run_playbook ansible/seed-vm.yml
}

###########################################################
# Main

function main {
    provision_seed_vm
}

main $*
