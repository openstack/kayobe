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

import copy
import unittest

from ansible import errors
from ansible.plugins.filter.core import to_bool
import jinja2

from kayobe.plugins.filter import networkd


class BaseNetworkdTest(unittest.TestCase):

    maxDiff = 2000

    variables = {
        # Inventory hostname, used to index IP list.
        "inventory_hostname": "test-host",
        # net1: Ethernet on eth0 with IP 1.2.3.4/24.
        "net1_interface": "eth0",
        "net1_cidr": "1.2.3.0/24",
        "net1_ips": {"test-host": "1.2.3.4"},
        "net1_macaddress": "aa:bb:cc:dd:ee:ff",
        # net2: VLAN on eth0.2 with VLAN 2 on interface eth0.
        "net2_interface": "eth0.2",
        "net2_vlan": 2,
        # net3: bridge on br0 with ports eth0 and eth1.
        "net3_interface": "br0",
        "net3_bridge_ports": ["eth0", "eth1"],
        # net4: bond on bond0 with members eth0 and eth1.
        "net4_interface": "bond0",
        "net4_bond_slaves": ["eth0", "eth1"],
        # net5: VLAN on vlan.5 with VLAN 5 on interface eth0.
        "net5_interface": "vlan.5",
        "net5_parent": "eth0",
        "net5_vlan": 5,
        # net6: VLAN on vlan6 with VLAN 6 on interface eth0.
        "net6_interface": "vlan6",
        "net6_parent": "eth0",
        "net6_vlan": 6,
        # NOTE(priteau): net7 is used in test_veth_on_vlan
        # Prefix for networkd config file names.
        "networkd_prefix": "50-kayobe-",
        # Veth pair patch link prefix and suffix.
        "network_patch_prefix": "p-",
        "network_patch_suffix_ovs": "-ovs",
        "network_patch_suffix_phy": "-phy",
        # List of route tables.
        "network_route_tables": [],
    }

    def setUp(self):
        # Bandit complains about Jinja2 autoescaping without nosec.
        self.env = jinja2.Environment()  # nosec
        self.env.filters['bool'] = to_bool
        self.variables.update({'ansible_facts': {'os_family': 'Debian'}})
        self.context = self._make_context(self.variables)

    def _make_context(self, parent):
        return self.env.context_class(
            self.env, parent=parent, name='dummy', blocks={})

    def _update_context(self, variables):
        updated_vars = copy.deepcopy(self.variables)
        updated_vars.update(variables)
        self.context = self._make_context(updated_vars)


class TestNetworkdNetDevs(BaseNetworkdTest):

    def test_empty(self):
        devs = networkd.networkd_netdevs(self.context, [])
        self.assertEqual({}, devs)

    def test_eth(self):
        devs = networkd.networkd_netdevs(self.context, ["net1"])
        expected = {}
        self.assertEqual(expected, devs)

    def test_eth_untagged_vlan(self):
        # An untagged interface on a network with a VLAN defined should not
        # create a VLAN subinterface.
        self._update_context({"net1_vlan": 42})
        devs = networkd.networkd_netdevs(self.context, ["net1"])
        expected = {}
        self.assertEqual(expected, devs)

    def test_vlan(self):
        devs = networkd.networkd_netdevs(self.context, ["net2"])
        expected = {
            "50-kayobe-eth0.2": [
                {
                    "NetDev": [
                        {"Name": "eth0.2"},
                        {"Kind": "vlan"},
                    ]
                },
                {
                    "VLAN": [
                        {"Id": 2},
                    ]
                },
            ]
        }
        self.assertEqual(expected, devs)

    def test_vlan_all_options(self):
        self._update_context({"net2_mtu": 1400})
        devs = networkd.networkd_netdevs(self.context, ["net2"])
        expected = {
            "50-kayobe-eth0.2": [
                {
                    "NetDev": [
                        {"Name": "eth0.2"},
                        {"Kind": "vlan"},
                        {"MTUBytes": 1400},
                    ]
                },
                {
                    "VLAN": [
                        {"Id": 2},
                    ]
                },
            ]
        }
        self.assertEqual(expected, devs)

    def test_vlan_no_interface(self):
        self._update_context({"net2_interface": None})
        self.assertRaises(errors.AnsibleFilterError,
                          networkd.networkd_netdevs, self.context, ["net2"])

    def test_vlan_with_parent(self):
        devs = networkd.networkd_netdevs(self.context,
                                         ["net1", "net2", "net5", "net6"])
        expected = {
            "50-kayobe-eth0.2": [
                {
                    "NetDev": [
                        {"Name": "eth0.2"},
                        {"Kind": "vlan"},
                    ]
                },
                {
                    "VLAN": [
                        {"Id": 2},
                    ]
                },
            ],
            "50-kayobe-vlan.5": [
                {
                    "NetDev": [
                        {"Name": "vlan.5"},
                        {"Kind": "vlan"},
                    ]
                },
                {
                    "VLAN": [
                        {"Id": 5},
                    ]
                },
            ],
            "50-kayobe-vlan6": [
                {
                    "NetDev": [
                        {"Name": "vlan6"},
                        {"Kind": "vlan"},
                    ]
                },
                {
                    "VLAN": [
                        {"Id": 6},
                    ]
                },
            ]
        }
        self.assertEqual(expected, devs)

    def test_bridge(self):
        devs = networkd.networkd_netdevs(self.context, ["net3"])
        expected = {
            "50-kayobe-br0": [
                {
                    "NetDev": [
                        {"Name": "br0"},
                        {"Kind": "bridge"},
                    ]
                },
            ]
        }
        self.assertEqual(expected, devs)

    def test_bridge_all_options(self):
        self._update_context({"net3_mtu": 1400, "net3_bridge_stp": True})
        devs = networkd.networkd_netdevs(self.context, ["net3"])
        expected = {
            "50-kayobe-br0": [
                {
                    "NetDev": [
                        {"Name": "br0"},
                        {"Kind": "bridge"},
                        {"MTUBytes": 1400},
                    ],
                    "Bridge": [
                        {"STP": "true"},
                    ]
                },
            ]
        }
        self.assertEqual(expected, devs)

    def test_bridge_no_interface(self):
        self._update_context({"net3_interface": None})
        self.assertRaises(errors.AnsibleFilterError,
                          networkd.networkd_netdevs, self.context, ["net3"])

    def test_bridge_untagged_vlan(self):
        # A bridge on a network with a VLAN defined should not create a VLAN
        # subinterface.
        self._update_context({"net3_vlan": 42})
        devs = networkd.networkd_netdevs(self.context, ["net3"])
        expected = {
            "50-kayobe-br0": [
                {
                    "NetDev": [
                        {"Name": "br0"},
                        {"Kind": "bridge"},
                    ]
                },
            ]
        }
        self.assertEqual(expected, devs)

    def test_bond(self):
        devs = networkd.networkd_netdevs(self.context, ["net4"])
        expected = {
            "50-kayobe-bond0": [
                {
                    "NetDev": [
                        {"Name": "bond0"},
                        {"Kind": "bond"},
                    ]
                },
            ]
        }
        self.assertEqual(expected, devs)

    def test_bond_all_options(self):
        self._update_context({
            "net4_mtu": 1400,
            "net4_bond_mode": "802.3ad",
            "net4_bond_miimon": 100,
            "net4_bond_updelay": 200,
            "net4_bond_downdelay": 300,
            "net4_bond_xmit_hash_policy": "layer3+4",
            "net4_bond_lacp_rate": 60,
        })
        devs = networkd.networkd_netdevs(self.context, ["net4"])
        expected = {
            "50-kayobe-bond0": [
                {
                    "NetDev": [
                        {"Name": "bond0"},
                        {"Kind": "bond"},
                        {"MTUBytes": 1400},
                    ]
                },
                {
                    "Bond": [
                        {"Mode": "802.3ad"},
                        {"TransmitHashPolicy": "layer3+4"},
                        {"LACPTransmitRate": 60},
                        {"MIIMonitorSec": 0.1},
                        {"UpDelaySec": 0.2},
                        {"DownDelaySec": 0.3},
                    ]
                },
            ]
        }
        self.assertEqual(expected, devs)

    def test_bond_no_interface(self):
        self._update_context({"net4_interface": None})
        self.assertRaises(errors.AnsibleFilterError,
                          networkd.networkd_netdevs, self.context, ["net4"])

    def test_bond_untagged_vlan(self):
        # A bridge on a network with a VLAN defined should not create a VLAN
        # subinterface.
        self._update_context({"net4_vlan": 42})
        devs = networkd.networkd_netdevs(self.context, ["net4"])
        expected = {
            "50-kayobe-bond0": [
                {
                    "NetDev": [
                        {"Name": "bond0"},
                        {"Kind": "bond"},
                    ]
                },
            ]
        }
        self.assertEqual(expected, devs)

    def test_veth(self):
        self._update_context({"external_net_names": ["net3"]})
        devs = networkd.networkd_netdevs(self.context, ["net3"])
        expected = {
            "50-kayobe-br0": [
                {
                    "NetDev": [
                        {"Name": "br0"},
                        {"Kind": "bridge"},
                    ]
                },
            ],
            "50-kayobe-p-br0-phy": [
                {
                    "NetDev": [
                        {"Name": "p-br0-phy"},
                        {"Kind": "veth"},
                    ]
                },
                {
                    "Peer": [
                        {"Name": "p-br0-ovs"},
                    ]
                },
            ]
        }
        self.assertEqual(expected, devs)

    def test_veth_no_interface(self):
        self._update_context({"external_net_names": ["net3"],
                              "net3_interface": None})
        self.assertRaises(errors.AnsibleFilterError,
                          networkd.networkd_netdevs, self.context, ["net3"])


class TestNetworkdLinks(BaseNetworkdTest):

    def test_empty(self):
        links = networkd.networkd_links(self.context, ['net2'])
        self.assertEqual({}, links)

    def test_link_name(self):
        links = networkd.networkd_links(self.context, ['net1'])
        expected = {
            "50-kayobe-eth0": [
                {
                    "Match": [
                        {"PermanentMACAddress": "aa:bb:cc:dd:ee:ff"}
                    ]
                },
                {
                    "Link": [
                        {"Name": "eth0"},
                    ]
                },
            ]
        }
        self.assertEqual(expected, links)


class TestNetworkdNetworks(BaseNetworkdTest):

    def test_empty(self):
        nets = networkd.networkd_networks(self.context, [])
        self.assertEqual({}, nets)

    def test_eth(self):
        nets = networkd.networkd_networks(self.context, ["net1"])
        expected = {
            "50-kayobe-eth0": [
                {
                    "Match": [
                        {"Name": "eth0"}
                    ]
                },
                {
                    "Network": [
                        {"Address": "1.2.3.4/24"},
                    ]
                },
            ]
        }
        self.assertEqual(expected, nets)

    def test_eth_all_options(self):
        self._update_context({
            "net1_gateway": "1.2.3.1",
            "net1_mtu": 1400,
            "net1_routes": [
                {
                    "cidr": "1.2.4.0/24",
                },
                {
                    "cidr": "1.2.5.0/24",
                    "gateway": "1.2.5.1",
                },
                {
                    "cidr": "1.2.6.0/24",
                    "table": 42,
                },
            ],
            "net1_rules": [
                {
                    "from": "1.2.7.0/24",
                    "table": 43,
                },
                {
                    "to": "1.2.8.0/24",
                    "table": 44,
                    "priority": 1,
                },
            ],
            "net1_bootproto": "dhcp",
            "net1_defroute": 'no',
        })
        nets = networkd.networkd_networks(self.context, ["net1"])
        expected = {
            "50-kayobe-eth0": [
                {
                    "Match": [
                        {"Name": "eth0"}
                    ]
                },
                {
                    "Network": [
                        {"Address": "1.2.3.4/24"},
                        {"Gateway": "1.2.3.1"},
                        {"DHCP": "yes"},
                        {'UseGateway': "false"},
                    ]
                },
                {
                    "Link": [
                        {"MTUBytes": 1400},
                    ]
                },
                {
                    "Route": [
                        {"Destination": "1.2.4.0/24"},
                    ]
                },
                {
                    "Route": [
                        {"Destination": "1.2.5.0/24"},
                        {"Gateway": "1.2.5.1"},
                    ]
                },
                {
                    "Route": [
                        {"Destination": "1.2.6.0/24"},
                        {"Table": 42},
                    ]
                },
                {
                    "RoutingPolicyRule": [
                        {"From": "1.2.7.0/24"},
                        {"Table": 43},
                    ]
                },
                {
                    "RoutingPolicyRule": [
                        {"To": "1.2.8.0/24"},
                        {"Priority": 1},
                        {"Table": 44},
                    ]
                },
            ]
        }
        self.assertEqual(expected, nets)

    def test_eth_no_interface(self):
        self._update_context({"net1_interface": None})
        self.assertRaises(errors.AnsibleFilterError,
                          networkd.networkd_networks, self.context, ["net1"])

    def test_vlan(self):
        nets = networkd.networkd_networks(self.context, ["net2"])
        expected = {
            "50-kayobe-eth0": [
                {
                    "Match": [
                        {"Name": "eth0"}
                    ],
                },
                {
                    "Network": [
                        {"VLAN": "eth0.2"},
                    ]
                },
            ],
            "50-kayobe-eth0.2": [
                {
                    "Match": [
                        {"Name": "eth0.2"}
                    ]
                },
            ]
        }
        self.assertEqual(expected, nets)

    def test_vlan_multiple(self):
        # Test the case with multiple VLANs on an implied parent without MTUs.
        # https://storyboard.openstack.org/#!/story/2009013
        self._update_context({
            "net5_interface": "eth0.3",
            "net5_vlan": 3})
        nets = networkd.networkd_networks(self.context, ["net2", "net5"])
        expected = {
            "50-kayobe-eth0": [
                {
                    "Match": [
                        {"Name": "eth0"}
                    ],
                },
                {
                    "Network": [
                        {"VLAN": "eth0.2"},
                        {"VLAN": "eth0.3"},
                    ]
                },
            ],
            "50-kayobe-eth0.2": [
                {
                    "Match": [
                        {"Name": "eth0.2"}
                    ]
                },
            ],
            "50-kayobe-eth0.3": [
                {
                    "Match": [
                        {"Name": "eth0.3"}
                    ]
                },
            ]
        }
        self.assertEqual(expected, nets)

    def test_vlan_with_parent(self):
        nets = networkd.networkd_networks(self.context,
                                          ["net1", "net2", "net5", "net6"])
        expected = {
            "50-kayobe-eth0": [
                {
                    "Match": [
                        {"Name": "eth0"}
                    ]
                },
                {
                    "Network": [
                        {"Address": "1.2.3.4/24"},
                        {"VLAN": "eth0.2"},
                        {"VLAN": "vlan.5"},
                        {"VLAN": "vlan6"},
                    ]
                },
            ],
            "50-kayobe-eth0.2": [
                {
                    "Match": [
                        {"Name": "eth0.2"}
                    ]
                },
            ],
            "50-kayobe-vlan.5": [
                {
                    "Match": [
                        {"Name": "vlan.5"}
                    ]
                },
            ],
            "50-kayobe-vlan6": [
                {
                    "Match": [
                        {"Name": "vlan6"}
                    ]
                },
            ]
        }
        self.assertEqual(expected, nets)

    def test_vlan_no_interface(self):
        self._update_context({"net2_interface": None})
        self.assertRaises(errors.AnsibleFilterError,
                          networkd.networkd_networks, self.context, ["net2"])

    def test_bridge(self):
        nets = networkd.networkd_networks(self.context, ["net3"])
        expected = {
            "50-kayobe-br0": [
                {
                    "Match": [
                        {"Name": "br0"}
                    ]
                },
            ],
            "50-kayobe-eth0": [
                {
                    "Match": [
                        {"Name": "eth0"}
                    ]
                },
                {
                    "Network": [
                        {"Bridge": "br0"},
                    ]
                },
            ],
            "50-kayobe-eth1": [
                {
                    "Match": [
                        {"Name": "eth1"}
                    ]
                },
                {
                    "Network": [
                        {"Bridge": "br0"},
                    ]
                },
            ]
        }
        self.assertEqual(expected, nets)

    def test_bridge_with_bridge_port_net(self):
        # Test the case where a bridge port interface is a Kayobe network
        # (here, eth0 is net1).
        self._update_context({
            "net1_mtu": 1400,
            "net1_ips": None,
        })
        nets = networkd.networkd_networks(self.context, ["net1", "net3"])
        expected = {
            "50-kayobe-br0": [
                {
                    "Match": [
                        {"Name": "br0"}
                    ]
                },
            ],
            "50-kayobe-eth0": [
                {
                    "Match": [
                        {"Name": "eth0"}
                    ]
                },
                {
                    "Network": [
                        {"Bridge": "br0"},
                    ]
                },
                {
                    "Link": [
                        {"MTUBytes": 1400},
                    ]
                },
            ],
            "50-kayobe-eth1": [
                {
                    "Match": [
                        {"Name": "eth1"}
                    ]
                },
                {
                    "Network": [
                        {"Bridge": "br0"},
                    ]
                },
            ]
        }
        self.assertEqual(expected, nets)

    def test_bridge_with_bridge_port_vlan(self):
        # Test the case where one of the bridge ports has a VLAN subinterface.
        self._update_context({
            "net2_interface": "eth1.2",
        })
        nets = networkd.networkd_networks(self.context, ["net2", "net3"])
        expected = {
            "50-kayobe-br0": [
                {
                    "Match": [
                        {"Name": "br0"}
                    ]
                },
            ],
            "50-kayobe-eth0": [
                {
                    "Match": [
                        {"Name": "eth0"}
                    ]
                },
                {
                    "Network": [
                        {"Bridge": "br0"},
                    ]
                },
            ],
            "50-kayobe-eth1": [
                {
                    "Match": [
                        {"Name": "eth1"}
                    ]
                },
                {
                    "Network": [
                        {"Bridge": "br0"},
                        {"VLAN": "eth1.2"}
                    ]
                },
            ],
            "50-kayobe-eth1.2": [
                {
                    "Match": [
                        {"Name": "eth1.2"}
                    ]
                },
            ],
        }
        self.assertEqual(expected, nets)

    def test_bridge_with_bridge_port_vlan_net(self):
        # Test the case where one of the bridge ports has a VLAN subinterface,
        # and is also a Kayobe network (here eth0 is net1).
        self._update_context({
            "net1_ips": None,
        })
        nets = networkd.networkd_networks(self.context,
                                          ["net1", "net2", "net3"])
        expected = {
            "50-kayobe-br0": [
                {
                    "Match": [
                        {"Name": "br0"}
                    ]
                },
            ],
            "50-kayobe-eth0": [
                {
                    "Match": [
                        {"Name": "eth0"}
                    ]
                },
                {
                    "Network": [
                        {"Bridge": "br0"},
                        {"VLAN": "eth0.2"}
                    ]
                },
            ],
            "50-kayobe-eth0.2": [
                {
                    "Match": [
                        {"Name": "eth0.2"}
                    ]
                },
            ],
            "50-kayobe-eth1": [
                {
                    "Match": [
                        {"Name": "eth1"}
                    ]
                },
                {
                    "Network": [
                        {"Bridge": "br0"},
                    ]
                },
            ]
        }
        self.assertEqual(expected, nets)

    def test_bridge_no_interface(self):
        self._update_context({"net3_interface": None})
        self.assertRaises(errors.AnsibleFilterError,
                          networkd.networkd_networks, self.context, ["net3"])

    def test_bond(self):
        nets = networkd.networkd_networks(self.context, ["net4"])
        expected = {
            "50-kayobe-bond0": [
                {
                    "Match": [
                        {"Name": "bond0"}
                    ]
                },
            ],
            "50-kayobe-eth0": [
                {
                    "Match": [
                        {"Name": "eth0"}
                    ]
                },
                {
                    "Network": [
                        {"Bond": "bond0"},
                    ]
                },
            ],
            "50-kayobe-eth1": [
                {
                    "Match": [
                        {"Name": "eth1"}
                    ]
                },
                {
                    "Network": [
                        {"Bond": "bond0"},
                    ]
                },
            ]
        }
        self.assertEqual(expected, nets)

    def test_bond_with_bond_member_net(self):
        # Test the case where a bond member interface is a Kayobe network
        # (here, eth0 is net1).
        self._update_context({
            "net1_mtu": 1400,
            "net1_ips": None,
        })
        nets = networkd.networkd_networks(self.context, ["net1", "net4"])
        expected = {
            "50-kayobe-bond0": [
                {
                    "Match": [
                        {"Name": "bond0"}
                    ]
                },
            ],
            "50-kayobe-eth0": [
                {
                    "Match": [
                        {"Name": "eth0"}
                    ]
                },
                {
                    "Network": [
                        {"Bond": "bond0"},
                    ]
                },
                {
                    "Link": [
                        {"MTUBytes": 1400},
                    ]
                },
            ],
            "50-kayobe-eth1": [
                {
                    "Match": [
                        {"Name": "eth1"}
                    ]
                },
                {
                    "Network": [
                        {"Bond": "bond0"},
                    ]
                },
            ]
        }
        self.assertEqual(expected, nets)

    def test_bond_with_bond_member_vlan(self):
        # Test the case where one of the bond members has a VLAN subinterface.
        self._update_context({
            "net2_interface": "eth1.2",
        })
        nets = networkd.networkd_networks(self.context, ["net2", "net4"])
        expected = {
            "50-kayobe-bond0": [
                {
                    "Match": [
                        {"Name": "bond0"}
                    ]
                },
            ],
            "50-kayobe-eth0": [
                {
                    "Match": [
                        {"Name": "eth0"}
                    ]
                },
                {
                    "Network": [
                        {"Bond": "bond0"},
                    ]
                },
            ],
            "50-kayobe-eth1": [
                {
                    "Match": [
                        {"Name": "eth1"}
                    ]
                },
                {
                    "Network": [
                        {"Bond": "bond0"},
                        {"VLAN": "eth1.2"},
                    ]
                },
            ],
            "50-kayobe-eth1.2": [
                {
                    "Match": [
                        {"Name": "eth1.2"}
                    ]
                },
            ],
        }
        self.assertEqual(expected, nets)

    def test_bond_with_bond_member_vlan_net(self):
        # Test the case where one of the bond members has a VLAN subinterface,
        # and is also a Kayobe network (here eth0 is net1).
        self._update_context({
            "net1_ips": None,
        })
        nets = networkd.networkd_networks(self.context,
                                          ["net1", "net2", "net4"])
        expected = {
            "50-kayobe-bond0": [
                {
                    "Match": [
                        {"Name": "bond0"}
                    ]
                },
            ],
            "50-kayobe-eth0": [
                {
                    "Match": [
                        {"Name": "eth0"}
                    ]
                },
                {
                    "Network": [
                        {"Bond": "bond0"},
                        {"VLAN": "eth0.2"},
                    ]
                },
            ],
            "50-kayobe-eth0.2": [
                {
                    "Match": [
                        {"Name": "eth0.2"}
                    ]
                },
            ],
            "50-kayobe-eth1": [
                {
                    "Match": [
                        {"Name": "eth1"}
                    ]
                },
                {
                    "Network": [
                        {"Bond": "bond0"},
                    ]
                },
            ]
        }
        self.assertEqual(expected, nets)

    def test_bond_no_interface(self):
        self._update_context({"net4_interface": None})
        self.assertRaises(errors.AnsibleFilterError,
                          networkd.networkd_networks, self.context, ["net4"])

    def test_veth(self):
        self._update_context({"external_net_names": ["net3"],
                              "net3_bridge_ports": []})
        nets = networkd.networkd_networks(self.context, ["net3"])
        expected = {
            "50-kayobe-br0": [
                {
                    "Match": [
                        {"Name": "br0"}
                    ]
                },
            ],
            "50-kayobe-p-br0-phy": [
                {
                    "Match": [
                        {"Name": "p-br0-phy"}
                    ]
                },
                {
                    "Network": [
                        {"Bridge": "br0"},
                    ]
                },
            ],
            "50-kayobe-p-br0-ovs": [
                {
                    "Match": [
                        {"Name": "p-br0-ovs"}
                    ]
                },
                {
                    "Network": [
                        {"ConfigureWithoutCarrier": "true"},
                    ]
                },
            ],
        }
        self.assertEqual(expected, nets)

    def test_veth_with_mtu(self):
        self._update_context({"external_net_names": ["net3"],
                              "net3_bridge_ports": [],
                              "net3_mtu": 1400})
        nets = networkd.networkd_networks(self.context, ["net3"])
        expected = {
            "50-kayobe-br0": [
                {
                    "Match": [
                        {"Name": "br0"}
                    ]
                },
                {
                    "Link": [
                        {"MTUBytes": 1400},
                    ]
                },
            ],
            "50-kayobe-p-br0-phy": [
                {
                    "Match": [
                        {"Name": "p-br0-phy"}
                    ]
                },
                {
                    "Network": [
                        {"Bridge": "br0"},
                    ]
                },
                {
                    "Link": [
                        {"MTUBytes": 1400},
                    ]
                },
            ],
            "50-kayobe-p-br0-ovs": [
                {
                    "Match": [
                        {"Name": "p-br0-ovs"}
                    ]
                },
                {
                    "Network": [
                        {"ConfigureWithoutCarrier": "true"},
                    ]
                },
                {
                    "Link": [
                        {"MTUBytes": 1400},
                    ]
                },
            ],
        }
        self.assertEqual(expected, nets)

    def test_veth_on_vlan(self):
        # Test the case where a VLAN interface is one of the networks that
        # needs patching to OVS. The parent interface is a bridge, and the veth
        # pair should be plugged into it.
        self._update_context({
            "provision_wl_net_name": "net7",
            "net3_bridge_ports": [],
            "net7_interface": "br0.42",
            "net7_vlan": 42})
        nets = networkd.networkd_networks(self.context, ["net3", "net7"])
        expected = {
            "50-kayobe-br0": [
                {
                    "Match": [
                        {"Name": "br0"}
                    ]
                },
                {
                    "Network": [
                        {"VLAN": "br0.42"}
                    ]
                }
            ],
            "50-kayobe-br0.42": [
                {
                    "Match": [
                        {"Name": "br0.42"}
                    ]
                },
            ],
            "50-kayobe-p-br0-phy": [
                {
                    "Match": [
                        {"Name": "p-br0-phy"}
                    ]
                },
                {
                    "Network": [
                        {"Bridge": "br0"},
                    ]
                },
            ],
            "50-kayobe-p-br0-ovs": [
                {
                    "Match": [
                        {"Name": "p-br0-ovs"}
                    ]
                },
                {
                    "Network": [
                        {"ConfigureWithoutCarrier": "true"},
                    ]
                },
            ],
        }
        self.assertEqual(expected, nets)

    def test_veth_no_interface(self):
        self._update_context({"external_net_names": ["net3"],
                              "net3_interface": None})
        self.assertRaises(errors.AnsibleFilterError,
                          networkd.networkd_networks, self.context, ["net3"])

    def test_no_veth_without_bridge(self):
        self._update_context({"external_net_names": ["net1"]})
        nets = networkd.networkd_networks(self.context, ["net1"])
        expected = {
            "50-kayobe-eth0": [
                {
                    "Match": [
                        {"Name": "eth0"}
                    ]
                },
                {
                    "Network": [
                        {"Address": "1.2.3.4/24"},
                    ]
                },
            ]
        }
        self.assertEqual(expected, nets)

    def test_no_veth_on_vlan_without_bridge(self):
        # Test the case where a VLAN interface is one of the networks that
        # needs patching to OVS. The parent interface is a bridge, and the veth
        # pair should be plugged into it.
        self._update_context({"provision_wl_net": "net2"})
        nets = networkd.networkd_networks(self.context, ["net1", "net2"])
        expected = {
            "50-kayobe-eth0": [
                {
                    "Match": [
                        {"Name": "eth0"}
                    ]
                },
                {
                    "Network": [
                        {"Address": "1.2.3.4/24"},
                        {"VLAN": "eth0.2"},
                    ]
                },
            ],
            "50-kayobe-eth0.2": [
                {
                    "Match": [
                        {"Name": "eth0.2"}
                    ]
                },
            ]
        }
        self.assertEqual(expected, nets)
