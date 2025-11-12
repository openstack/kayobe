# Copyright (c) 2021 StackHPC Ltd.
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
import re

from kayobe.plugins.filter import utils


def get_and_validate_interface(context, name, inventory_hostname):
    """Return a validated interface for a network.

    :param context: a Jinja2 Context object.
    :param name: name of the network.
    :param inventory_hostname: Ansible inventory hostname.
    :returns: a validated interface for a network.
    :raises: ansible.errors.AnsibleFilterError
    """
    device = net_interface(context, name, inventory_hostname)
    if not device:
        raise errors.AnsibleFilterError(
            "Network interface for network '%s' on host '%s' not found" %
            (name, inventory_hostname))
    return device


def _get_veth_interface(context, bridge, inventory_hostname):
    """Return a veth link name for a bridge.

    :param context: a Jinja2 Context object.
    :param bridge: name of the bridge interface into which the veth is plugged.
    :param inventory_hostname: Ansible inventory hostname.
    :returns: a veth link name for a bridge.
    """
    prefix = utils.get_hostvar(context, 'network_patch_prefix',
                               inventory_hostname)
    suffix = utils.get_hostvar(context, 'network_patch_suffix_phy',
                               inventory_hostname)

    # interface names can't be longer than 15 characters
    char_limit = 15 - len(prefix) - len(suffix)
    return prefix + bridge[:char_limit] + suffix


def _get_veth_peer(context, bridge, inventory_hostname):
    """Return a veth peer name for a bridge.

    :param context: a Jinja2 Context object.
    :param bridge: name of the bridge interface into which the veth is plugged.
    :param inventory_hostname: Ansible inventory hostname.
    :returns: a veth peer name for a bridge.
    """
    prefix = utils.get_hostvar(context, 'network_patch_prefix',
                               inventory_hostname)
    suffix = utils.get_hostvar(context, 'network_patch_suffix_ovs',
                               inventory_hostname)

    # interface names can't be longer than 15 characters
    char_limit = 15 - len(prefix) - len(suffix)
    return prefix + bridge[:char_limit] + suffix


def get_ovs_veths(context, names, inventory_hostname):
    """Return a list of dicts describing veth pairs to plug into Open vSwitch.

    :param context: a Jinja2 Context object.
    :param names: list of names of networks.
    :param inventory_hostname: Ansible inventory hostname.
    :returns: a list of dicts describing veth pairs. Each dict has keys 'name',
              'peer', 'bridge', and 'mtu'.
    """
    # The following networks need to be plugged into Open vSwitch:
    # * workload provisioning network
    # * workload cleaning network
    # * neutron external networks
    ironic_networks = [
        utils.get_hostvar(context, 'provision_wl_net_name',
                          inventory_hostname),
        utils.get_hostvar(context, 'cleaning_net_name', inventory_hostname),
    ]
    external_networks = utils.get_hostvar(context, 'external_net_names',
                                          inventory_hostname)
    veth_networks = ironic_networks + (external_networks or [])

    # Make a list of all bridge interfaces.
    bridges = net_select_bridges(context, names, inventory_hostname)
    bridge_interfaces = [net_interface(context, bridge, inventory_hostname)
                         for bridge in bridges]

    # Dict mapping bridge interfaces to the MTU of a connected veth pair.
    veth_mtu_map = {}
    for name in veth_networks:
        if name not in names:
            continue
        device = get_and_validate_interface(context, name, inventory_hostname)
        # When these networks are VLANs, we need to use the underlying tagged
        # interface rather than the untagged interface. We therefore strip the
        # .<vlan> suffix of the interface name. We use a union here as a single
        # tagged interface may be shared between these networks.
        vlan = net_vlan(context, name, inventory_hostname)
        if vlan:
            parent_or_device = get_vlan_parent(
                context, name, device, vlan, inventory_hostname)
        else:
            parent_or_device = device
        if parent_or_device in bridge_interfaces:
            # Determine the MTU as the maximum of all subinterface MTUs. Only
            # interfaces with an explicit MTU set will be taken account of. If
            # no interface has an explicit MTU set, then the corresponding veth
            # will not either.
            # Allow for the case where an MTU is not specified.
            mtu = net_mtu(context, name, inventory_hostname)
            veth_mtu_map.setdefault(parent_or_device, mtu)
            if (veth_mtu_map.get(parent_or_device) or 0) < (mtu or 0):
                veth_mtu_map[parent_or_device] = mtu

    return [
        {
            'name': _get_veth_interface(context, bridge, inventory_hostname),
            'peer': _get_veth_peer(context, bridge, inventory_hostname),
            'bridge': bridge,
            'mtu': mtu
        }
        for bridge, mtu in veth_mtu_map.items()
    ]


def get_vlan_parent(context, name, device, vlan, inventory_hostname):
    """Return the parent interface of a VLAN subinterface.

    :param context: a Jinja2 Context object.
    :param name: name of the network.
    :param device: VLAN interface name.
    :param vlan: VLAN ID.
    :param inventory_hostname: Ansible inventory hostname.
    :returns: parent interface name.
    :raises: ansible.errors.AnsibleFilterError
    """
    parent = net_parent(context, name, inventory_hostname)
    if not parent:
        parent = re.sub(r'\.{}$'.format(vlan), '', device)
    return parent


@jinja2.pass_context
def net_attr(context, name, attr, inventory_hostname=None):
    var_name = "%s_%s" % (name, attr)
    return utils.get_hostvar(context, var_name, inventory_hostname)


def _make_attr_filter(attr):
    @jinja2.pass_context
    def func(context, name, inventory_hostname=None):
        return net_attr(context, name, attr, inventory_hostname)
    return func


@jinja2.pass_context
def net_vip_address(context, name, inventory_hostname=None):
    return net_attr(context, name, 'vip_address', inventory_hostname)


@jinja2.pass_context
def net_ip(context, name, inventory_hostname=None):
    ips = net_attr(context, name, 'ips', inventory_hostname)
    if ips:
        if inventory_hostname is None:
            inventory_hostname = utils.get_hostvar(context,
                                                   "inventory_hostname")
        return ips.get(inventory_hostname)


@jinja2.pass_context
def net_interface(context, name, inventory_hostname=None):
    return net_attr(context, name, 'interface', inventory_hostname)


@jinja2.pass_context
def net_no_ip(context, name, inventory_hostname=None):
    return net_attr(context, name, 'no_ip', inventory_hostname)


@jinja2.pass_context
def net_cidr(context, name, inventory_hostname=None):
    return net_attr(context, name, 'cidr', inventory_hostname)


@jinja2.pass_context
def net_mask(context, name, inventory_hostname=None):
    cidr = net_cidr(context, name, inventory_hostname)
    return str(netaddr.IPNetwork(cidr).netmask) if cidr is not None else None


@jinja2.pass_context
def net_parent(context, name, inventory_hostname=None):
    return net_attr(context, name, 'parent', inventory_hostname)


@jinja2.pass_context
def net_prefix(context, name, inventory_hostname=None):
    cidr = net_cidr(context, name, inventory_hostname)
    return str(netaddr.IPNetwork(cidr).prefixlen) if cidr is not None else None


@jinja2.pass_context
def net_gateway(context, name, inventory_hostname=None):
    return net_attr(context, name, 'gateway', inventory_hostname)


@jinja2.pass_context
def net_allocation_pool_start(context, name, inventory_hostname=None):
    return net_attr(context, name, 'allocation_pool_start', inventory_hostname)


@jinja2.pass_context
def net_allocation_pool_end(context, name, inventory_hostname=None):
    return net_attr(context, name, 'allocation_pool_end', inventory_hostname)


@jinja2.pass_context
def net_inspection_allocation_pool_start(context, name,
                                         inventory_hostname=None):
    return net_attr(context, name, 'inspection_allocation_pool_start',
                    inventory_hostname)


@jinja2.pass_context
def net_inspection_allocation_pool_end(context, name, inventory_hostname=None):
    return net_attr(context, name, 'inspection_allocation_pool_end',
                    inventory_hostname)


net_inspection_gateway = _make_attr_filter('inspection_gateway')


@jinja2.pass_context
def net_neutron_allocation_pool_start(context, name, inventory_hostname=None):
    return net_attr(context, name, 'neutron_allocation_pool_start',
                    inventory_hostname)


@jinja2.pass_context
def net_neutron_allocation_pool_end(context, name, inventory_hostname=None):
    return net_attr(context, name, 'neutron_allocation_pool_end',
                    inventory_hostname)


net_neutron_gateway = _make_attr_filter('neutron_gateway')


@jinja2.pass_context
def net_vlan(context, name, inventory_hostname=None):
    return net_attr(context, name, 'vlan', inventory_hostname)


@jinja2.pass_context
def net_mtu(context, name, inventory_hostname=None):
    mtu = net_attr(context, name, 'mtu', inventory_hostname)
    if mtu is not None:
        mtu = int(mtu)
    return mtu


@jinja2.pass_context
def net_macaddress(context, name, inventory_hostname=None):
    return net_attr(context, name, 'macaddress', inventory_hostname)


@jinja2.pass_context
def net_bridge_stp(context, name, inventory_hostname=None):
    """Return the Spanning Tree Protocol (STP) state for a bridge.

    On RL10 if STP is not defined, default it to 'false' to preserve
    compatibility with network scripts. STP is 'true' in NetworkManager by
    default, so we set it to 'false' here.

    :param context: Jinja2 Context object.
    :param name: The name of the network.
    :param inventory_hostname: Ansible inventory hostname.
    :returns: A string "true" or "false" representing the STP state.
    """
    bridge_stp = net_attr(context, name, 'bridge_stp', inventory_hostname)
    os_family = context['ansible_facts']['os_family']
    if bridge_stp is None:
        if os_family == 'RedHat':
            return 'false'
        else:
            return None
    bridge_stp = str(utils.call_bool_filter(context, bridge_stp)).lower()
    return bridge_stp


net_routes = _make_attr_filter('routes')
net_rules = _make_attr_filter('rules')
net_physical_network = _make_attr_filter('physical_network')
net_bootproto = _make_attr_filter('bootproto')
net_defroute = _make_attr_filter('defroute')
net_ethtool_opts = _make_attr_filter('ethtool_opts')
net_zone = _make_attr_filter('zone')


@jinja2.pass_context
def net_libvirt_network_name(context, name, inventory_hostname=None):
    """Return the configured Libvirt name for a network.

    If no Libvirt name is configured, the network's name is returned.
    """
    libvirt_name = net_attr(context, name, 'libvirt_network_name',
                            inventory_hostname)
    return libvirt_name or name


@jinja2.pass_context
def net_bridge_ports(context, name, inventory_hostname=None):
    ports = net_attr(context, name, 'bridge_ports', inventory_hostname)
    if ports and not isinstance(ports, list):
        raise errors.AnsibleFilterError("Bridge ports for network '%s' should"
                                        " be a list", name)
    return ports


net_bond_mode = _make_attr_filter('bond_mode')
net_bond_ad_select = _make_attr_filter('bond_ad_select')
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
        'options',
    }
    for option in optional:
        if option in route:
            route_obj[option] = route[option]
    return route_obj


def _validate_rules(rules):
    """Validate the format of policy-based routing rules.

    :param rules: a list of rules or None.
    :raises: AnsibleFilterError if any rule is invalid.
    """
    for rule in rules or []:
        if not isinstance(rule, str) and not isinstance(rule, dict):
            raise errors.AnsibleFilterError(
                "Routing policy rules must be defined in string or dict "
                "format for CentOS Stream and Rocky Linux")


@jinja2.pass_context
def net_interface_obj(context, name, inventory_hostname=None, names=None):
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
    netmask = net_mask(context, name, inventory_hostname)
    gateway = net_gateway(context, name, inventory_hostname)
    if ip is None:
        ip = ''
        gateway = None
        netmask = None
    vlan = net_vlan(context, name, inventory_hostname)
    mtu = net_mtu(context, name, inventory_hostname)
    macaddress = net_macaddress(context, name, inventory_hostname)

    # NOTE(priteau): do not pass MTU for VLAN interfaces on bridges when it is
    # identical to the parent bridge, to work around a NetworkManager bug.
    if names is not None and net_is_vlan_interface(context, name,
                                                   inventory_hostname):
        # Make a mapping of bridge interfaces and their MTUs
        bridge_mtus = {}
        for bridge in net_select_bridges(context, names, inventory_hostname):
            bridge_interface = net_interface(context, bridge,
                                             inventory_hostname)
            bridge_mtus[bridge_interface] = net_mtu(context, bridge,
                                                    inventory_hostname)

        # Get parent and check for its MTU if it is a bridge
        parent_or_device = get_vlan_parent(
            context, name, device, vlan, inventory_hostname)
        if parent_or_device in bridge_mtus:
            parent_mtu = bridge_mtus[parent_or_device]
            if mtu == parent_mtu:
                mtu = None

    routes = net_routes(context, name, inventory_hostname)
    if routes:
        routes = [_route_obj(route) for route in routes]
    rules = net_rules(context, name, inventory_hostname)
    bootproto = net_bootproto(context, name, inventory_hostname)
    defroute = net_defroute(context, name, inventory_hostname)
    ethtool_opts = net_ethtool_opts(context, name, inventory_hostname)
    zone = net_zone(context, name, inventory_hostname)
    vip_address = net_vip_address(context, name, inventory_hostname)
    allowed_addresses = [vip_address] if vip_address else None
    _validate_rules(rules)
    interface = {
        'device': device,
        'address': ip,
        'netmask': netmask,
        'gateway': gateway,
        'vlan': vlan,
        'mtu': mtu,
        'macaddress': macaddress,
        'route': routes,
        'rules': rules,
        'bootproto': bootproto or 'static',
        'defroute': defroute,
        'ethtool_opts': ethtool_opts,
        'zone': zone,
        'allowed_addresses': allowed_addresses,
        'onboot': 'yes',
    }
    interface = {k: v for k, v in interface.items() if v is not None}
    return interface


@jinja2.pass_context
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
    netmask = net_mask(context, name, inventory_hostname)
    gateway = net_gateway(context, name, inventory_hostname)
    if ip is None:
        ip = ''
        gateway = None
        netmask = None
    vlan = net_vlan(context, name, inventory_hostname)
    mtu = net_mtu(context, name, inventory_hostname)
    ports = net_bridge_ports(context, name, inventory_hostname)
    routes = net_routes(context, name, inventory_hostname)
    if routes:
        routes = [_route_obj(route) for route in routes]
    rules = net_rules(context, name, inventory_hostname)
    bootproto = net_bootproto(context, name, inventory_hostname)
    defroute = net_defroute(context, name, inventory_hostname)
    ethtool_opts = net_ethtool_opts(context, name, inventory_hostname)
    zone = net_zone(context, name, inventory_hostname)
    stp = net_bridge_stp(context, name, inventory_hostname)
    vip_address = net_vip_address(context, name, inventory_hostname)
    allowed_addresses = [vip_address] if vip_address else None
    _validate_rules(rules)
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
        'ethtool_opts': ethtool_opts,
        'zone': zone,
        'allowed_addresses': allowed_addresses,
        'onboot': 'yes',
        'stp': stp,
    }
    interface = {k: v for k, v in interface.items() if v is not None}
    return interface


@jinja2.pass_context
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
    netmask = net_mask(context, name, inventory_hostname)
    gateway = net_gateway(context, name, inventory_hostname)
    if ip is None:
        ip = ''
        gateway = None
        netmask = None
    vlan = net_vlan(context, name, inventory_hostname)
    mtu = net_mtu(context, name, inventory_hostname)
    mode = net_bond_mode(context, name, inventory_hostname)
    ad_select = net_bond_ad_select(context, name, inventory_hostname)
    slaves = net_bond_slaves(context, name, inventory_hostname)
    miimon = net_bond_miimon(context, name, inventory_hostname)
    updelay = net_bond_updelay(context, name, inventory_hostname)
    downdelay = net_bond_downdelay(context, name, inventory_hostname)
    xmit_hash_policy = net_bond_xmit_hash_policy(context, name,
                                                 inventory_hostname)
    lacp_rate = net_bond_lacp_rate(context, name, inventory_hostname)
    routes = net_routes(context, name, inventory_hostname)
    if routes:
        routes = [_route_obj(route) for route in routes]
    rules = net_rules(context, name, inventory_hostname)
    bootproto = net_bootproto(context, name, inventory_hostname)
    defroute = net_defroute(context, name, inventory_hostname)
    ethtool_opts = net_ethtool_opts(context, name, inventory_hostname)
    zone = net_zone(context, name, inventory_hostname)
    vip_address = net_vip_address(context, name, inventory_hostname)
    allowed_addresses = [vip_address] if vip_address else None
    _validate_rules(rules)
    interface = {
        'device': device,
        'address': ip,
        'netmask': netmask,
        'gateway': gateway,
        'vlan': vlan,
        'mtu': mtu,
        'bond_slaves': slaves,
        'bond_mode': mode,
        'bond_ad_select': ad_select,
        'bond_miimon': miimon,
        'bond_updelay': updelay,
        'bond_downdelay': downdelay,
        'bond_xmit_hash_policy': xmit_hash_policy,
        'bond_lacp_rate': lacp_rate,
        'route': routes,
        'rules': rules,
        'bootproto': bootproto or 'static',
        'defroute': defroute,
        'ethtool_opts': ethtool_opts,
        'zone': zone,
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
             utils.get_hostvar(context, 'inventory_hostname',
                               inventory_hostname)))
    if bridge_ports is None and bond_slaves is None:
        return 'ether'
    if bridge_ports is not None:
        return 'bridge'
    if bond_slaves is not None:
        return 'bond'


@jinja2.pass_context
def net_is_ether(context, name, inventory_hostname=None):
    return _net_interface_type(context, name, inventory_hostname) == 'ether'


@jinja2.pass_context
def net_is_bridge(context, name, inventory_hostname=None):
    return _net_interface_type(context, name, inventory_hostname) == 'bridge'


@jinja2.pass_context
def net_is_bond(context, name, inventory_hostname=None):
    return _net_interface_type(context, name, inventory_hostname) == 'bond'


@jinja2.pass_context
def net_is_vlan(context, name, inventory_hostname=None):
    return net_vlan(context, name) is not None


@jinja2.pass_context
def net_is_vlan_interface(context, name, inventory_hostname=None):
    parent = net_parent(context, name, inventory_hostname)
    vlan = net_vlan(context, name, inventory_hostname)
    if parent and vlan:
        return True
    else:
        device = get_and_validate_interface(context, name, inventory_hostname)
        # Use a heuristic to match conventional VLAN names, ending with a
        # period and a numerical extension to an interface name
        return re.match(r"^[a-zA-Z0-9_\-]+\.[1-9][\d]{0,3}$", device)


@jinja2.pass_context
def net_select_ethers(context, names, inventory_hostname=None):
    return [name for name in names
            if net_is_ether(context, name, inventory_hostname)]


@jinja2.pass_context
def net_select_bridges(context, names, inventory_hostname=None):
    return [name for name in names
            if net_is_bridge(context, name, inventory_hostname)]


@jinja2.pass_context
def net_select_bonds(context, names, inventory_hostname=None):
    return [name for name in names
            if net_is_bond(context, name, inventory_hostname)]


@jinja2.pass_context
def net_select_vlans(context, names, inventory_hostname=None):
    return [name for name in names
            if net_is_vlan(context, name, inventory_hostname)]


@jinja2.pass_context
def net_select_vlan_interfaces(context, names, inventory_hostname=None):
    return [name for name in names
            if net_is_vlan_interface(context, name, inventory_hostname)]


@jinja2.pass_context
def net_reject_vlans(context, names, inventory_hostname=None):
    return [name for name in names
            if not net_is_vlan(context, name, inventory_hostname)]


@jinja2.pass_context
def net_configdrive_network_device(context, name, inventory_hostname=None):
    device = net_interface(context, name, inventory_hostname)
    if not device:
        raise errors.AnsibleFilterError(
            "Network interface for network '%s' on host '%s' not found" %
            (name, inventory_hostname))
    ip = net_ip(context, name, inventory_hostname)
    netmask = net_mask(context, name, inventory_hostname)
    gateway = net_gateway(context, name, inventory_hostname)
    bootproto = net_bootproto(context, name, inventory_hostname)
    mtu = net_mtu(context, name, inventory_hostname)
    vlan = net_vlan(context, name, inventory_hostname)
    parent = net_parent(context, name, inventory_hostname)
    if vlan and parent:
        backend = parent
    elif vlan and '.' in device:
        backend = [device.split('.')[0]]
    else:
        backend = None
    interface = {
        'device': device,
        'address': ip,
        'netmask': netmask,
        'gateway': gateway,
        'bootproto': bootproto or 'static',
        'mtu': mtu,
        'backend': backend,
    }
    if backend:
        interface['type'] = 'vlan'
    interface = {k: v for k, v in interface.items() if v is not None}
    return interface


@jinja2.pass_context
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


@jinja2.pass_context
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


@jinja2.pass_context
def net_ovs_veths(context, names, inventory_hostname=None):
    """Return a list of virtual Ethernet pairs for OVS.

    The format is as expected by the veth_interfaces variable of the Kayobe
    veth role.
    """
    veths = get_ovs_veths(context, names, inventory_hostname)
    return [
        {
            'device': veth['name'],
            'bootproto': 'static',
            'bridge': veth['bridge'],
            'mtu': veth['mtu'],
            'peer_device': veth['peer'],
            'peer_bootproto': 'static',
            'peer_mtu': veth['mtu'],
            'onboot': 'yes',
        }
        for veth in veths
    ]


@jinja2.pass_context
def net_physical_interface(context, name, inventory_hostname=None):
    """Return a list of bridge ports, bond slaves or a direct interface name

    Depending on the interface type - return a list of child interfaces or
    (if it's not a bridge/bond) direct interface name.
    """
    if _net_interface_type(context, name, inventory_hostname) == 'bridge':
        return net_bridge_ports(context, name, inventory_hostname)
    elif _net_interface_type(context, name, inventory_hostname) == 'bond':
        return net_bond_slaves(context, name, inventory_hostname)
    else:
        return [net_attr(context, name, 'interface', inventory_hostname)]


def get_filters():
    return {
        'net_attr': net_attr,
        'net_vip_address': net_vip_address,
        'net_fqdn': _make_attr_filter('fqdn'),
        'net_ip': net_ip,
        'net_interface': net_interface,
        'net_parent': net_parent,
        'net_no_ip': net_no_ip,
        'net_cidr': net_cidr,
        'net_mask': net_mask,
        'net_prefix': net_prefix,
        'net_gateway': net_gateway,
        'net_allocation_pool_start': net_allocation_pool_start,
        'net_allocation_pool_end': net_allocation_pool_end,
        'net_inspection_allocation_pool_start': (
            net_inspection_allocation_pool_start),
        'net_inspection_allocation_pool_end': (
            net_inspection_allocation_pool_end),
        'net_inspection_gateway': net_inspection_gateway,
        'net_neutron_allocation_pool_start': net_neutron_allocation_pool_start,
        'net_neutron_allocation_pool_end': net_neutron_allocation_pool_end,
        'net_neutron_gateway': net_neutron_gateway,
        'net_vlan': net_vlan,
        'net_mtu': net_mtu,
        'net_macaddress': net_macaddress,
        'net_routes': net_routes,
        'net_rules': net_rules,
        'net_physical_network': net_physical_network,
        'net_bootproto': net_bootproto,
        'net_defroute': net_defroute,
        'net_ethtool_opts': net_ethtool_opts,
        'net_zone': net_zone,
        'net_bridge_stp': net_bridge_stp,
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
        'net_ovs_veths': net_ovs_veths,
        'net_physical_interface': net_physical_interface,
    }
