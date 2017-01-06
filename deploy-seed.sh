#!/bin/bash

set -e

###########################################################
# Seed node

function configure_seed_os {
    sudo yum -y install epel-release
    sudo yum -y install ansible
    sudo yum -y install git vim

    # Generate an SSH key
    if [[ ! -f ~/.ssh/id_rsa ]]; then
        ssh-keygen -N '' -f ~/.ssh/id_rsa
    fi
    ansible localhost -m authorized_key -a "user=$(whoami) key='$(cat ~/.ssh/id_rsa.pub)'"
    ssh-keyscan 127.0.0.1 >> ~/.ssh/known_hosts
    ssh-keyscan localhost >> ~/.ssh/known_hosts

    # Disable SELiunx
    if selinuxenabled && [[ $(getenforce) = 'Enforcing' ]] ; then
        echo "Disabling SELinux and rebooting. Re-run this script"
        ansible localhost -b -m selinux -a 'state=disabled'
        sudo reboot -f
    fi
}

function install_kolla {
    # Install kolla
    sudo yum -y install gcc python-devel python-pip libffi-devel openssl-devel
    #sudo yum -y install centos-release-openstack-newton
    #sudo yum -y install python-openstackclient python-neutronclient

    sudo pip install 'kolla<4.0.0'
    set +e
    sudo yum -y install patch
    sudo patch -u -f /usr/share/kolla/ansible/roles/baremetal/tasks/pre-install.yml << EOF
--- /usr/share/kolla/ansible/roles/baremetal/tasks/pre-install.yml.old  2017-01-06 17:23:12.444746830 +0000
+++ /usr/share/kolla/ansible/roles/baremetal/tasks/pre-install.yml      2017-01-06 17:22:27.864278879 +0000
@@ -28,6 +28,7 @@
           {% for host in groups['all'] %}
           {{ hostvars[host]['ansible_' + hostvars[host]['api_interface']]['ipv4']['address'] }} {{ hostvars[host]['ansible_hostname'] }}
           {% endfor %}
+  become: True
   when: customize_etc_hosts | bool
 
 - name: ensure sudo group is present
@@ -126,7 +127,7 @@
     recurse: yes
     owner: kolla
     group: kolla
-    mode: 755
+    mode: 0755
   become: True
   when: create_kolla_user | bool == True
 
@@ -135,6 +136,6 @@
     path: /etc/kolla
     state: directory
     recurse: yes
-    mode: 666
+    mode: 0666
   become: True
   when: create_kolla_user | bool == False
EOF
    sudo patch -u -f /usr/share/kolla/ansible/roles/ironic/templates/ironic-api.json.j2 << EOF
--- /usr/share/kolla/ansible/roles/ironic/templates/ironic-api.json.j2.old      2017-01-06 13:56:52.881061188 +0000
+++ /usr/share/kolla/ansible/roles/ironic/templates/ironic-api.json.j2  2017-01-06 14:00:21.757338271 +0000
@@ -10,7 +10,7 @@
     ],
     "permissions": [
         {
-            "path": "/var/log/kolla/ironic"
+            "path": "/var/log/kolla/ironic",
             "owner": "ironic:ironic",
             "recurse": true
         }
EOF
    sudo patch -u -f /usr/share/kolla/ansible/roles/ironic/templates/ironic-conductor.json.j2 << EOF
--- /usr/share/kolla/ansible/roles/ironic/templates/ironic-conductor.json.j2.old        2017-01-06 14:28:35.048365453 +0000
+++ /usr/share/kolla/ansible/roles/ironic/templates/ironic-conductor.json.j2    2017-01-06 14:28:44.858467071 +0000
@@ -20,7 +20,7 @@
             "recurse": true
         },
         {
-            "path": "/tftpboot"
+            "path": "/tftpboot",
             "owner": "ironic:ironic",
             "recurse": true
         }
EOF
    set -e
}

function configure_kolla {
    # Configure Kolla
    if [[ -d /etc/kolla ]]; then
        sudo mv /etc/kolla /etc/kolla.old.$(date +%s)
    fi
    sudo mkdir -p /etc/kolla
    sudo chown $(whoami):$(whoami) /etc/kolla
    mkdir -p /etc/kolla/config /etc/kolla/inventory
    cat > /etc/kolla/inventory/seed << EOF
# Simple inventory for bootstrapping Kolla control host.
[baremetal]
seed      ansible_host=127.0.0.1 ansible_user=kolla
EOF

    cat > /etc/kolla/inventory/overcloud << EOF
[controllers]
# These hostname must be resolvable from your deployment host
control01      ansible_host=${CONTROLLER_IP} ansible_user=kolla ansible_become=true

# These initial groups are the only groups required to be modified. The
# additional groups are for more control of the environment.
[control:children]
controllers

# The network nodes are where your l3-agent and loadbalancers will run
# This can be the same as a host in the control group
[network:children]
controllers

[compute:children]
controllers

[monitoring:children]
controllers

[storage:children]
controllers

[baremetal:children]
control
network
compute
storage
monitoring

# You can explicitly specify which hosts run each project by updating the
# groups in the sections below. Common services are grouped together.
[collectd:children]
compute

[grafana:children]
monitoring

[etcd:children]
control

[influxdb:children]
monitoring

[kibana:children]
control

[telegraf:children]
monitoring

[elasticsearch:children]
control

[haproxy:children]
network

[mariadb:children]
control

[rabbitmq:children]
control

[mongodb:children]
control

[keystone:children]
control

[glance:children]
control

[nova:children]
control

[neutron:children]
network

[cinder:children]
control

[cloudkitty:children]
control

[memcached:children]
control

[horizon:children]
control

[swift:children]
control

[barbican:children]
control

[heat:children]
control

[murano:children]
control

[ironic:children]
control

[ceph:children]
control

[magnum:children]
control

[sahara:children]
control

[mistral:children]
control

[manila:children]
control

[ceilometer:children]
control

[aodh:children]
control

[congress:children]
control

[gnocchi:children]
control

# Tempest
[tempest:children]
control

[senlin:children]
control

[vmtp:children]
control

[watcher:children]
control

[rally:children]
control

# Additional control implemented here. These groups allow you to control which
# services run on which hosts at a per-service level.
#
# Word of caution: Some services are required to run on the same host to
# function appropriately. For example, neutron-metadata-agent must run on the
# same host as the l3-agent and (depending on configuration) the dhcp-agent.

# Glance
[glance-api:children]
glance

[glance-registry:children]
glance

# Nova
[nova-api:children]
nova

[nova-conductor:children]
nova

[nova-consoleauth:children]
nova

[nova-novncproxy:children]
nova

[nova-scheduler:children]
nova

[nova-spicehtml5proxy:children]
nova

[nova-compute-ironic:children]
nova

# Neutron
[neutron-server:children]
control

[neutron-dhcp-agent:children]
neutron

[neutron-l3-agent:children]
neutron

[neutron-lbaas-agent:children]
neutron

[neutron-metadata-agent:children]
neutron

[neutron-vpnaas-agent:children]
neutron

# Ceph
[ceph-mon:children]
ceph

[ceph-rgw:children]
ceph

[ceph-osd:children]
storage

# Cinder
[cinder-api:children]
cinder

[cinder-backup:children]
storage

[cinder-scheduler:children]
cinder

[cinder-volume:children]
storage

# Cloudkitty
[cloudkitty-api:children]
cloudkitty

[cloudkitty-processor:children]
cloudkitty

# iSCSI
[iscsid:children]
compute
storage
ironic-conductor

[tgtd:children]
storage

# Manila
[manila-api:children]
manila

[manila-scheduler:children]
manila

[manila-share:children]
network

# Swift
[swift-proxy-server:children]
swift

[swift-account-server:children]
storage

[swift-container-server:children]
storage

[swift-object-server:children]
storage

# Barbican
[barbican-api:children]
barbican

[barbican-keystone-listener:children]
barbican

[barbican-worker:children]
barbican

# Heat
[heat-api:children]
heat

[heat-api-cfn:children]
heat

[heat-engine:children]
heat

# Murano
[murano-api:children]
murano

[murano-engine:children]
murano

# Ironic
[ironic-api:children]
ironic

[ironic-conductor:children]
ironic

[ironic-inspector:children]
ironic

[ironic-pxe:children]
ironic

# Magnum
[magnum-api:children]
magnum

[magnum-conductor:children]
magnum

# Sahara
[sahara-api:children]
sahara

[sahara-engine:children]
sahara

# Mistral
[mistral-api:children]
mistral

[mistral-executor:children]
mistral

[mistral-engine:children]
mistral

# Ceilometer
[ceilometer-api:children]
ceilometer

[ceilometer-central:children]
ceilometer

[ceilometer-notification:children]
ceilometer

[ceilometer-collector:children]
ceilometer

[ceilometer-compute:children]
compute

# Aodh
[aodh-api:children]
aodh

[aodh-evaluator:children]
aodh

[aodh-listener:children]
aodh

[aodh-notifier:children]
aodh

# Congress
[congress-api:children]
congress

[congress-datasource:children]
congress

[congress-policy-engine:children]
congress

# Gnocchi
[gnocchi-api:children]
gnocchi

[gnocchi-statsd:children]
gnocchi

[gnocchi-metricd:children]
gnocchi

# Multipathd
[multipathd:children]
compute

# Watcher
[watcher-api:children]
watcher

[watcher-engine:children]
watcher

[watcher-applier:children]
watcher

# Senlin
[senlin-api:children]
senlin

[senlin-engine:children]
senlin
EOF

    my_ip=$(ip route get 192.168.0.1 | awk '{ print $5 }')
    vip=$(python -c "import netaddr; a = netaddr.IPAddress('$my_ip'); print a+1")
    my_intf=$(ip route get 192.168.0.1 | awk '{ print $3 }')

    cp /usr/share/kolla/etc_examples/kolla/* /etc/kolla
    cat >> /etc/kolla/globals.yml << EOF
##################################################
# Begin overrides
##################################################

# OpenStack distro
kolla_base_distro: "centos"
kolla_install_type: "binary"
openstack_release: "3.0.1"

# Networking
kolla_internal_vip_address: "${vip}"
network_interface: "${my_intf}"

# TLS
#kolla_enable_tls_external: "no"
#kolla_external_fqdn_cert: "{{ node_config_directory }}/certificates/haproxy.pem"

# Services
enable_ironic: "yes"
EOF

    # Generate passwords
    kolla-genpwd

    # Configure Kolla build
    cat > /etc/kolla/template-override.j2 << EOF
{% extends parent_template %}

# Disable troublesome keys
{% set base_yum_repo_keys_override=['http://yum.mariadb.org/RPM-GPG-KEY-MariaDB'] %}
# Disable repos with troublesome keys
{% set base_yum_repo_files_override=['MariaDB.repo'] %}
EOF
    cat > /etc/kolla/kolla-build.conf << EOF
[DEFAULT]
template_override=/etc/kolla/template-override.j2
EOF

    # Configure Bifrost
    mkdir /etc/kolla/config/bifrost
    cat > /etc/kolla/config/bifrost/bifrost.yml << EOF
---
EOF
    cat > /etc/kolla/config/bifrost/dib.yml << EOF
---
dib_os_element: "centos7"
EOF
    cat > /etc/kolla/config/bifrost/servers.yml << EOF
---
EOF
}

function bootstrap_seed_kolla {
    # Bootstrap seed node
    kolla-ansible bootstrap-servers -i /etc/kolla/inventory/seed -e ansible_user=$(whoami)
    ansible seed -i /etc/kolla/inventory/seed -b -m authorized_key -a "user=kolla key='$(cat ~/.ssh/id_rsa.pub)'" -e ansible_user=$(whoami)
    ansible seed -i /etc/kolla/inventory/seed -b -m user -a "name=$(whoami) groups=kolla,docker append=true"
    ansible seed -i /etc/kolla/inventory/seed -m command -a 'docker info'
    # Enable NTPd
    ansible seed -i /etc/kolla/inventory/seed -b -m service -a 'name=ntpd state=started enabled=yes'
}

function configure_seed_docker {
    # TODO
    echo "TODO: configure docker on seed"
}

function deploy_bifrost {
    if true ; then
        # Build Bifrost image
        # FIXME: sudo required because we need to log out/in for docker group
        # membership to take effect.
        sudo kolla-build -t source bifrost-deploy
    else
        # Image on Dockerhub not currently working :(
        docker pull docker.io/kolla/centos-source-bifrost-deploy:3.0.1
    fi

    # Deploy Bifrost
    kolla-ansible deploy-bifrost -i /etc/kolla/inventory/seed -e kolla_install_type=source
}

function deploy_seed_node {
    configure_seed_os
    install_kolla
    configure_kolla
    bootstrap_seed_kolla
    configure_seed_docker
    deploy_bifrost
}

###########################################################
# Main

function main {
    if [[ $# -ne 1 ]]; then
        echo "Usage: $0 <controller IP>"
        exit 1
    fi
    CONTROLLER_IP=$1
    deploy_seed_node
}

main $*
