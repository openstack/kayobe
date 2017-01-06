#!/bin/bash

set -e

###########################################################
# Overcloud

function configure_overcloud_network {
    echo "TODO: configure overcloud network"
}

function configure_overcloud_bios_and_raid {
    echo "TODO: configure overcloud BIOS and RAID"
}

function deploy_overcloud_servers {
    # Deploy servers with Bifrost
    kolla-ansible deploy-servers -i /etc/kolla/inventory/seed
}

function configure_overcloud_os {
    #ansible controllers -b -i /etc/kolla/inventory/overcloud -m yum -a 'name=[epel-release, centos-release-openstack-newton]'
    #ansible controllers -b -i /etc/kolla/inventory/overcloud -m yum -a 'name=[python-pip, vim]'

    # Disable SELiunx
    ansible controllers -b -i /etc/kolla/inventory/overcloud -m selinux -a 'state=disabled'
    ansible controllers -b -i /etc/kolla/inventory/overcloud -m command -a 'reboot -f' &

    # Wait for nodes to come back up
    echo "Waiting for overcloud nodes to come back up"
    while true ; do
        ansible controllers -i /etc/kolla/inventory/overcloud -m command -a 'hostname' && break
    done
}

function bootstrap_overcloud_kolla {
    # TODO
    # Bootstrap seed node
    kolla-ansible bootstrap-servers -i /etc/kolla/inventory/overcloud
    ansible controllers -i /etc/kolla/inventory/overcloud -m command -a 'docker ps'
    ansible controllers -b -i /etc/kolla/inventory/overcloud -m service -a 'name=ntpd state=started enabled=yes'
}

function configure_overcloud_docker {
    echo "TODO: configure overcloud docker"
}

function pull_overcloud_images {
    kolla-ansible pull -i /etc/kolla/inventory/overcloud
}

function deploy_overcloud_services {
    kolla-ansible prechecks -i /etc/kolla/inventory/overcloud
    kolla-ansible deploy -i /etc/kolla/inventory/overcloud
    kolla-ansible post-deploy -i /etc/kolla/inventory/overcloud
}

function deploy_overcloud {
    configure_overcloud_network
    configure_overcloud_bios_and_raid
    deploy_overcloud_servers
    configure_overcloud_os
    bootstrap_overcloud_kolla
    configure_overcloud_docker
    pull_overcloud_images
    deploy_overcloud_services
}

###########################################################
# Main

function main {
    deploy_overcloud
}

deploy_overcloud
