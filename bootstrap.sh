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
        -e @${KAYOBE_CONFIG_PATH}/swift.yml \
        $@
}

function install_ansible {
    if [[ -f /etc/centos-release ]]; then
        sudo yum -y install epel-release
    elif [[ -f /etc/redhat-release ]]; then
        sudo subscription-manager repos --enable=qci-1.0-for-rhel-7-rpms
        if ! yum info epel-release >/dev/null 2>&1 ; then
            sudo yum -y install \
                https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm
        fi
    fi
    sudo yum -y install ansible
}

function install_ansible_roles {
    ansible-galaxy install \
        --roles-path ansible/roles \
        --role-file ansible/requirements.yml
}

function bootstrap {
    run_playbook ansible/bootstrap.yml
}

function install_kolla {
    run_playbook ansible/kolla.yml
}

function main {
    install_ansible
    install_ansible_roles
    bootstrap
    install_kolla
}

main $*
