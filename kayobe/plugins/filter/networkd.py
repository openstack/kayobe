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

"""
This module provides Ansible filters that generate configuration for
systemd-networkd NetDevs, links and networks. The results are compatible with
the stackhpc.linux.systemd_networkd role.

Systemd-networkd uses INI-style configuration files, with the provision for
multiple sections with the same name, and multiple options with the same name
in a given section. This results in a slightly unwieldy data format used by the
role. The top level is a list of dicts with section names as keys. The values
are lists of dicts mapping option names to values.

Example schema (YAML):
- section1:
    - option1: value1
    - option2: value2
- section2
    - option3: value3
"""

import ipaddress

from ansible import errors
import jinja2

from kayobe.plugins.filter import networks
from kayobe.plugins.filter import utils


def _filter_options(config):
    """Filter out None values from a networkd config.

    :param config: List of sections to filter.
    :returns: a filtered list of sections without empty options.
    """
    # Example schema (YAML):
    # - section1:
    #     - option1: value1
    #     - option2:
    # - section2
    #     - option3:
    # We can filter this down to the following:
    # - section1:
    #     - option1: value1
    new_config = []
    for section_dict in config:
        new_section_dict = {}
        for section_name, section in section_dict.items():
            new_section = []
            for option_dict in section:
                new_option_dict = {}
                for option_name, option in option_dict.items():
                    if option is not None:
                        new_option_dict[option_name] = option
                if new_option_dict:
                    new_section.append(new_option_dict)
            if new_section:
                new_section_dict[section_name] = new_section
        if new_section_dict:
            new_config.append(new_section_dict)
    return new_config


def _ms_to_s(n):
    """Convert from milliseconds to seconds."""
    if n is not None:
        n = float(n) / 1000
    return n


def _vlan_netdev(context, name, inventory_hostname):
    """Return a networkd NetDev configuration for a VLAN interface.

    :param context: a Jinja2 Context object.
    :param name: name of the network.
    :param inventory_hostname: Ansible inventory hostname.
    """
    device = networks.net_interface(context, name, inventory_hostname)
    mtu = networks.net_mtu(context, name, inventory_hostname)
    vlan = networks.net_vlan(context, name, inventory_hostname)
    config = [
        {
            'NetDev': [
                {'Name': device},
                {'Kind': 'vlan'},
                {'MTUBytes': mtu},
            ],
        },
        {
            'VLAN': [
                {'Id': vlan},
            ]
        }
    ]
    return _filter_options(config)


def _bridge_netdev(context, name, inventory_hostname):
    """Return a networkd NetDev configuration for a bridge.

    :param context: a Jinja2 Context object.
    :param name: name of the network.
    :param inventory_hostname: Ansible inventory hostname.
    """
    device = networks.net_interface(context, name, inventory_hostname)
    mtu = networks.net_mtu(context, name, inventory_hostname)
    stp = networks.net_bridge_stp(context, name, inventory_hostname)
    config = [
        {
            'NetDev': [
                {'Name': device},
                {'Kind': 'bridge'},
                {'MTUBytes': mtu},
            ]
        }
    ]
    if stp is not None:
        config[0]['Bridge'] = [{'STP': stp}]
    return _filter_options(config)


def _bond_netdev(context, name, inventory_hostname):
    """Return a networkd NetDev configuration for a bond.

    :param context: a Jinja2 Context object.
    :param name: name of the network.
    :param inventory_hostname: Ansible inventory hostname.
    """
    device = networks.net_interface(context, name, inventory_hostname)
    mtu = networks.net_mtu(context, name, inventory_hostname)
    mode = networks.net_bond_mode(context, name, inventory_hostname)
    ad_select = networks.net_bond_ad_select(context, name, inventory_hostname)
    miimon = networks.net_bond_miimon(context, name, inventory_hostname)
    updelay = networks.net_bond_updelay(context, name, inventory_hostname)
    downdelay = networks.net_bond_downdelay(context, name, inventory_hostname)
    xmit_hash_policy = networks.net_bond_xmit_hash_policy(context, name,
                                                          inventory_hostname)
    lacp_rate = networks.net_bond_lacp_rate(context, name, inventory_hostname)
    config = [
        {
            'NetDev': [
                {'Name': device},
                {'Kind': 'bond'},
                {'MTUBytes': mtu},
            ]
        },
        {
            'Bond': [
                {'Mode': mode},
                {'AdSelect': ad_select},
                {'TransmitHashPolicy': xmit_hash_policy},
                {'LACPTransmitRate': lacp_rate},
                {'MIIMonitorSec': _ms_to_s(miimon)},
                {'UpDelaySec': _ms_to_s(updelay)},
                {'DownDelaySec': _ms_to_s(downdelay)},
            ]
        }
    ]
    return _filter_options(config)


def _veth_netdev(context, veth, inventory_hostname):
    """Return a networkd NetDev configuration for a veth pair.

    :param context: a Jinja2 Context object.
    :param veth: a dict describing the virtual Ethernet pair.
    :param inventory_hostname: Ansible inventory hostname.
    """
    interface = veth['name']
    peer = veth['peer']
    config = [
        {
            'NetDev': [
                {'Name': interface},
                {'Kind': 'veth'},
            ],
        },
        {
            'Peer': [
                {'Name': peer},
            ]
        }
    ]
    return _filter_options(config)


def _network_routes(routes, route_tables):
    """Return a list of routes for a networkd network.

    :param routes: a list of route dictionaries.
    :param route_tables: a dict mapping route table names to IDs.
    :returns: a list of routes for a networkd network.
    """
    return [
        {
            'Route': [
                # FIXME(mgoddard): No support for 'options'.
                {'Destination': route['cidr']},
                {'Gateway': route.get('gateway')},
                {'Table': route_tables.get(route.get('table'),
                                           route.get('table'))},
            ]
        }
        for route in routes or []
    ]


def _network_rules(rules, route_tables):
    """Return a list of routing policy rules for a networkd network.

    :param rules: a list of rule dictionaries.
    :param route_tables: a dict mapping route table names to IDs.
    :returns: a list of rules for a networkd network.
    """
    for rule in rules or []:
        if not isinstance(rule, dict):
            raise errors.AnsibleFilterError(
                "Routing policy rules must be defined in dictionary "
                "format for systemd-networkd")
    return [
        {
            'RoutingPolicyRule': [
                {'From': rule.get("from")},
                {'To': rule.get("to")},
                {'Priority': rule.get("priority")},
                {'Table': route_tables.get(rule.get('table'),
                                           rule.get('table'))},
            ]
        }
        for rule in rules or []
    ]


def _network(context, name, inventory_hostname, bridge, bond, vlan_interfaces):
    """Return a networkd network for an interface.

    :param context: a Jinja2 Context object.
    :param name: name of the network.
    :param inventory_hostname: Ansible inventory hostname.
    :param bridge: Name of a bridge into which the interface is plugged, or
                   None.
    :param bond: Name of a bond of which the interface is a member, or None.
    :param vlan_interfaces: List of VLAN subinterfaces of the interface.
    """
    # FIXME(mgoddard): Currently does not support: ethtool_opts, zone,
    # allowed_addresses.
    device = networks.net_interface(context, name, inventory_hostname)
    ip = networks.net_ip(context, name, inventory_hostname)
    cidr = networks.net_cidr(context, name, inventory_hostname)
    gateway = networks.net_gateway(context, name, inventory_hostname)
    if ip is None:
        gateway = None
    else:
        if not cidr:
            raise errors.AnsibleFilterError(
                "No CIDR attribute configured for '%s' network but it has an "
                "IP address" %
                (name))
        ip = "%s/%s" % (ip, ipaddress.ip_network(cidr).prefixlen)

    mtu = networks.net_mtu(context, name, inventory_hostname)
    routes = networks.net_routes(context, name, inventory_hostname)
    rules = networks.net_rules(context, name, inventory_hostname)
    bootproto = networks.net_bootproto(context, name, inventory_hostname)
    defroute = networks.net_defroute(context, name, inventory_hostname)
    if defroute is not None:
        defroute = utils.call_bool_filter(context, defroute)
    config = [
        {
            'Match': [
                {'Name': device},
            ]
        },
        {
            'Network': [
                {'Address': ip},
                {'Gateway': gateway},
                {'DHCP': ('yes' if bootproto and bootproto.lower() == 'dhcp'
                          else None)},
                {'UseGateway': ('false'
                                if defroute is not None and not defroute
                                else None)},
                {'Bridge': bridge},
                {'Bond': bond},
            ] + [
                {'VLAN': vlan_interface}
                for vlan_interface in vlan_interfaces
            ]
        },
        {
            'Link': [
                {'MTUBytes': mtu},
            ]
        },
    ]

    # NOTE(mgoddard): Systemd-networkd does not support named route tables
    # until v248. Until then, translate names to numeric IDs using the
    # network_route_tables variable.
    route_tables = utils.get_hostvar(context, "network_route_tables",
                                     inventory_hostname)
    route_tables = {table["name"]: table["id"] for table in route_tables}
    config += _network_routes(routes, route_tables)
    config += _network_rules(rules, route_tables)

    return _filter_options(config)


def _vlan_parent_network(device, mtu, vlan_interfaces):
    """Return a networkd network configuration for a VLAN parent interface.

    :param device: name of the interface.
    :param mtu: Interface MTU.
    :param vlan_interfaces: List of VLAN subinterfaces of the interface.
    """
    config = [
        {
            'Match': [
                {'Name': device},
            ]
        },
        {
            'Network': [
                {'VLAN': vlan_interface}
                for vlan_interface in vlan_interfaces
            ]
        },
        {
            'Link': [
                {'MTUBytes': mtu},
            ]
        }
    ]
    return _filter_options(config)


def _bridge_port_network(context, name, port, inventory_hostname,
                         vlan_interfaces):
    """Return a networkd network configuration for a bridge port.

    :param context: a Jinja2 Context object.
    :param name: name of the network.
    :param port: name of the bridge port interface.
    :param inventory_hostname: Ansible inventory hostname.
    :param vlan_interfaces: List of VLAN subinterfaces of the interface.
    """
    bridge = networks.get_and_validate_interface(context, name,
                                                 inventory_hostname)
    mtu = networks.net_mtu(context, name, inventory_hostname)
    config = [
        {
            'Match': [
                {'Name': port},
            ]
        },
        {
            'Network': [
                {'Bridge': bridge},
            ] + [
                {'VLAN': vlan_interface}
                for vlan_interface in vlan_interfaces
            ]
        },
        {
            'Link': [
                {'MTUBytes': mtu},
            ]
        }
    ]
    return _filter_options(config)


def _bond_member_network(context, name, member, inventory_hostname,
                         vlan_interfaces):
    """Return a networkd network configuration for a bond member.

    :param context: a Jinja2 Context object.
    :param name: name of the network.
    :param member: name of the bond member interface.
    :param inventory_hostname: Ansible inventory hostname.
    :param vlan_interfaces: List of VLAN subinterfaces of the interface.
    """
    bond = networks.get_and_validate_interface(context, name,
                                               inventory_hostname)
    mtu = networks.net_mtu(context, name, inventory_hostname)
    config = [
        {
            'Match': [
                {'Name': member},
            ]
        },
        {
            'Network': [
                {'Bond': bond},
            ] + [
                {'VLAN': vlan_interface}
                for vlan_interface in vlan_interfaces
            ]
        },
        {
            'Link': [
                {'MTUBytes': mtu},
            ]
        }
    ]
    return _filter_options(config)


def _veth_network(context, veth, inventory_hostname):
    """Return a networkd network configuration for a veth link.

    :param context: a Jinja2 Context object.
    :param veth: a dict describing the virtual Ethernet pair.
    :param inventory_hostname: Ansible inventory hostname.
    """
    interface = veth['name']
    bridge = veth['bridge']
    mtu = veth['mtu']
    config = [
        {
            'Match': [
                {'Name': interface},
            ]
        },
        {
            'Network': [
                {'Bridge': bridge},
            ]
        },
        {
            'Link': [
                {'MTUBytes': mtu},
            ]
        }
    ]
    return _filter_options(config)


def _veth_peer_network(context, veth, inventory_hostname):
    """Return a networkd network configuration for a veth peer.

    :param context: a Jinja2 Context object.
    :param veth: a dict describing the virtual Ethernet pair.
    :param inventory_hostname: Ansible inventory hostname.
    """
    interface = veth['peer']
    mtu = veth['mtu']
    config = [
        {
            'Match': [
                {'Name': interface},
            ]
        },
        {
            'Network': [
                # NOTE(mgoddard): bring the interface up, even without an IP.
                {'ConfigureWithoutCarrier': 'true'},
            ]
        },
        {
            'Link': [
                {'MTUBytes': mtu},
            ]
        }
    ]
    return _filter_options(config)


def _ether_link(context, name, inventory_hostname):
    """Return a networkd link configuration for a ether.

    :param context: a Jinja2 Context object.
    :param name: name of the network.
    :param inventory_hostname: Ansible inventory hostname.
    """
    config = []

    device = networks.net_interface(context, name, inventory_hostname)
    macaddress = networks.net_macaddress(context, name, inventory_hostname)

    if macaddress is not None:
        config = [
            {
                'Match': [
                    {'PermanentMACAddress': macaddress},
                ],
            },
            {
                'Link': [
                    {'Name': device},
                ],
            }
        ]

    return _filter_options(config)


def _add_to_result(result, prefix, device, config):
    """Add configuration for an interface to a filter result.

    :param result: the result dict.
    :param prefix: the systemd-networkd configuration file prefix.
    :param device: the interface being configured.
    :param config: the configuration to add to the result.
    :raises: AnsibleFilterError if the interface already exists in the result.
    """
    key = "%s%s" % (prefix, device)
    # Catch the case where interface configuration is added multiple times.
    # This should not happen.
    if key in result:
        raise errors.AnsibleFilterError(
            "Programming error: duplicate interface configuration for %s: "
            "have %s"
            % (device, result))
    result[key] = config


@jinja2.pass_context
def networkd_netdevs(context, names, inventory_hostname=None):
    """Return a dict representation of networkd NetDev configuration.

    The format is compatible with the systemd_networkd_netdev variable in the
    stackhpc.linux.systemd_networkd role.

    :param context: a Jinja2 Context object.
    :param names: List of names of networks.
    :param inventory_hostname: Ansible inventory hostname.
    :returns: a dict representation of networkd NetDev configuration.
    """
    # Prefix for configuration file names.
    prefix = utils.get_hostvar(context, "networkd_prefix", inventory_hostname)

    result = {}

    # VLANs.
    for name in networks.net_select_vlan_interfaces(context, names,
                                                    inventory_hostname):
        device = networks.get_and_validate_interface(context, name,
                                                     inventory_hostname)
        netdev = _vlan_netdev(context, name, inventory_hostname)
        _add_to_result(result, prefix, device, netdev)

    # Bridges.
    for name in networks.net_select_bridges(context, names,
                                            inventory_hostname):
        device = networks.get_and_validate_interface(context, name,
                                                     inventory_hostname)
        netdev = _bridge_netdev(context, name, inventory_hostname)
        _add_to_result(result, prefix, device, netdev)

    # Bonds.
    for name in networks.net_select_bonds(context, names, inventory_hostname):
        device = networks.get_and_validate_interface(context, name,
                                                     inventory_hostname)
        netdev = _bond_netdev(context, name, inventory_hostname)
        _add_to_result(result, prefix, device, netdev)

    # Virtual Ethernet pairs.
    veths = networks.get_ovs_veths(context, names, inventory_hostname)
    for veth in veths:
        netdev = _veth_netdev(context, veth, inventory_hostname)
        device = veth['name']
        _add_to_result(result, prefix, device, netdev)

    return result


@jinja2.pass_context
def networkd_links(context, names, inventory_hostname=None):
    """Return a dict representation of networkd link configuration.

    The format is compatible with the systemd_networkd_link variable in the
    stackhpc.linux.systemd_networkd role.

    :param context: a Jinja2 Context object.
    :param names: List of names of networks.
    :param inventory_hostname: Ansible inventory hostname.
    :returns: a dict representation of networkd link configuration.
    """
    # Prefix for configuration file names.
    prefix = utils.get_hostvar(context, "networkd_prefix", inventory_hostname)

    result = {}

    # only ethers
    for name in networks.net_select_ethers(context, names, inventory_hostname):
        device = networks.get_and_validate_interface(context, name,
                                                     inventory_hostname)
        ether_link = _ether_link(context, name, inventory_hostname)
        if ether_link:
            _add_to_result(result, prefix, device, ether_link)

    return result


@jinja2.pass_context
def networkd_networks(context, names, inventory_hostname=None):
    """Return a dict representation of networkd network configuration.

    The format is compatible with the systemd_networkd_network variable in the
    stackhpc.linux.systemd_networkd role.

    :param context: a Jinja2 Context object.
    :param names: List of names of networks.
    :param inventory_hostname: Ansible inventory hostname.
    :returns: a dict representation of networkd network configuration.
    """
    # TODO(mgoddard): some attributes are currently not supported for
    # systemd-networkd: rules, route options, ethtool_opts, zone,
    # allowed addresses

    # Build up some useful mappings.
    bridge_port_to_bridge = {}
    bond_member_to_bond = {}
    interface_to_vlans = {}

    # List of all interfaces.
    interfaces = [
        networks.net_interface(context, name, inventory_hostname)
        for name in names
    ]

    # Map bridge ports to bridges.
    for name in networks.net_select_bridges(context, names,
                                            inventory_hostname):
        device = networks.get_and_validate_interface(context, name,
                                                     inventory_hostname)
        for port in networks.net_bridge_ports(context, name,
                                              inventory_hostname):
            bridge_port_to_bridge[port] = device

    # Map bond members to bonds.
    for name in networks.net_select_bonds(context, names, inventory_hostname):
        device = networks.get_and_validate_interface(context, name,
                                                     inventory_hostname)
        for member in networks.net_bond_slaves(context, name,
                                               inventory_hostname):
            bond_member_to_bond[member] = device

    # Map interfaces to lists of VLAN subinterfaces.
    for name in networks.net_select_vlans(context, names, inventory_hostname):
        device = networks.get_and_validate_interface(context, name,
                                                     inventory_hostname)
        vlan = networks.net_vlan(context, name, inventory_hostname)
        mtu = networks.net_mtu(context, name, inventory_hostname)
        parent = networks.get_vlan_parent(
            context, name, device, vlan, inventory_hostname)
        vlan_interfaces = interface_to_vlans.setdefault(parent, [])
        vlan_interfaces.append({"device": device, "mtu": mtu})

    # Prefix for configuration file names.
    prefix = utils.get_hostvar(context, "networkd_prefix", inventory_hostname)

    result = {}

    # Configured networks.
    for name in names:
        device = networks.get_and_validate_interface(context, name,
                                                     inventory_hostname)
        bridge = bridge_port_to_bridge.get(device)
        bond = bond_member_to_bond.get(device)
        vlan_interfaces = interface_to_vlans.get(device, [])
        net = _network(context, name, inventory_hostname, bridge, bond,
                       [vlan["device"] for vlan in vlan_interfaces])
        _add_to_result(result, prefix, device, net)

    # VLAN parent interfaces that are not in configured networks, bridge ports
    # or bond members.
    implied_vlan_parents = (set(interface_to_vlans) -
                            set(interfaces) -
                            set(bridge_port_to_bridge) -
                            set(bond_member_to_bond))
    for device in implied_vlan_parents:
        vlan_interfaces = interface_to_vlans[device]
        vlan_mtus = [vlan["mtu"] for vlan in vlan_interfaces if vlan["mtu"]]
        mtu = max(vlan_mtus) if vlan_mtus else None
        net = _vlan_parent_network(device, mtu,
                                   [vlan["device"]
                                    for vlan in vlan_interfaces])
        _add_to_result(result, prefix, device, net)

    # Bridge ports that are not in configured networks.
    for name in networks.net_select_bridges(context, names,
                                            inventory_hostname):
        device = networks.get_and_validate_interface(context, name,
                                                     inventory_hostname)
        bridge_ports = networks.net_bridge_ports(context, name,
                                                 inventory_hostname)
        for port in set(bridge_ports) - set(interfaces):
            vlan_interfaces = interface_to_vlans.get(port, [])
            net = _bridge_port_network(context, name, port, inventory_hostname,
                                       [vlan["device"]
                                        for vlan in vlan_interfaces])
            _add_to_result(result, prefix, port, net)

    # Bond members that are not in configured networks.
    for name in networks.net_select_bonds(context, names, inventory_hostname):
        device = networks.get_and_validate_interface(context, name,
                                                     inventory_hostname)
        bond_members = networks.net_bond_slaves(context, name,
                                                inventory_hostname)
        for member in set(bond_members) - set(interfaces):
            vlan_interfaces = interface_to_vlans.get(member, [])
            net = _bond_member_network(context, name, member,
                                       inventory_hostname,
                                       [vlan["device"]
                                        for vlan in vlan_interfaces])
            _add_to_result(result, prefix, member, net)

    # Virtual Ethernet pairs for Open vSwitch.
    veths = networks.get_ovs_veths(context, names, inventory_hostname)
    for veth in veths:
        net = _veth_network(context, veth, inventory_hostname)
        device = veth['name']
        _add_to_result(result, prefix, device, net)

        net = _veth_peer_network(context, veth, inventory_hostname)
        device = veth['peer']
        _add_to_result(result, prefix, device, net)

    return result


def get_filters():
    return {
        'networkd_netdevs': networkd_netdevs,
        'networkd_links': networkd_links,
        'networkd_networks': networkd_networks,
    }
