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

import jinja2

from ansible import errors
from kayobe.plugins.filter import networks


class BaseNetworksTest(unittest.TestCase):

    maxDiff = 2000

    variables = {
        # Inventory hostname, used to index IP list.
        "inventory_hostname": "test-host",
        # net1: Ethernet on eth0 with IP 1.2.3.4/24.
        "net1_interface": "eth0",
        # net2: VLAN on eth0.2 with VLAN 2 on interface eth0.
        "net2_interface": "eth0.2",
        "net2_vlan": 2,
        # net3: bridge on br0 with ports eth0 and eth1.
        "net3_interface": "br0",
        "net3_bridge_ports": ['eth0', 'eth1'],
        # net4: VLAN on br0.4 with VLAN 4 on bridge br0.
        "net4_interface": "br0.4",
        "net4_vlan": 4,
        # net5: VLAN on br0.5 with VLAN 5 on bridge br0.
        "net5_interface": "br0.5",
        "net5_vlan": 5,
        # Veth pair patch link prefix and suffix.
        "network_patch_prefix": "p-",
        "network_patch_suffix_ovs": "-ovs",
        "network_patch_suffix_phy": "-phy",
    }

    def setUp(self):
        # Bandit complains about Jinja2 autoescaping without nosec.
        self.env = jinja2.Environment()  # nosec
        self.context = self._make_context(self.variables)

    def _make_context(self, parent):
        return self.env.context_class(
            self.env, parent=parent, name='dummy', blocks={})

    def _update_context(self, variables):
        updated_vars = copy.deepcopy(self.variables)
        updated_vars.update(variables)
        self.context = self._make_context(updated_vars)


class TestNetworks(BaseNetworksTest):

    def test_get_ovs_veths_empty(self):
        veths = networks.get_ovs_veths(self.context, [], None)
        self.assertEqual([], veths)

    def test_get_ovs_veths_eth(self):
        # Ethernet does not need a veth pair.
        self._update_context({"external_net_names": ["net1"]})
        veths = networks.get_ovs_veths(self.context, ["net1"], None)
        self.assertEqual([], veths)

    def test_get_ovs_veths_eth_vlan(self):
        # VLAN on Ethernet does not need a veth pair.
        self._update_context({"external_net_names": ["net2"]})
        veths = networks.get_ovs_veths(self.context, ["net2"], None)
        self.assertEqual([], veths)

    def test_get_ovs_veths_bridge(self):
        # Bridge needs a veth pair.
        self._update_context({"external_net_names": ["net3"]})
        veths = networks.get_ovs_veths(self.context, ["net3"], None)
        expected = [
            {
                "name": "p-br0-phy",
                "peer": "p-br0-ovs",
                "bridge": "br0",
                "mtu": None,
            }
        ]
        self.assertEqual(expected, veths)

    def test_get_ovs_veths_bridge_provision_wl(self):
        # Bridge needs a veth pair.
        self._update_context({"provision_wl_net_name": "net3"})
        veths = networks.get_ovs_veths(self.context, ["net3"], None)
        expected = [
            {
                "name": "p-br0-phy",
                "peer": "p-br0-ovs",
                "bridge": "br0",
                "mtu": None,
            }
        ]
        self.assertEqual(expected, veths)

    def test_get_ovs_veths_bridge_cleaning(self):
        # Bridge needs a veth pair.
        self._update_context({"cleaning_net_name": "net3"})
        veths = networks.get_ovs_veths(self.context, ["net3"], None)
        expected = [
            {
                "name": "p-br0-phy",
                "peer": "p-br0-ovs",
                "bridge": "br0",
                "mtu": None,
            }
        ]
        self.assertEqual(expected, veths)

    def test_get_ovs_veths_bridge_mtu(self):
        # Use the MTU of bridge.
        self._update_context({"external_net_names": ["net3"],
                              "net3_mtu": 1400})
        veths = networks.get_ovs_veths(self.context, ["net3"], None)
        expected = [
            {
                "name": "p-br0-phy",
                "peer": "p-br0-ovs",
                "bridge": "br0",
                "mtu": 1400,
            }
        ]
        self.assertEqual(expected, veths)

    def test_get_ovs_veths_bridge_vlan(self):
        # VLAN on a bridge needs a veth pair.
        self._update_context({"external_net_names": ["net4"]})
        veths = networks.get_ovs_veths(self.context, ["net3", "net4"], None)
        expected = [
            {
                "name": "p-br0-phy",
                "peer": "p-br0-ovs",
                "bridge": "br0",
                "mtu": None,
            }
        ]
        self.assertEqual(expected, veths)

    def test_get_ovs_veths_bridge_vlan_mtu(self):
        # Use the MTU of VLAN on a bridge.
        self._update_context({"external_net_names": ["net4"],
                              "net4_mtu": 1400})
        veths = networks.get_ovs_veths(self.context, ["net3", "net4"], None)
        expected = [
            {
                "name": "p-br0-phy",
                "peer": "p-br0-ovs",
                "bridge": "br0",
                "mtu": 1400,
            }
        ]
        self.assertEqual(expected, veths)

    def test_get_ovs_veths_bridge_vlan_multiple(self):
        # Multiple VLANs on a bridge need a single veth pair.
        self._update_context({"external_net_names": ["net4", "net5"]})
        veths = networks.get_ovs_veths(self.context, ["net3", "net4", "net5"],
                                       None)
        expected = [
            {
                "name": "p-br0-phy",
                "peer": "p-br0-ovs",
                "bridge": "br0",
                "mtu": None,
            }
        ]
        self.assertEqual(expected, veths)

    def test_get_ovs_veths_bridge_vlan_multiple_mtu(self):
        # Use the highest MTU of multiple VLANs on a bridge.
        self._update_context({"external_net_names": ["net4", "net5"],
                              "net4_mtu": 1400,
                              "net5_mtu": 1500})
        veths = networks.get_ovs_veths(self.context, ["net3", "net4", "net5"],
                                       None)
        expected = [
            {
                "name": "p-br0-phy",
                "peer": "p-br0-ovs",
                "bridge": "br0",
                "mtu": 1500,
            }
        ]
        self.assertEqual(expected, veths)

    def test_ensure_bridge_ports_is_list(self):
        self._update_context({"net3_bridge_ports": "ens3"})
        self.assertRaises(errors.AnsibleFilterError, networks.net_bridge_ports,
                          self.context, "net3")

    def test_physical_interface_bond(self):
        self._update_context({"net6_interface": "bond0",
                              "net6_bond_slaves": ["eth3", "eth4"]})
        interface = networks.net_physical_interface(self.context, "net6")
        expected = ['eth3', 'eth4']
        self.assertEqual(expected, interface)

    def test_physical_interface_bridge(self):
        interface = networks.net_physical_interface(self.context, "net3")
        expected = ['eth0', 'eth1']
        self.assertEqual(expected, interface)

    def test_physical_interface_direct(self):
        interface = networks.net_physical_interface(self.context, "net1")
        expected = ['eth0']
        self.assertEqual(expected, interface)
