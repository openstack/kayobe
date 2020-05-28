#!/usr/bin/env python3

# Kayobe overcloud host configure tests.
# Uses py.test and TestInfra.

import ipaddress
import os

import distro
import pytest


def _is_dnf():
    info = distro.linux_distribution()
    return info[0] == 'CentOS Linux' and info[1].startswith('8')


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


def test_network_bridge(host):
    interface = host.interface('br0')
    assert interface.exists
    assert '192.168.36.1' in interface.addresses
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
    slaves = ['dummy5', 'dummy6']
    assert sys_slaves == " ".join(slaves)
    for slave in slaves:
       interface = host.interface(slave)
       assert interface.exists
       assert not interface.addresses


def test_network_bond_vlan(host):
    interface = host.interface('bond0.44')
    assert interface.exists
    assert '192.168.39.1' in interface.addresses
    assert host.file('/sys/class/net/bond0.44/lower_bond0').exists


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


def test_docker_storage_driver_is_devicemapper(host):
    with host.sudo("stack"):
        info = host.check_output("docker info")
    assert "devicemapper" in info


@pytest.mark.parametrize('user', ['kolla', 'stack'])
def test_docker_image_download(host, user):
    with host.sudo(user):
        host.check_output("docker pull alpine")


@pytest.mark.parametrize('user', ['kolla', 'stack'])
def test_docker_container_run(host, user):
    with host.sudo(user):
        host.check_output("docker run --rm alpine /bin/true")


def test_timezone(host):
    status = host.check_output("timedatectl status")
    assert "Pacific/Honolulu" in status


@pytest.mark.parametrize('repo', ["AppStream", "BaseOS", "Extras", "epel",
                                  "epel-modular"])
@pytest.mark.skipif(not _is_dnf(), reason="DNF only supported on CentOS 8")
def test_dnf_local_package_mirrors(host, repo):
    # Depends on SITE_MIRROR_FQDN environment variable.
    assert os.getenv('SITE_MIRROR_FQDN')
    # NOTE(mgoddard): Should not require sudo but some files
    # (/var/cache/dnf/expired_repos.json) can have incorrect permissions.
    # https://bugzilla.redhat.com/show_bug.cgi?id=1636909
    with host.sudo():
        info = host.check_output("dnf repoinfo %s", repo)
    assert os.getenv('SITE_MIRROR_FQDN') in info


@pytest.mark.skipif(not _is_dnf(), reason="DNF only supported on CentOS 8")
def test_dnf_custom_package_repository_is_available(host):
    with host.sudo():
        host.check_output("dnf -y install td-agent")
    assert host.package("td-agent").is_installed


@pytest.mark.skipif(not _is_dnf(), reason="DNF only supported on CentOS 8")
def test_dnf_automatic(host):
    assert host.package("dnf-automatic").is_installed
    assert host.service("dnf-automatic.timer").is_enabled
    assert host.service("dnf-automatic.timer").is_running
