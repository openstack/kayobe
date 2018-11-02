#!/bin/bash

# NOTE(mgoddard): This has been adapted from tests/get_logs.sh in Kolla
# Ansible.

# Environment variables:
# $LOG_DIR is the directory to copy logs to.
# $CONFIG_DIR is the directory to copy configuration from.

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
    free  > ${LOG_DIR}/system_logs/free.txt
    parted -l > ${LOG_DIR}/system_logs/parted-l.txt
    mount > ${LOG_DIR}/system_logs/mount.txt
    env > ${LOG_DIR}/system_logs/env.txt
    ip address > ${LOG_DIR}/system_logs/ip-address.txt
    ip route > ${LOG_DIR}/system_logs/ip-route.txt

    if [ `command -v dpkg` ]; then
        dpkg -l > ${LOG_DIR}/system_logs/dpkg-l.txt
    fi
    if [ `command -v rpm` ]; then
        rpm -qa > ${LOG_DIR}/system_logs/rpm-qa.txt
    fi

    # final memory usage and process list
    ps -eo user,pid,ppid,lwp,%cpu,%mem,size,rss,cmd > ${LOG_DIR}/system_logs/ps.txt

    # docker related information
    (docker info && docker images && docker ps -a) > ${LOG_DIR}/system_logs/docker-info.txt

    for container in $(docker ps -a --format "{{.Names}}"); do
        docker logs --tail all ${container} > ${LOG_DIR}/docker_logs/${container}.txt
    done

    # Rename files to .txt; this is so that when displayed via
    # logs.openstack.org clicking results in the browser shows the
    # files, rather than trying to send it to another app or make you
    # download it, etc.
    for f in $(find ${LOG_DIR}/{system_logs,kolla,docker_logs} -name "*.log"); do
        mv $f ${f/.log/.txt}
    done

    chmod -R 777 ${LOG_DIR}
    find ${LOG_DIR}/{system_logs,kolla,docker_logs} -iname '*.txt' -execdir gzip -f -9 {} \+
    find ${LOG_DIR}/{system_logs,kolla,docker_logs} -iname '*.json' -execdir gzip -f -9 {} \+
}

copy_logs
