#!/bin/bash

set -e

function run_playbook {
    KAYOBE_CONFIG_PATH=${KAYOBE_CONFIG_PATH:-/etc/kayobe}
    # Ansible fails silently if the inventory does not exist.
    test -e ${KAYOBE_CONFIG_PATH}/inventory
    ansible-playbook \
        -i ${KAYOBE_CONFIG_PATH}/inventory \
        -e @${KAYOBE_CONFIG_PATH}/bifrost.yml \
        -e @${KAYOBE_CONFIG_PATH}/dns.yml \
        -e @${KAYOBE_CONFIG_PATH}/globals.yml \
        -e @${KAYOBE_CONFIG_PATH}/kolla.yml \
        -e @${KAYOBE_CONFIG_PATH}/networks.yml \
        -e @${KAYOBE_CONFIG_PATH}/network-allocation.yml \
        -e @${KAYOBE_CONFIG_PATH}/ntp.yml \
        -e @${KAYOBE_CONFIG_PATH}/seed-vm.yml \
        -e @${KAYOBE_CONFIG_PATH}/ssh.yml \
        -e @${KAYOBE_CONFIG_PATH}/swift.yml \
        $@
}

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

function configure_os {
    ansible_user=$(./kayobe-config-dump -e dump_hosts=seed -e dump_var_name=kayobe_ansible_user | head -n -1)
    run_playbook ansible/ip-allocation.yml -l seed
    run_playbook ansible/ssh-known-host.yml -l seed
    run_playbook ansible/kayobe-ansible-user.yml -l seed
    run_playbook ansible/disable-selinux.yml -l seed
    run_playbook ansible/network.yml -l seed
    run_playbook ansible/ntp.yml -l seed
    run_kolla_ansible bootstrap-servers -e ansible_user=${ansible_user}
    run_playbook ansible/kolla-host.yml -l seed
    run_playbook ansible/docker.yml -l seed
}

function deploy_bifrost {
    # Use a pre-built bifrost image in the stackhpc repository.
    # The image was built via kolla-build -t source bifrost-deploy.
    run_playbook ansible/kolla-bifrost.yml
    run_kolla_ansible deploy-bifrost \
      -e kolla_install_type=source \
      -e docker_namespace=stackhpc
}

function deploy_seed_node {
    configure_os
    deploy_bifrost
}

###########################################################
# Main

function main {
    deploy_seed_node
}

main $*
