# Copyright (c) 2017 StackHPC Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from ansible import errors
import jinja2
import netaddr


def _get_hostvar(context, var_name, inventory_hostname=None):
    if inventory_hostname is None:
        namespace = context
    else:
        if inventory_hostname not in context['hostvars']:
            raise errors.AnsibleFilterError(
                "Inventory hostname '%s' not in hostvars" % inventory_hostname)
        namespace = context["hostvars"][inventory_hostname]
    return namespace.get(var_name)


@jinja2.contextfilter
def net_attr(context, name, attr, inventory_hostname=None):
    var_name = "%s_%s" % (name, attr)
    return _get_hostvar(context, var_name, inventory_hostname)


def _make_attr_filter(attr):
    @jinja2.contextfilter
    def func(context, name, inventory_hostname=None):
        return net_attr(context, name, attr, inventory_hostname)
    return func


@jinja2.contextfilter
def net_vip_address(context, name, inventory_hostname=None):
    return net_attr(context, name, 'vip_address', inventory_hostname)


@jinja2.contextfilter
def net_ip(context, name, inventory_hostname=None):
    ips = net_attr(context, name, 'ips', inventory_hostname)
    if ips:
        if inventory_hostname is None:
            inventory_hostname = _get_hostvar(context, "inventory_hostname")
        return ips.get(inventory_hostname)


@jinja2.contextfilter
def net_interface(context, name, inventory_hostname=None):
    return net_attr(context, name, 'interface', inventory_hostname)


@jinja2.contextfilter
def net_cidr(context, name, inventory_hostname=None):
    return net_attr(context, name, 'cidr', inventory_hostname)


@jinja2.contextfilter
def net_mask(context, name, inventory_hostname=None):
    cidr = net_cidr(context, name, inventory_hostname)
    return str(netaddr.IPNetwork(cidr).netmask) if cidr is not None else None


@jinja2.contextfilter
def net_prefix(context, name, inventory_hostname=None):
    cidr = net_cidr(context, name, inventory_hostname)
    return str(netaddr.IPNetwork(cidr).prefixlen) if cidr is not None else None


@jinja2.contextfilter
def net_gateway(context, name, inventory_hostname=None):
    return net_attr(context, name, 'gateway', inventory_hostname)


@jinja2.contextfilter
def net_allocation_pool_start(context, name, inventory_hostname=None):
    return net_attr(context, name, 'allocation_pool_start', inventory_hostname)


@jinja2.contextfilter
def net_allocation_pool_end(context, name, inventory_hostname=None):
    return net_attr(context, name, 'allocation_pool_end', inventory_hostname)


@jinja2.contextfilter
def net_inspection_allocation_pool_start(context, name, inventory_hostname=None):
    return net_attr(context, name, 'inspection_allocation_pool_start', inventory_hostname)


@jinja2.contextfilter
def net_inspection_allocation_pool_end(context, name, inventory_hostname=None):
    return net_attr(context, name, 'inspection_allocation_pool_end', inventory_hostname)


net_inspection_gateway = _make_attr_filter('inspection_gateway')


@jinja2.contextfilter
def net_neutron_allocation_pool_start(context, name, inventory_hostname=None):
    return net_attr(context, name, 'neutron_allocation_pool_start', inventory_hostname)


@jinja2.contextfilter
def net_neutron_allocation_pool_end(context, name, inventory_hostname=None):
    return net_attr(context, name, 'neutron_allocation_pool_end', inventory_hostname)


net_neutron_gateway = _make_attr_filter('neutron_gateway')


@jinja2.contextfilter
def net_vlan(context, name, inventory_hostname=None):
    return net_attr(context, name, 'vlan', inventory_hostname)


@jinja2.contextfilter
def net_mtu(context, name, inventory_hostname=None):
    mtu = net_attr(context, name, 'mtu', inventory_hostname)
    if mtu is not None:
        mtu = int(mtu)
    return mtu


net_routes = _make_attr_filter('routes')
net_rules = _make_attr_filter('rules')
net_physical_network = _make_attr_filter('physical_network')
net_bootproto = _make_attr_filter('bootproto')
net_defroute = _make_attr_filter('defroute')


@jinja2.contextfilter
def net_libvirt_network_name(context, name, inventory_hostname=None):
    """Return the configured Libvirt name for a network.

    If no Libvirt name is configured, the network's name is returned.
    """
    libvirt_name = net_attr(context, name, 'libvirt_network_name',
                            inventory_hostname)
    return libvirt_name or name


@jinja2.contextfilter
def net_bridge_ports(context, name, inventory_hostname=None):
    return net_attr(context, name, 'bridge_ports', inventory_hostname)


net_bond_mode = _make_attr_filter('bond_mode')
net_bond_slaves = _make_attr_filter('bond_slaves')
net_bond_miimon = _make_attr_filter('bond_miimon')
net_bond_updelay = _make_attr_filter('bond_updelay')
net_bond_downdelay = _make_attr_filter('bond_downdelay')
net_bond_xmit_hash_policy = _make_attr_filter('bond_xmit_hash_policy')
net_bond_lacp_rate = _make_attr_filter('bond_lacp_rate')


def _route_obj(route):
    """Return a dict representation of an IP route.

    The returned dict is compatible with the route item of the
    interfaces_ether_interfaces and interfaces_bridge_interfaces variables in
    the MichaelRigart.interfaces role.
    """
    net = netaddr.IPNetwork(route['cidr'])
    route_obj = {
        'network': str(net.network),
        'netmask': str(net.netmask),
    }
    optional = {
        'gateway',
        'table',
    }
    for option in optional:
        if option in route:
            route_obj[option] = route[option]
    return route_obj


@jinja2.contextfilter
def net_interface_obj(context, name, inventory_hostname=None):
    """Return a dict representation of a network interface.

    The returned dict is compatible with the interfaces_ether_interfaces
    variable in the MichaelRigaert.interfaces role.
    """
    device = net_interface(context, name, inventory_hostname)
    if not device:
        raise errors.AnsibleFilterError(
            "Network interface for network '%s' on host '%s' not found" %
            (name, inventory_hostname))
    ip = net_ip(context, name, inventory_hostname)
    if ip is None:
        ip = '0.0.0.0'
    cidr = net_cidr(context, name, inventory_hostname)
    netmask = net_mask(context, name, inventory_hostname)
    gateway = net_gateway(context, name, inventory_hostname)
    vlan = net_vlan(context, name, inventory_hostname)
    mtu = net_mtu(context, name, inventory_hostname)
    routes = net_routes(context, name, inventory_hostname)
    if routes:
        routes = [_route_obj(route) for route in routes]
    rules = net_rules(context, name, inventory_hostname)
    bootproto = net_bootproto(context, name, inventory_hostname)
    defroute = net_defroute(context, name, inventory_hostname)
    vip_address = net_vip_address(context, name, inventory_hostname)
    allowed_addresses = [vip_address] if vip_address else None
    interface = {
        'device': device,
        'address': ip,
        'netmask': netmask,
        'gateway': gateway,
        'vlan': vlan,
        'mtu': mtu,
        'route': routes,
        'rules': rules,
        'bootproto': bootproto or 'static',
        'defroute': defroute,
        'allowed_addresses': allowed_addresses,
        'onboot': 'yes',
    }
    interface = {k: v for k, v in interface.items() if v is not None}
    return interface


@jinja2.contextfilter
def net_bridge_obj(context, name, inventory_hostname=None):
    """Return a dict representation of a network bridge interface.

    The returned dict is compatible with the interfaces_bridge_interfaces
    variable in the MichaelRigaert.interfaces role.
    """
    device = net_interface(context, name, inventory_hostname)
    if not device:
        raise errors.AnsibleFilterError(
            "Network interface for network '%s' on host '%s' not found" %
            (name, inventory_hostname))
    ip = net_ip(context, name, inventory_hostname)
    if ip is None:
        ip = '0.0.0.0'
    cidr = net_cidr(context, name, inventory_hostname)
    netmask = net_mask(context, name, inventory_hostname)
    gateway = net_gateway(context, name, inventory_hostname)
    vlan = net_vlan(context, name, inventory_hostname)
    mtu = net_mtu(context, name, inventory_hostname)
    ports = net_bridge_ports(context, name, inventory_hostname)
    routes = net_routes(context, name, inventory_hostname)
    if routes:
        routes = [_route_obj(route) for route in routes]
    rules = net_rules(context, name, inventory_hostname)
    bootproto = net_bootproto(context, name, inventory_hostname)
    defroute = net_defroute(context, name, inventory_hostname)
    vip_address = net_vip_address(context, name, inventory_hostname)
    allowed_addresses = [vip_address] if vip_address else None
    interface = {
        'device': device,
        'address': ip,
        'netmask': netmask,
        'gateway': gateway,
        'vlan': vlan,
        'mtu': mtu,
        'ports': ports,
        'route': routes,
        'rules': rules,
        'bootproto': bootproto or 'static',
        'defroute': defroute,
        'allowed_addresses': allowed_addresses,
        'onboot': 'yes',
    }
    interface = {k: v for k, v in interface.items() if v is not None}
    return interface


@jinja2.contextfilter
def net_bond_obj(context, name, inventory_hostname=None):
    """Return a dict representation of a network bond interface.

    The returned dict is compatible with the interfaces_bond_interfaces
    variable in the MichaelRigaert.interfaces role.
    """
    device = net_interface(context, name, inventory_hostname)
    if not device:
        raise errors.AnsibleFilterError(
            "Network interface for network '%s' on host '%s' not found" %
            (name, inventory_hostname))
    ip = net_ip(context, name, inventory_hostname)
    if ip is None:
        ip = '0.0.0.0'
    cidr = net_cidr(context, name, inventory_hostname)
    netmask = net_mask(context, name, inventory_hostname)
    gateway = net_gateway(context, name, inventory_hostname)
    vlan = net_vlan(context, name, inventory_hostname)
    mtu = net_mtu(context, name, inventory_hostname)
    mode = net_bond_mode(context, name, inventory_hostname)
    slaves = net_bond_slaves(context, name, inventory_hostname)
    miimon = net_bond_miimon(context, name, inventory_hostname)
    updelay = net_bond_updelay(context, name, inventory_hostname)
    downdelay = net_bond_downdelay(context, name, inventory_hostname)
    xmit_hash_policy = net_bond_xmit_hash_policy(context, name, inventory_hostname)
    lacp_rate = net_bond_lacp_rate(context, name, inventory_hostname)
    routes = net_routes(context, name, inventory_hostname)
    if routes:
        routes = [_route_obj(route) for route in routes]
    rules = net_rules(context, name, inventory_hostname)
    bootproto = net_bootproto(context, name, inventory_hostname)
    defroute = net_defroute(context, name, inventory_hostname)
    vip_address = net_vip_address(context, name, inventory_hostname)
    allowed_addresses = [vip_address] if vip_address else None
    interface = {
        'device': device,
        'address': ip,
        'netmask': netmask,
        'gateway': gateway,
        'vlan': vlan,
        'mtu': mtu,
        'bond_slaves': slaves,
        'bond_mode': mode,
        'bond_miimon': miimon,
        'bond_updelay': updelay,
        'bond_downdelay': downdelay,
        'bond_xmit_hash_policy': xmit_hash_policy,
        'bond_lacp_rate': lacp_rate,
        'route': routes,
        'rules': rules,
        'bootproto': bootproto or 'static',
        'defroute': defroute,
        'allowed_addresses': allowed_addresses,
        'onboot': 'yes',
    }
    interface = {k: v for k, v in interface.items() if v is not None}
    return interface


def _net_interface_type(context, name, inventory_hostname):
    """Return a string describing the network interface type.

    Possible types include 'ether', 'bridge', 'bond'.
    """
    bridge_ports = net_bridge_ports(context, name, inventory_hostname)
    bond_slaves = net_bond_slaves(context, name, inventory_hostname)
    if bridge_ports is not None and bond_slaves is not None:
        raise errors.AnsibleFilterError(
            "Network %s on host %s has both bridge ports and bond slaves "
            "defined" %
            (name,
             _get_hostvar(context, 'inventory_hostname', inventory_hostname)))
    if bridge_ports is None and bond_slaves is None:
        return 'ether'
    if bridge_ports is not None:
        return 'bridge'
    if bond_slaves is not None:
        return 'bond'


@jinja2.contextfilter
def net_is_ether(context, name, inventory_hostname=None):
    return _net_interface_type(context, name, inventory_hostname) == 'ether'


@jinja2.contextfilter
def net_is_bridge(context, name, inventory_hostname=None):
    return _net_interface_type(context, name, inventory_hostname) == 'bridge'


@jinja2.contextfilter
def net_is_bond(context, name, inventory_hostname=None):
    return _net_interface_type(context, name, inventory_hostname) == 'bond'


@jinja2.contextfilter
def net_is_vlan(context, name, inventory_hostname=None):
    return net_vlan(context, name) is not None


@jinja2.contextfilter
def net_select_ethers(context, names):
    return [name for name in names if net_is_ether(context, name)]


@jinja2.contextfilter
def net_select_bridges(context, names):
    return [name for name in names if net_is_bridge(context, name)]


@jinja2.contextfilter
def net_select_bonds(context, names):
    return [name for name in names if net_is_bond(context, name)]


@jinja2.contextfilter
def net_select_vlans(context, names):
    return [name for name in names if net_is_vlan(context, name)]


@jinja2.contextfilter
def net_reject_vlans(context, names):
    return [name for name in names if not net_is_vlan(context, name)]


@jinja2.contextfilter
def net_configdrive_network_device(context, name, inventory_hostname=None):
    device = net_interface(context, name, inventory_hostname)
    if not device:
        raise errors.AnsibleFilterError(
            "Network interface for network '%s' on host '%s' not found" %
            (name, inventory_hostname))
    ip = net_ip(context, name, inventory_hostname)
    cidr = net_cidr(context, name, inventory_hostname)
    netmask = net_mask(context, name, inventory_hostname)
    gateway = net_gateway(context, name, inventory_hostname)
    bootproto = net_bootproto(context, name, inventory_hostname)
    mtu = net_mtu(context, name, inventory_hostname)
    interface = {
        'device': device,
        'address': ip,
        'netmask': netmask,
        'gateway': gateway,
        'bootproto': bootproto or 'static',
        'mtu': mtu,
    }
    interface = {k: v for k, v in interface.items() if v is not None}
    return interface


@jinja2.contextfilter
def net_libvirt_network(context, name, inventory_hostname=None):
    """Return a dict which describes the Libvirt network for a network.

    The Libvirt network is in a form accepted by the libvirt-host role.
    """
    interface = net_interface(context, name, inventory_hostname)
    name = net_libvirt_network_name(context, name, inventory_hostname)
    return {
        "name": name,
        "mode": "bridge",
        "bridge": interface,
    }


@jinja2.contextfilter
def net_libvirt_vm_network(context, name, inventory_hostname=None):
    """Return a dict which describes the Libvirt VM's network for a network.

    The Libvirt network is in a form accepted by the libvirt_vm_interfaces
    variable of the libvirt-vm role.
    """
    libvirt_name = net_libvirt_network_name(context, name, inventory_hostname)
    return {
        "network": libvirt_name,
        "net_name": name,
    }


class FilterModule(object):
    """Networking filters."""

    def filters(self):
        return {
            'net_attr': net_attr,
            'net_vip_address': net_vip_address,
            'net_fqdn': _make_attr_filter('fqdn'),
            'net_ip': net_ip,
            'net_interface': net_interface,
            'net_cidr': net_cidr,
            'net_mask': net_mask,
            'net_prefix': net_prefix,
            'net_gateway': net_gateway,
            'net_allocation_pool_start': net_allocation_pool_start,
            'net_allocation_pool_end': net_allocation_pool_end,
            'net_inspection_allocation_pool_start': net_inspection_allocation_pool_start,
            'net_inspection_allocation_pool_end': net_inspection_allocation_pool_end,
            'net_inspection_gateway': net_inspection_gateway,
            'net_neutron_allocation_pool_start': net_neutron_allocation_pool_start,
            'net_neutron_allocation_pool_end': net_neutron_allocation_pool_end,
            'net_neutron_gateway': net_neutron_gateway,
            'net_vlan': net_vlan,
            'net_mtu': net_mtu,
            'net_routes': net_routes,
            'net_rules': net_rules,
            'net_physical_network': net_physical_network,
            'net_bootproto': net_bootproto,
            'net_defroute': net_defroute,
            'net_interface_obj': net_interface_obj,
            'net_bridge_obj': net_bridge_obj,
            'net_bond_obj': net_bond_obj,
            'net_is_ether': net_is_ether,
            'net_is_bridge': net_is_bridge,
            'net_is_bond': net_is_bond,
            'net_is_vlan': net_is_vlan,
            'net_select_ethers': net_select_ethers,
            'net_select_bridges': net_select_bridges,
            'net_select_bonds': net_select_bonds,
            'net_select_vlans': net_select_vlans,
            'net_reject_vlans': net_reject_vlans,
            'net_configdrive_network_device': net_configdrive_network_device,
            'net_libvirt_network_name': net_libvirt_network_name,
            'net_libvirt_network': net_libvirt_network,
            'net_libvirt_vm_network': net_libvirt_vm_network,
        }
