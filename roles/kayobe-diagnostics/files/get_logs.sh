#!/bin/bash

# NOTE(mgoddard): This has been adapted from tests/get_logs.sh in Kolla
# Ansible.

# Environment variables:
# $LOG_DIR is the directory to copy logs to.
# $CONFIG_DIR is the directory to copy configuration from.
# $PREVIOUS_CONFIG_DIR is the directory to copy previous configuration, prior
# to an upgrade, from.

set +o errexit

copy_logs() {
    cp -rnL /var/lib/docker/volumes/kolla_logs/_data/* ${LOG_DIR}/kolla/
    if [[ -d ${CONFIG_DIR} ]]; then
        cp -rnL ${CONFIG_DIR}/etc/kayobe/* ${LOG_DIR}/kayobe_configs
        cp -rnL ${CONFIG_DIR}/etc/kolla/* ${LOG_DIR}/kolla_configs
        cp -rnL /etc/kolla/* ${LOG_DIR}/kolla_node_configs
        # Don't save the IPA images.
        rm ${LOG_DIR}/kayobe_configs/kolla/config/ironic/ironic-agent.{kernel,initramfs}
        rm ${LOG_DIR}/kolla_configs/config/ironic/ironic-agent.{kernel,initramfs}
        rm ${LOG_DIR}/kolla_node_configs/ironic-ipxe/ironic-agent.{kernel,initramfs}
        rm ${LOG_DIR}/kolla_node_configs/ironic-pxe/ironic-agent.{kernel,initramfs}
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
    cp -rvnL /var/log/* ${LOG_DIR}/system_logs/


    if [[ -x "$(command -v journalctl)" ]]; then
        journalctl --no-pager > ${LOG_DIR}/system_logs/syslog.txt
        journalctl --no-pager -u docker.service > ${LOG_DIR}/system_logs/docker.log
    else
        cp /var/log/upstart/docker.log ${LOG_DIR}/system_logs/docker.log
    fi

    cp -r /etc/sudoers.d ${LOG_DIR}/system_logs/
    cp /etc/sudoers ${LOG_DIR}/system_logs/sudoers.txt

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

    # docker related information
    (docker info && docker images && docker ps -a) > ${LOG_DIR}/system_logs/docker-info.txt

    for container in $(docker ps -a --format "{{.Names}}"); do
        docker logs --tail all ${container} &> ${LOG_DIR}/docker_logs/${container}.txt
    done

    # Bifrost: grab config files and logs from the container.
    if [[ $(docker ps -q -f name=bifrost_deploy) ]]; then
        for service in dnsmasq ironic-api ironic-conductor ironic-inspector mariadb nginx rabbitmq-server; do
            mkdir -p ${LOG_DIR}/kolla/$service
            docker exec bifrost_deploy \
                systemctl status $service -l -n 10000 > ${LOG_DIR}/kolla/$service/${service}-systemd-status.txt
            docker exec bifrost_deploy \
                journalctl -u $service --no-pager > ${LOG_DIR}/kolla/$service/${service}-journal.txt
        done
        docker exec -it bifrost_deploy \
            journalctl --no-pager > ${LOG_DIR}/kolla/bifrost-journal.log
        for d in dnsmasq.conf ironic ironic-inspector nginx/nginx.conf; do
            docker cp bifrost_deploy:/etc/$d ${LOG_DIR}/kolla_node_configs/bifrost/
        done
        docker cp bifrost_deploy:/var/log/mariadb/mariadb.log ${LOG_DIR}/kolla/mariadb/
    fi

    # IPA build logs
    if [[ -f /opt/kayobe/images/ipa/ipa.stderr ]] || [[ -f /opt/kayobe/images/ipa/ipa.stdout ]]; then
        mkdir -p ${LOG_DIR}/kayobe
        cp /opt/kayobe/images/ipa/ipa.stderr /opt/kayobe/images/ipa/ipa.stdout ${LOG_DIR}/kayobe/
    fi

    # Rename files to .txt; this is so that when displayed via
    # logs.openstack.org clicking results in the browser shows the
    # files, rather than trying to send it to another app or make you
    # download it, etc.
    for f in $(find ${LOG_DIR}/{system_logs,kolla,docker_logs} -name "*.log"); do
        mv $f ${f/.log/.txt}
    done

    chmod -R 777 ${LOG_DIR}
}

copy_logs
