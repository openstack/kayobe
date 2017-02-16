#!/bin/bash

set -e

function configure_kayobe {
    KAYOBE_CONFIG_PATH=${KAYOBE_CONFIG_PATH:-/etc/kayobe}
    sudo yum -y install python-netaddr
    sudo mkdir -p ${KAYOBE_CONFIG_PATH}
    sudo chown ${USER}:${USER} ${KAYOBE_CONFIG_PATH}
    chmod 755 ${KAYOBE_CONFIG_PATH}
    cp -r etc/kayobe/* ${KAYOBE_CONFIG_PATH}
    my_interface=$(ip route get 8.8.8.8 | awk '{ print $5 }')
    my_ip=$(ip route get 8.8.8.8 | awk '{ print $7 }')
    gateway=$(ip route get 8.8.8.8 | awk '{ print $3 }')
    cidr=$(ip a show $my_interface | awk '$1 == "inet" { print $2 }')
    vip=$(python -c "import netaddr; a = netaddr.IPAddress('$my_ip'); print a+2")
    cat >> ${KAYOBE_CONFIG_PATH}/ntp.yml << EOF

#######################################################
# Local config
timezone: GMT
EOF

    cat >> ${KAYOBE_CONFIG_PATH}/networks.yml << EOF

#######################################################
# Local config
provision_oc_net_name: 'the_net'
provision_wl_net_name: 'the_net'
internal_net_name: 'the_net'
external_net_name: 'the_net'
storage_net_name: 'the_net'
storage_mgmt_net_name: 'the_net'

the_net_vip_address: ${vip}
the_net_cidr: ${cidr}
the_net_gateway: ${gateway}
EOF

    cat > ${KAYOBE_CONFIG_PATH}/network-allocation.yml << EOF
---
the_net_ips:
  localhost: ${my_ip}
EOF

    cat > ${KAYOBE_CONFIG_PATH}/inventory/hosts << EOF
[config-mgmt]
# This host acts as the configuration management control host. This must be
# localhost.
localhost ansible_connection=local

[seed]
# This host will provide the Bifrost undercloud.
localhost ansible_host=127.0.0.1

[controllers]
# These hosts will provide the OpenStack overcloud.
EOF

    if [[ -e ~/kayobe-env ]] ; then
        for controller_ip in $(python -c "import json
with open('/home/centos/kayobe-env') as f:
    cfg = json.load(f)
for ctl_ip in cfg['controller_ips']:
    print ctl_ip"); do
            echo "  '$controller_ip': $controller_ip" >> ${KAYOBE_CONFIG_PATH}/network-allocation.yml
            echo $controller_ip >> ${KAYOBE_CONFIG_PATH}/inventory/hosts
        done
    fi
}

function main {
    configure_kayobe
}

main $@
