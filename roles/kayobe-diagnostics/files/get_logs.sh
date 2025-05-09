#!/bin/bash

# NOTE(mgoddard): This has been adapted from tests/get_logs.sh in Kolla
# Ansible.

# Environment variables:
# $LOG_DIR is the directory to copy logs to.
# $CONFIG_DIR is the directory to copy configuration from.
# $PREVIOUS_CONFIG_DIR is the directory to copy previous configuration, prior
# to an upgrade, from.

set +o errexit

copy_container_engine_logs() {
    container_engine=$1

    # container_engine related information
    ($container_engine info && $container_engine images && $container_engine ps -a) > ${LOG_DIR}/system_logs/${container_engine}-info.txt

    for container in $($container_engine ps -a --format "{{.Names}}"); do
        #NOTE(wszumski): Podman does not support --tail all like docker
        $container_engine logs --tail -1 ${container} &> ${LOG_DIR}/${container_engine}_logs/${container}.txt
    done
}

copy_bifrost_logs() {
    container_engine=$1
    for service in dnsmasq ironic ironic-inspector mariadb nginx; do
        mkdir -p ${LOG_DIR}/kolla/$service
        $container_engine exec bifrost_deploy \
            systemctl status $service -l -n 10000 > ${LOG_DIR}/kolla/$service/${service}-systemd-status.txt
        $container_engine exec bifrost_deploy \
            journalctl -u $service --no-pager > ${LOG_DIR}/kolla/$service/${service}-journal.txt
    done
    $container_engine exec -it bifrost_deploy \
        journalctl --no-pager > ${LOG_DIR}/kolla/bifrost-journal.log
    for d in dnsmasq.conf ironic ironic-inspector nginx/nginx.conf; do
        $container_engine cp bifrost_deploy:/etc/$d ${LOG_DIR}/kolla_node_configs/bifrost/
    done
    $container_engine cp bifrost_deploy:/var/log/mariadb/mariadb.log ${LOG_DIR}/kolla/mariadb/
}

copy_logs() {
    cp -rnL /var/log/kolla/* ${LOG_DIR}/kolla/
    if [[ -d ${CONFIG_DIR} ]]; then
        cp -rnL ${CONFIG_DIR}/etc/kayobe/* ${LOG_DIR}/kayobe_configs
        cp -rnL ${CONFIG_DIR}/etc/kolla/* ${LOG_DIR}/kolla_configs
        cp -rnL /etc/kolla/* ${LOG_DIR}/kolla_node_configs
        # Don't save the IPA images.
        rm ${LOG_DIR}/kayobe_configs/kolla/config/ironic/ironic-agent.{kernel,initramfs}
        rm ${LOG_DIR}/kolla_configs/config/ironic/ironic-agent.{kernel,initramfs}
        rm ${LOG_DIR}/kolla_node_configs/ironic-http/ironic-agent.{kernel,initramfs}
        rm ${LOG_DIR}/kolla_node_configs/ironic-tftp/ironic-agent.{kernel,initramfs}
    fi
    if [[ -n ${PREVIOUS_CONFIG_DIR} ]] && [[ -d ${PREVIOUS_CONFIG_DIR} ]]; then
        mkdir -p ${LOG_DIR}/previous_{kayobe,kolla}_configs
        cp -rnL ${PREVIOUS_CONFIG_DIR}/etc/kayobe/* ${LOG_DIR}/previous_kayobe_configs
        cp -rnL ${PREVIOUS_CONFIG_DIR}/etc/kolla/* ${LOG_DIR}/previous_kolla_configs
        # NOTE: we can't save node configs in /etc/kolla for the pervious
        # release since they'll have been overwritten at this point.
        # Don't save the IPA images.
        rm ${LOG_DIR}/previous_kayobe_configs/kolla/config/ironic/ironic-agent.{kernel,initramfs}
        rm ${LOG_DIR}/previous_kolla_configs/config/ironic/ironic-agent.{kernel,initramfs}
    fi

    if [[ -d /opt/kayobe/etc/kolla ]]; then
        cp -rnL /opt/kayobe/etc/kolla/* ${LOG_DIR}/kolla_build_configs/
    fi

    cp -rvnL /var/log/* ${LOG_DIR}/system_logs/

    if [[ -x "$(command -v journalctl)" ]]; then
        journalctl --no-pager > ${LOG_DIR}/system_logs/syslog.txt
        journalctl --no-pager -u docker.service > ${LOG_DIR}/system_logs/docker.log
        journalctl --no-pager -u podman.service > ${LOG_DIR}/system_logs/podman.log
        journalctl --no-pager -u vbmcd.service > ${LOG_DIR}/system_logs/vbmcd.log
        journalctl --no-pager -u NetworkManager.service > ${LOG_DIR}/system_logs/NetworkManager.log
    else
        cp /var/log/upstart/docker.log ${LOG_DIR}/system_logs/docker.log
    fi

    if [[ -d /etc/sysconfig/network-scripts/ ]]; then
        cp -r /etc/sysconfig/network-scripts/ ${LOG_DIR}/system_logs/
    fi

    if [[ -d /etc/NetworkManager/system-connections/ ]]; then
        cp -r /etc/NetworkManager/system-connections/ ${LOG_DIR}/system_logs/
    fi

    if [[ -d /etc/yum.repos.d/ ]]; then
        cp -r /etc/yum.repos.d/ ${LOG_DIR}/system_logs/
    fi

    if [[ -d /etc/apt/sources.list.d/ ]]; then
        cp -r /etc/apt/sources.list.d/ ${LOG_DIR}/system_logs/
    fi

    if [[ -d /etc/systemd/ ]]; then
        cp -rL /etc/systemd/ ${LOG_DIR}/system_logs/
    fi

    df -h > ${LOG_DIR}/system_logs/df.txt
    # Gather disk usage statistics for files and directories larger than 1MB
    du -d 5 -hx / | sort -hr | grep '^[0-9\.]*[MGT]' > ${LOG_DIR}/system_logs/du.txt
    free  > ${LOG_DIR}/system_logs/free.txt
    cat /etc/hosts  > ${LOG_DIR}/system_logs/hosts.txt
    parted -l > ${LOG_DIR}/system_logs/parted-l.txt
    mount > ${LOG_DIR}/system_logs/mount.txt
    env > ${LOG_DIR}/system_logs/env.txt
    ip address > ${LOG_DIR}/system_logs/ip-address.txt
    ip route > ${LOG_DIR}/system_logs/ip-route.txt
    ip route show table all > ${LOG_DIR}/system_logs/ip-route-all-tables.txt
    ip rule list > ${LOG_DIR}/system_logs/ip-rule-list.txt

    iptables-save > ${LOG_DIR}/system_logs/iptables.txt

    if [ `command -v dpkg` ]; then
        dpkg -l > ${LOG_DIR}/system_logs/dpkg-l.txt
    fi
    if [ `command -v rpm` ]; then
        rpm -qa > ${LOG_DIR}/system_logs/rpm-qa.txt
    fi

    # final memory usage and process list
    ps -eo user,pid,ppid,lwp,%cpu,%mem,size,rss,cmd > ${LOG_DIR}/system_logs/ps.txt

    # available entropy
    cat /proc/sys/kernel/random/entropy_avail > ${LOG_DIR}/system_logs/entropy_avail.txt

    copy_container_engine_logs docker
    copy_container_engine_logs podman

    # Bifrost: grab config files and logs from the container.
    if [[ $(docker ps -q -f name=bifrost_deploy) ]]; then
        copy_bifrost_logs docker
    fi

    if [[ $(podman ps -q -f name=bifrost_deploy) ]]; then
        copy_bifrost_logs podman
    fi

    # IPA build logs
    if [[ -f /opt/kayobe/images/ipa/ipa.stderr ]] || [[ -f /opt/kayobe/images/ipa/ipa.stdout ]]; then
        mkdir -p ${LOG_DIR}/kayobe
        cp /opt/kayobe/images/ipa/ipa.stderr /opt/kayobe/images/ipa/ipa.stdout ${LOG_DIR}/kayobe/
    fi

    # Overcloud host image build logs
    if [[ -f /opt/kayobe/images/deployment_image/deployment_image.stderr ]] || [[ -f /opt/kayobe/images/deployment_image/deployment_image.stdout ]]; then
        mkdir -p ${LOG_DIR}/kayobe
        cp /opt/kayobe/images/deployment_image/deployment_image.stderr /opt/kayobe/images/deployment_image/deployment_image.stdout ${LOG_DIR}/kayobe/
    fi

    # Rename files to .txt; this is so that when displayed via
    # logs.openstack.org clicking results in the browser shows the
    # files, rather than trying to send it to another app or make you
    # download it, etc.
    for f in $(find ${LOG_DIR}/{system_logs,kolla,docker_logs,podman_logs} -name "*.log"); do
        mv $f ${f/.log/.txt}
    done

    chmod -R 777 ${LOG_DIR}
}

copy_logs
