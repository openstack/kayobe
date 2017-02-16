#!/bin/bash

set -e

function run_playbook {
    KAYOBE_CONFIG_PATH=${KAYOBE_CONFIG_PATH:-/etc/kayobe}
    # Ansible fails silently if the inventory does not exist.
    test -e ${KAYOBE_CONFIG_PATH}/inventory
    ansible-playbook \
        -i ${KAYOBE_CONFIG_PATH}/inventory \
        -e @${KAYOBE_CONFIG_PATH}/globals.yml \
        -e @${KAYOBE_CONFIG_PATH}/dns.yml \
        -e @${KAYOBE_CONFIG_PATH}/kolla.yml \
        -e @${KAYOBE_CONFIG_PATH}/networks.yml \
        -e @${KAYOBE_CONFIG_PATH}/network-allocation.yml \
        -e @${KAYOBE_CONFIG_PATH}/ntp.yml \
        -e @${KAYOBE_CONFIG_PATH}/ssh.yml \
        -e @${KAYOBE_CONFIG_PATH}/swift.yml \
        $@
}

function run_kolla_ansible {
    export KOLLA_CONFIG_PATH=${KOLLA_CONFIG_PATH:-/etc/kolla}
    # Ansible fails silently if the inventory does not exist.
    test -e ${KOLLA_CONFIG_PATH}/inventory/overcloud
    KOLLA_VENV=$(pwd)/ansible/kolla-venv
    source ${KOLLA_VENV}/bin/activate
    kolla-ansible \
        --configdir ${KOLLA_CONFIG_PATH} \
        --passwords ${KOLLA_CONFIG_PATH}/passwords.yml \
        -i ${KOLLA_CONFIG_PATH}/inventory/overcloud \
        $@
    deactivate
}

function configure_os {
    run_playbook ansible/ip-allocation.yml -l controllers
    run_playbook ansible/ssh-known-host.yml -l controllers
    run_playbook ansible/disable-selinux.yml -l controllers
    run_playbook ansible/network.yml -l controllers
    run_playbook ansible/ntp.yml -l controllers
    run_kolla_ansible bootstrap-servers -e ansible_user=${USER}
    run_playbook ansible/kolla-host.yml -l controllers
    run_playbook ansible/docker.yml -l controllers
}

function deploy_services {
    run_playbook ansible/kolla-openstack.yml
    run_playbook ansible/swift-setup.yml
    run_kolla_ansible pull
    run_kolla_ansible prechecks
    run_kolla_ansible deploy
    run_kolla_ansible post-deploy
}

function deploy_overcloud {
    configure_os
    deploy_services
}

###########################################################
# Main

function main {
    deploy_overcloud
}

deploy_overcloud
