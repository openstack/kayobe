#!/usr/bin/env python3

# Kayobe overcloud host configure tests.
# Uses py.test and TestInfra.

import ipaddress
import os

import distro
import pytest


def _is_apt():
    info = distro.id()
    return info == 'ubuntu'


def _is_dnf():
    info = distro.id()
    return info in ['centos', 'rocky']


# NOTE: There are OpenDev mirrors only for centos-stream/9-stream and epel/9.
def _is_dnf_mirror():
    info = distro.id()
    version = distro.version()
    return info == 'centos' and version == '9'


def _is_ubuntu_noble():
    name = distro.name()
    version = distro.version()
    return name == 'Ubuntu' and version == '24.04'


def test_network_ethernet(host):
    interface = host.interface('dummy2')
    assert interface.exists
    assert '192.168.34.1' in interface.addresses
    routes = host.check_output('/sbin/ip route show dev dummy2')
    assert '192.168.40.0/24 via 192.168.34.254' in routes


def test_network_ethernet_vlan(host):
    interface = host.interface('dummy2.42')
    assert interface.exists
    assert '192.168.35.1' in interface.addresses
    assert host.file('/sys/class/net/dummy2.42/lower_dummy2').exists
    routes = host.check_output(
        '/sbin/ip route show dev dummy2.42 table kayobe-test-route-table')
    assert '192.168.40.0/24 via 192.168.35.254' in routes
    rules = host.check_output(
        '/sbin/ip rule show table kayobe-test-route-table')
    expected_from = 'from 192.168.35.0/24 lookup kayobe-test-route-table'
    expected_to = 'to 192.168.35.0/24 lookup kayobe-test-route-table'
    assert expected_from in rules
    assert expected_to in rules


def test_network_bridge(host):
    interface = host.interface('br0')
    assert interface.exists
    assert '192.168.36.1' in interface.addresses
    state_file = "/sys/class/net/br0/bridge/stp_state"
    stp_status = host.file(state_file).content_string.strip()
    assert '0' == stp_status
    ports = ['dummy3', 'dummy4']
    sys_ports = host.check_output('ls -1 /sys/class/net/br0/brif')
    assert sys_ports == "\n".join(ports)
    for port in ports:
        interface = host.interface(port)
        assert interface.exists
        v4_addresses = [a for a in interface.addresses
                        if ipaddress.ip_address(a).version == '4']
        assert not v4_addresses


def test_network_bridge_vlan(host):
    interface = host.interface('br0.43')
    assert interface.exists
    assert '192.168.37.1' in interface.addresses
    assert host.file('/sys/class/net/br0.43/lower_br0').exists


def test_network_bond(host):
    interface = host.interface('bond0')
    assert interface.exists
    assert '192.168.38.1' in interface.addresses
    sys_slaves = host.check_output('cat /sys/class/net/bond0/bonding/slaves')
    # Ordering is not guaranteed, so compare sets.
    sys_slaves = set(sys_slaves.split())
    slaves = set(['dummy5', 'dummy6'])
    assert sys_slaves == slaves
    for slave in slaves:
        interface = host.interface(slave)
        assert interface.exists
        assert not interface.addresses


def test_network_bond_vlan(host):
    interface = host.interface('bond0.44')
    assert interface.exists
    assert '192.168.39.1' in interface.addresses
    assert host.file('/sys/class/net/bond0.44/lower_bond0').exists


def test_network_bridge_no_ip(host):
    interface = host.interface('br1')
    assert interface.exists
    assert '192.168.40.1' not in interface.addresses
    state_file = "/sys/class/net/br1/bridge/stp_state"
    stp_status = host.file(state_file).content_string.strip()
    assert '1' == stp_status


@pytest.mark.skipif(not _is_apt(),
                    reason="systemd-networkd VLANs only supported on Ubuntu")
def test_network_systemd_vlan(host):
    interface = host.interface('vlan45')
    assert interface.exists
    assert '192.168.41.1' in interface.addresses


def test_additional_user_account(host):
    user = host.user("kayobe-test-user")
    assert user.name == "kayobe-test-user"
    assert user.group == "kayobe-test-user"
    assert set(user.groups) == {"kayobe-test-user", "stack"}
    assert user.gecos == "Kayobe test user"
    with host.sudo():
        assert user.password == 'kayobe-test-user-password'


def test_software_RAID(host):
    slaves = host.check_output("ls -1 /sys/class/block/md0/slaves/")
    assert slaves == "loop0\nloop1"


def test_luks(host):
    # blkid returns an emptry string without root permissions
    with host.sudo():
        blkid = host.check_output('blkid /dev/md0')
    assert 'TYPE="crypto_LUKS"' in blkid


def test_sysctls(host):
    assert host.sysctl("fs.mount-max") == 99999


def test_cloud_init_is_disabled(host):
    assert host.file("/etc/cloud/cloud-init.disabled").exists


def test_docker_storage_driver_is_overlay2(host):
    with host.sudo("stack"):
        info = host.check_output("docker info")
    assert "overlay2" in info


@pytest.mark.parametrize('user', ['kolla', 'stack'])
def test_docker_image_download(host, user):
    with host.sudo(user):
        host.check_output("docker pull quay.io/podman/hello")


@pytest.mark.parametrize('user', ['kolla', 'stack'])
def test_docker_container_run(host, user):
    with host.sudo(user):
        host.check_output("docker run --rm quay.io/podman/hello")


def test_timezone(host):
    status = host.check_output("timedatectl status")
    assert "Pacific/Honolulu" in status


def test_ntp_alternative_services_disabled(host):
    # Tests that we don't have any conflicting NTP servers running
    # NOTE(wszumski): We always mask services even if they don't exist
    ntpd_service = host.service("ntp")
    assert ntpd_service.is_masked
    assert not ntpd_service.is_running

    timesyncd_service = host.service("systemd-timesyncd")
    assert timesyncd_service.is_masked
    assert not timesyncd_service.is_running


def test_ntp_running(host):
    # Tests that NTP services are enabled and running
    assert host.package("chrony").is_installed
    assert host.service("chronyd").is_enabled
    assert host.service("chronyd").is_running


def test_ntp_non_default_time_server(host):
    # Tests that the NTP pool has been changed from pool.ntp.org to
    # time.cloudflare.com
    if ('centos' in host.system_info.distribution.lower() or
       'rocky' in host.system_info.distribution.lower()):
        chrony_config = host.file("/etc/chrony.conf")
    else:
        # Debian based distributions use the following path
        chrony_config = host.file("/etc/chrony/chrony.conf")
    assert chrony_config.exists
    assert "time.cloudflare.com" in chrony_config.content_string


def test_ntp_clock_synchronized(host):
    # Tests that the clock is synchronized
    status_output = host.check_output("timedatectl status")
    assert "synchronized: yes" in status_output


@pytest.mark.skipif(not _is_apt(), reason="Apt only supported on Ubuntu")
def test_apt_config(host):
    apt_config = host.file("/etc/apt/apt.conf.d/99retries")
    assert apt_config.exists
    assert apt_config.content_string == "Acquire::Retries 1;\n"


@pytest.mark.skipif(not _is_apt(), reason="Apt only supported on Ubuntu")
def test_apt_preferences(host):
    apt_preferences = host.file("/etc/apt/preferences.d/99fakepackage")
    assert apt_preferences.exists
    assert apt_preferences.content_string == ("Package: fake-package\n"
                                              "Pin: origin fake.repo.url\n"
                                              "Pin-Priority: 1\n")


@pytest.mark.skipif(not _is_apt(), reason="Apt only supported on Ubuntu")
def test_apt_custom_package_repository_is_available(host):
    with host.sudo():
        host.check_output("apt -y install fluent-package")
    assert host.package("fluent-package").is_installed


@pytest.mark.skipif(not _is_apt(), reason="Apt only supported on Ubuntu")
def test_apt_auth(host):
    apt_auth = host.file("/etc/apt/auth.conf.d/test.conf")
    assert apt_auth.exists
    with host.sudo():
        auth_lines = apt_auth.content_string.splitlines()
    assert "machine https://apt.example.com" in auth_lines
    assert "login foo" in auth_lines
    assert "password bar" in auth_lines


@pytest.mark.parametrize('repo', ["appstream", "baseos", "extras", "epel"])
@pytest.mark.skipif(not _is_dnf_mirror(),
                    reason="DNF OpenDev mirror only for CentOS Stream 9")
def test_dnf_local_package_mirrors(host, repo):
    # Depends on SITE_MIRROR_FQDN environment variable.
    assert os.getenv('SITE_MIRROR_FQDN')
    # NOTE(mgoddard): Should not require sudo but some files
    # (/var/cache/dnf/expired_repos.json) can have incorrect permissions.
    # https://bugzilla.redhat.com/show_bug.cgi?id=1636909
    with host.sudo():
        info = host.check_output("dnf repoinfo %s", repo)
    assert os.getenv('SITE_MIRROR_FQDN') in info


@pytest.mark.skipif(not _is_dnf(), reason="DNF only supported on CentOS/Rocky")
def test_dnf_custom_package_repository_is_available(host):
    with host.sudo():
        host.check_output("dnf -y install fluent-package")
    assert host.package("fluent-package").is_installed


@pytest.mark.skipif(not _is_dnf(), reason="DNF only supported on CentOS/Rocky")
def test_dnf_automatic(host):
    assert host.package("dnf-automatic").is_installed
    assert host.service("dnf-automatic.timer").is_enabled
    assert host.service("dnf-automatic.timer").is_running


def test_tuned_profile_is_active(host):
    tuned_output = host.check_output("tuned-adm active")
    assert "throughput-performance" in tuned_output


def test_firewalld_running(host):
    assert host.package("firewalld").is_installed
    assert host.service("firewalld.service").is_enabled
    assert host.service("firewalld.service").is_running


def test_firewalld_zones(host):
    # Verify that interfaces are on correct zones.
    expected_zones = {
        'dummy2.42': 'test-zone1',
        'br0': 'test-zone2',
        'br0.43': 'test-zone3',
        'bond0': 'test-zone3',
        'bond0.44': 'public'
    }
    for interface, expected_zone in expected_zones.items():
        with host.sudo():
            zone = host.check_output(
                "firewall-cmd --get-zone-of-interface %s", interface)
            assert zone == expected_zone

            zone = host.check_output(
                "firewall-cmd --permanent --get-zone-of-interface %s",
                interface)
            assert zone == expected_zone


def test_firewalld_rules(host):
    # Verify that expected rules are present.
    expected_info = {
        'test-zone1': [
            '  services: ',
            '  ports: 8080/tcp',
            '  icmp-blocks: ',
        ],
        'test-zone2': [
            '  services: http',
            '  ports: ',
            '  icmp-blocks: ',
        ],
        'test-zone3': [
            '  services: ',
            '  ports: ',
            '  icmp-blocks: echo-request',
        ],
        'public': [
            '  services: dhcpv6-client ssh',
            '  ports: ',
            '  icmp-blocks: ',
        ],
    }

    for zone, expected_lines in expected_info.items():
        with host.sudo():
            info = host.check_output(
                "firewall-cmd --info-zone %s", zone)
            info = info.splitlines()
            perm_info = host.check_output(
                "firewall-cmd --permanent --info-zone %s", zone)
            perm_info = perm_info.splitlines()

        for expected_line in expected_lines:
            assert expected_line in info
            assert expected_line in perm_info


@pytest.mark.skipif(not _is_dnf(),
                    reason="SELinux only supported on CentOS/Rocky")
def test_selinux(host):
    selinux = host.check_output("sestatus")
    selinux = selinux.splitlines()
    # Remove duplicate whitespace characters in output
    selinux = [" ".join(x.split()) for x in selinux]

    assert "SELinux status: enabled" in selinux
    assert "Current mode: permissive" in selinux
    assert "Mode from config file: permissive" in selinux


def test_swap(host):
    swapon = host.check_output("swapon -s")
    swapon = swapon.splitlines()
    assert len(swapon) > 1
    swap_devs = [swap.split()[0] for swap in swapon[1:]]
    assert "/swapfile" in swap_devs
