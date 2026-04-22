# Copyright (c) 2026 StackHPC Ltd.
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

import jinja2
import unittest

from kayobe.plugins.filter import nmstate


class TestNMStateFilter(unittest.TestCase):

    maxDiff = 2000

    variables = {
        "inventory_hostname": "test-host",
        "ansible_facts": {"os_family": "RedHat"},
        # net1: Ethernet on eth0 with IP 1.2.3.4/24.
        "net1_interface": "eth0",
        "net1_ips": {"test-host": "1.2.3.4"},
        "net1_cidr": "1.2.3.4/24",
        "net1_gateway": "1.2.3.1",
        "net1_mtu": 1500,
        "net1_ethtool_config": {
            "ring": {"rx": 2048, "tx": 2048},
            "feature": {"rx": True, "gso": False}
        },
        # net2: VLAN on eth0.2 with VLAN 2 on interface eth0.
        "net2_interface": "eth0.2",
        "net2_vlan": 2,
        "net2_ips": {"test-host": "1.2.4.4"},
        "net2_cidr": "1.2.4.4/24",
        # net3: bridge on br0 with ports eth1.
        "net3_interface": "br0",
        "net3_bridge_ports": ['eth1'],
        "net3_bridge_stp": True,
        # net4: bond on bond0 with slaves eth2 and eth3.
        "net4_interface": "bond0",
        "net4_bond_slaves": ['eth2', 'eth3'],
        "net4_bond_mode": "layer3+4",
        "net4_bond_miimon": 100,
        "net4_bond_updelay": 200,
        "net4_bond_downdelay": 300,
        "net4_bond_xmit_hash_policy": "layer3+4",
        "net4_bond_lacp_rate": 1,
        "net4_bond_ad_select": "bandwidth",
        # net5 & net6: Multiple networks on the same interface eth4
        "net5_interface": "eth4",
        "net5_ips": {"test-host": "10.0.0.1"},
        "net5_cidr": "10.0.0.1/24",
        "net6_interface": "eth4",
        "net6_ips": {"test-host": "10.0.0.2"},
        "net6_cidr": "10.0.0.2/24",
    }

    def setUp(self):
        self.env = jinja2.Environment(autoescape=True)
        self.env.filters["bool"] = self._jinja2_bool
        self.context = self._make_context(self.variables)

    def _jinja2_bool(self, value):
        if isinstance(value, bool):
            return value
        if str(value).lower() in ("true", "yes", "on", "1"):
            return True
        return False

    def _make_context(self, parent):
        return self.env.context_class(
            self.env, parent=parent, name='dummy', blocks={})

    def test_nmstate_config_ethernet(self):
        result = nmstate.nmstate_config(self.context, ["net1"])
        expected_iface = {
            "name": "eth0",
            "state": "up",
            "type": "ethernet",
            "mtu": 1500,
            "ipv4": {
                "enabled": True,
                "dhcp": False,
                "address": [{"ip": "1.2.3.4", "prefix-length": 24}]
            },
            "ethtool": {
                "ring": {
                    "rx": 2048,
                    "tx": 2048
                },
                "feature": {
                    "rx-checksum": True,
                    "tx-generic-segmentation": False
                }
            }
        }
        self.assertIn(expected_iface, result["interfaces"])
        route = result["routes"]["config"][0]
        self.assertEqual(route["next-hop-address"], "1.2.3.1")

    def test_nmstate_config_vlan(self):
        result = nmstate.nmstate_config(self.context, ["net2"])
        # Should have eth0 and eth0.2
        ifnames = [i["name"] for i in result["interfaces"]]
        self.assertIn("eth0", ifnames)
        self.assertIn("eth0.2", ifnames)

        vlan_iface = next(i for i in result["interfaces"]
                          if i["name"] == "eth0.2")
        self.assertEqual(vlan_iface["type"], "vlan")
        self.assertEqual(vlan_iface["vlan"]["base-iface"], "eth0")
        self.assertEqual(vlan_iface["vlan"]["id"], 2)

    def test_nmstate_config_bridge(self):
        result = nmstate.nmstate_config(self.context, ["net3"])
        br_iface = next(i for i in result["interfaces"] if i["name"] == "br0")
        self.assertEqual(br_iface["type"], "linux-bridge")
        self.assertEqual(br_iface["bridge"]["port"], [{"name": "eth1"}])
        self.assertTrue(br_iface["bridge"]["options"]["stp"]["enabled"])

        # eth1 should be present as ethernet
        eth1_iface = next(i for i in result["interfaces"]
                          if i["name"] == "eth1")
        self.assertEqual(eth1_iface["type"], "ethernet")

    def test_nmstate_config_bond(self):
        result = nmstate.nmstate_config(self.context, ["net4"])
        bond_iface = next(i for i in result["interfaces"]
                          if i["name"] == "bond0")
        self.assertEqual(bond_iface["type"], "bond")
        self.assertEqual(bond_iface["link-aggregation"]["mode"], "layer3+4")
        self.assertEqual(
            bond_iface["link-aggregation"]["options"],
            {
                "ad_select": "bandwidth",
                "downdelay": 300,
                "lacp_rate": 1,
                "miimon": 100,
                "updelay": 200,
                "xmit_hash_policy": "layer3+4",
            }
        )
        ports = set(bond_iface["link-aggregation"]["port"])
        self.assertEqual(ports, {"eth2", "eth3"})

    def test_nmstate_config_multiple_nets_same_iface(self):
        result = nmstate.nmstate_config(self.context, ["net5", "net6"])
        eth4_iface = next(i for i in result["interfaces"]
                          if i["name"] == "eth4")
        self.assertEqual(eth4_iface["type"], "ethernet")
        addresses = eth4_iface["ipv4"]["address"]
        self.assertEqual(len(addresses), 2)
        ips = {a["ip"] for a in addresses}
        self.assertEqual(ips, {"10.0.0.1", "10.0.0.2"})

    def test_nmstate_config_dummy_interface_infers_dummy_type(self):
        variables = {
            "inventory_hostname": "test-host",
            "test_interface": "dummy2",
        }
        context = self._make_context(variables)
        result = nmstate.nmstate_config(context, ["test"])

        iface = next(i for i in result["interfaces"] if i["name"] == "dummy2")
        self.assertEqual(iface["type"], "dummy")

    def test_nmstate_config_dummy_interface_explicit_type_override(self):
        variables = {
            "inventory_hostname": "test-host",
            "test_interface": "dummy2",
            "test_type": "ethernet",
        }
        context = self._make_context(variables)
        result = nmstate.nmstate_config(context, ["test"])

        iface = next(i for i in result["interfaces"] if i["name"] == "dummy2")
        self.assertEqual(iface["type"], "ethernet")

    def test_nmstate_config_bridge_ports_infer_dummy_type(self):
        variables = {
            "inventory_hostname": "test-host",
            "ansible_facts": {"os_family": "RedHat"},
            "test_interface": "br0",
            "test_bridge_ports": ["dummy3", "dummy4"],
        }
        context = self._make_context(variables)
        result = nmstate.nmstate_config(context, ["test"])

        dummy3 = next(i for i in result["interfaces"] if i["name"] == "dummy3")
        dummy4 = next(i for i in result["interfaces"] if i["name"] == "dummy4")
        self.assertEqual(dummy3["type"], "dummy")
        self.assertEqual(dummy4["type"], "dummy")

    def test_nmstate_config_bridge_port_explicit_type_override(self):
        variables = {
            "inventory_hostname": "test-host",
            "ansible_facts": {"os_family": "RedHat"},
            "test_interface": "br0",
            "test_bridge_ports": ["dummy3", "dummy4"],
            "test_port_type_dummy3": "ethernet",
        }
        context = self._make_context(variables)
        result = nmstate.nmstate_config(context, ["test"])

        dummy3 = next(i for i in result["interfaces"] if i["name"] == "dummy3")
        dummy4 = next(i for i in result["interfaces"] if i["name"] == "dummy4")
        self.assertEqual(dummy3["type"], "ethernet")
        self.assertEqual(dummy4["type"], "dummy")

    def test_nmstate_config_bond_slaves_infer_dummy_type(self):
        variables = {
            "inventory_hostname": "test-host",
            "test_interface": "bond0",
            "test_bond_slaves": ["dummy5", "dummy6"],
        }
        context = self._make_context(variables)
        result = nmstate.nmstate_config(context, ["test"])

        dummy5 = next(i for i in result["interfaces"] if i["name"] == "dummy5")
        dummy6 = next(i for i in result["interfaces"] if i["name"] == "dummy6")
        self.assertEqual(dummy5["type"], "dummy")
        self.assertEqual(dummy6["type"], "dummy")

    def test_nmstate_config_bond_slave_explicit_type_override(self):
        variables = {
            "inventory_hostname": "test-host",
            "test_interface": "bond0",
            "test_bond_slaves": ["dummy5", "dummy6"],
            "test_slave_type_dummy5": "ethernet",
        }
        context = self._make_context(variables)
        result = nmstate.nmstate_config(context, ["test"])

        dummy5 = next(i for i in result["interfaces"] if i["name"] == "dummy5")
        dummy6 = next(i for i in result["interfaces"] if i["name"] == "dummy6")
        self.assertEqual(dummy5["type"], "ethernet")
        self.assertEqual(dummy6["type"], "dummy")

    def test_ethtool_ring_configuration(self):
        """Test structured ethtool ring buffer configuration."""
        variables = {
            "inventory_hostname": "test-host",
            "test_interface": "eth0",
            "test_ethtool_config": {
                "ring": {"rx": 4096, "tx": 2048, "rx-max": 8192}
            }
        }
        context = self._make_context(variables)
        result = nmstate.nmstate_config(context, ["test"])

        eth_iface = next(i for i in result["interfaces"]


                         if i["name"] == "eth0")
        expected_ethtool = {
            "ring": {"rx": 4096, "tx": 2048, "rx-max": 8192}
        }
        self.assertEqual(eth_iface["ethtool"], expected_ethtool)

    def test_ethtool_tier1_features(self):
        """Test Tier 1 ethtool features with canonical names."""
        variables = {
            "inventory_hostname": "test-host",
            "test_interface": "eth0",
            "test_ethtool_config": {
                "feature": {
                    "rx-checksum": True,
                    "tx-checksum-ip-generic": False,
                    "rx-gro": True,
                    "tx-generic-segmentation": False,
                    "rx-lro": True,
                    "hw-tc-offload": True
                }
            }
        }
        context = self._make_context(variables)
        result = nmstate.nmstate_config(context, ["test"])

        eth_iface = next(i for i in result["interfaces"]


                         if i["name"] == "eth0")
        expected_features = {
            "rx-checksum": True,
            "tx-checksum-ip-generic": False,
            "rx-gro": True,
            "tx-generic-segmentation": False,
            "rx-lro": True,
            "hw-tc-offload": True
        }
        self.assertEqual(eth_iface["ethtool"]["feature"], expected_features)

    def test_ethtool_feature_aliases(self):
        """Test ethtool feature alias resolution."""
        variables = {
            "inventory_hostname": "test-host",
            "test_interface": "eth0",
            "test_ethtool_config": {
                "feature": {
                    "rx": True,        # alias for rx-checksum
                    "gro": False,      # alias for rx-gro
                    "gso": True,       # alias for tx-generic-segmentation
                    "lro": False       # alias for rx-lro
                }
            }
        }
        context = self._make_context(variables)
        result = nmstate.nmstate_config(context, ["test"])

        eth_iface = next(i for i in result["interfaces"]


                         if i["name"] == "eth0")
        expected_features = {
            "rx-checksum": True,
            "rx-gro": False,
            "tx-generic-segmentation": True,
            "rx-lro": False
        }
        self.assertEqual(eth_iface["ethtool"]["feature"], expected_features)

    def test_ethtool_combined_config(self):
        """Test combined ring and feature configuration."""
        variables = {
            "inventory_hostname": "test-host",
            "test_interface": "eth0",
            "test_ethtool_config": {
                "ring": {"rx": 1024, "tx": 512},
                "feature": {"rx": True, "gso": False}
            }
        }
        context = self._make_context(variables)
        result = nmstate.nmstate_config(context, ["test"])

        eth_iface = next(i for i in result["interfaces"]


                         if i["name"] == "eth0")
        expected_ethtool = {
            "ring": {"rx": 1024, "tx": 512},
            "feature": {"rx-checksum": True, "tx-generic-segmentation": False}
        }
        self.assertEqual(eth_iface["ethtool"], expected_ethtool)

    def test_ethtool_invalid_feature(self):
        """Test error handling for unsupported features."""
        variables = {
            "inventory_hostname": "test-host",
            "test_interface": "eth0",
            "test_ethtool_config": {
                "feature": {"unsupported-feature": True}
            }
        }
        context = self._make_context(variables)

        with self.assertRaises(ValueError) as cm:
            nmstate.nmstate_config(context, ["test"])
        self.assertIn(
            "Unsupported ethtool features: unsupported-feature",
            str(cm.exception))

    def test_ethtool_invalid_ring_param(self):
        """Test error handling for invalid ring parameters."""
        variables = {
            "inventory_hostname": "test-host",
            "test_interface": "eth0",
            "test_ethtool_config": {
                "ring": {"invalid-param": 1024}
            }
        }
        context = self._make_context(variables)

        with self.assertRaises(ValueError) as cm:
            nmstate.nmstate_config(context, ["test"])
        self.assertIn(

            "Unsupported ring parameters: invalid-param", str(cm.exception))

    def test_ethtool_invalid_feature_value(self):
        """Test error handling for non-boolean feature values."""
        variables = {
            "inventory_hostname": "test-host",
            "test_interface": "eth0",
            "test_ethtool_config": {
                "feature": {"rx-checksum": "invalid"}
            }
        }
        context = self._make_context(variables)

        with self.assertRaises(ValueError) as cm:
            nmstate.nmstate_config(context, ["test"])
        self.assertIn(

            "Ethtool feature 'rx-checksum' must be boolean", str(cm.exception))

    def test_ethtool_invalid_ring_value(self):
        """Test error handling for invalid ring values."""
        variables = {
            "inventory_hostname": "test-host",
            "test_interface": "eth0",
            "test_ethtool_config": {
                "ring": {"rx": -1}
            }
        }
        context = self._make_context(variables)

        with self.assertRaises(ValueError) as cm:
            nmstate.nmstate_config(context, ["test"])
        self.assertIn(
            "Ring parameter 'rx' must be a non-negative integer",
            str(cm.exception))

    def test_vlan_interface_naming_heuristic(self):
        """Test VLAN ID derivation from interface name.

        Tests derivation without explicit vlan attribute.
        """
        variables = {
            "inventory_hostname": "test-host",
            "ansible_facts": {"os_family": "RedHat"},
            "vlan_interface": "eth0.123",
        }
        context = self._make_context(variables)
        result = nmstate.nmstate_config(context, ["vlan"])

        vlan_iface = next(
            i for i in result["interfaces"]
            if i["name"] == "eth0.123")
        self.assertEqual(vlan_iface["type"], "vlan")
        self.assertEqual(vlan_iface["vlan"]["base-iface"], "eth0")
        self.assertEqual(vlan_iface["vlan"]["id"], 123)

    def test_vlan_interface_explicit_vlan_and_parent(self):
        """Test VLAN with explicit vlan and parent attributes."""
        variables = {
            "inventory_hostname": "test-host",
            "ansible_facts": {"os_family": "RedHat"},
            "vlan_interface": "custom1",
            "vlan_vlan": 100,
            "vlan_parent": "eth0",
        }
        context = self._make_context(variables)
        result = nmstate.nmstate_config(context, ["vlan"])

        vlan_iface = next(
            i for i in result["interfaces"]
            if i["name"] == "custom1")
        self.assertEqual(vlan_iface["type"], "vlan")
        self.assertEqual(vlan_iface["vlan"]["base-iface"], "eth0")
        self.assertEqual(vlan_iface["vlan"]["id"], 100)

    def test_vlan_interface_invalid_name(self):
        """Test VLAN with invalid interface name is skipped gracefully."""
        variables = {
            "inventory_hostname": "test-host",
            "ansible_facts": {"os_family": "RedHat"},
            "vlan_interface": "eth0",
        }
        context = self._make_context(variables)
        result = nmstate.nmstate_config(context, ["vlan"])

        eth_iface = next(
            i for i in result["interfaces"]
            if i["name"] == "eth0")
        self.assertEqual(eth_iface["type"], "ethernet")

    def test_vlan_interface_parent_derivation(self):
        """Test VLAN parent derivation from interface name."""
        variables = {
            "inventory_hostname": "test-host",
            "ansible_facts": {"os_family": "RedHat"},
            "vlan_interface": "bond0.42",
            "vlan_vlan": 42,
        }
        context = self._make_context(variables)
        result = nmstate.nmstate_config(context, ["vlan"])

        vlan_iface = next(
            i for i in result["interfaces"]
            if i["name"] == "bond0.42")
        self.assertEqual(vlan_iface["vlan"]["base-iface"], "bond0")
        self.assertEqual(vlan_iface["vlan"]["id"], 42)

        bond_iface = next(
            i for i in result["interfaces"]
            if i["name"] == "bond0")
        self.assertEqual(bond_iface["state"], "up")

    def test_vlan_interface_qos_map_structured(self):
        context = self._make_context(
            {
                "inventory_hostname": "test-host",
                "ansible_facts": {"os_family": "RedHat"},
                "vlan_interface": "eth0.123",
                "vlan_ingress_qos_map": [
                    {"from": 7, "to": 254},
                    {"from": 3, "to": 12},
                ],
                "vlan_egress_qos_map": [
                    {"from": 130, "to": 6},
                    {"from": 129, "to": 7},
                ],
            }
        )

        result = nmstate.nmstate_config(context, ["vlan"])
        vlan_iface = next(
            iface for iface in result["interfaces"]
            if iface["name"] == "eth0.123"
        )
        self.assertEqual(
            vlan_iface["vlan"]["ingress-qos-map"],
            [{"from": 3, "to": 12}, {"from": 7, "to": 254}],
        )
        self.assertEqual(
            vlan_iface["vlan"]["egress-qos-map"],
            [{"from": 129, "to": 7}, {"from": 130, "to": 6}],
        )

    def test_vlan_interface_qos_map_invalid_input(self):
        test_cases = [
            ("non-list input", {"vlan_ingress_qos_map": ""}),
            ("missing required key", {"vlan_ingress_qos_map": [{"from": 1}]}),
            ("wrong entry type", {"vlan_ingress_qos_map": ["1:2"]}),
            (
                "invalid numeric bound",
                {"vlan_egress_qos_map": [{"from": 129, "to": 8}]},
            ),
        ]

        for test_case, qos_map in test_cases:
            variables = {
                "inventory_hostname": "test-host",
                "ansible_facts": {"os_family": "RedHat"},
                "vlan_interface": "eth0.123",
            }
            variables.update(qos_map)
            context = self._make_context(variables)

            with self.subTest(test_case=test_case):
                with self.assertRaises(ValueError):
                    nmstate.nmstate_config(context, ["vlan"])

    def test_bridge_stp_unset(self):
        """Test bridge with unset bridge_stp does not configure STP."""
        variables = {
            "inventory_hostname": "test-host",
            "ansible_facts": {"os_family": "Debian"},
            "test_interface": "br0",
            "test_bridge_ports": ["eth1"],
        }
        context = self._make_context(variables)
        result = nmstate.nmstate_config(context, ["test"])

        br_iface = next(i for i in result["interfaces"] if i["name"] == "br0")
        self.assertEqual(br_iface["type"], "linux-bridge")
        self.assertEqual(br_iface["bridge"]["port"], [{"name": "eth1"}])
        self.assertNotIn("options", br_iface["bridge"])

    def test_bridge_stp_true(self):
        """Test bridge with STP explicitly enabled."""
        variables = {
            "inventory_hostname": "test-host",
            "ansible_facts": {"os_family": "RedHat"},
            "test_interface": "br0",
            "test_bridge_ports": ["eth1"],
            "test_bridge_stp": "true",
        }
        context = self._make_context(variables)
        result = nmstate.nmstate_config(context, ["test"])

        br_iface = next(i for i in result["interfaces"] if i["name"] == "br0")
        self.assertTrue(br_iface["bridge"]["options"]["stp"]["enabled"])

    def test_bridge_stp_false(self):
        """Test bridge with STP explicitly disabled."""
        variables = {
            "inventory_hostname": "test-host",
            "ansible_facts": {"os_family": "RedHat"},
            "test_interface": "br0",
            "test_bridge_ports": ["eth1"],
            "test_bridge_stp": "false",
        }
        context = self._make_context(variables)
        result = nmstate.nmstate_config(context, ["test"])

        br_iface = next(i for i in result["interfaces"] if i["name"] == "br0")
        self.assertFalse(br_iface["bridge"]["options"]["stp"]["enabled"])

    def test_defroute_false_static_ip(self):
        """Test defroute=false suppresses default route for static IP."""
        variables = {
            "inventory_hostname": "test-host",
            "test_interface": "eth0",
            "test_ips": {"test-host": "10.0.0.1"},
            "test_cidr": "10.0.0.1/24",
            "test_gateway": "10.0.0.254",
            "test_defroute": "false",
        }
        context = self._make_context(variables)
        result = nmstate.nmstate_config(context, ["test"])

        eth_iface = next(
            i for i in result["interfaces"]
            if i["name"] == "eth0")
        self.assertEqual(
            eth_iface["ipv4"]["address"][0]["ip"], "10.0.0.1")

        default_routes = [
            r for r in result["routes"]["config"]
            if r["destination"] == "0.0.0.0/0"]
        self.assertEqual(len(default_routes), 0)

    def test_defroute_true_static_ip(self):
        """Test defroute=true adds default route for static IP."""
        variables = {
            "inventory_hostname": "test-host",
            "test_interface": "eth0",
            "test_ips": {"test-host": "10.0.0.1"},
            "test_cidr": "10.0.0.1/24",
            "test_gateway": "10.0.0.254",
            "test_defroute": "true",
        }
        context = self._make_context(variables)
        result = nmstate.nmstate_config(context, ["test"])

        default_routes = [
            r for r in result["routes"]["config"]
            if r["destination"] == "0.0.0.0/0"]
        self.assertEqual(len(default_routes), 1)
        self.assertEqual(default_routes[0]["next-hop-address"],
                         "10.0.0.254")

    def test_defroute_unset_static_ip(self):
        """Test defroute unset (None) adds default route for static IP."""
        variables = {
            "inventory_hostname": "test-host",
            "test_interface": "eth0",
            "test_ips": {"test-host": "10.0.0.1"},
            "test_cidr": "10.0.0.1/24",
            "test_gateway": "10.0.0.254",
        }
        context = self._make_context(variables)
        result = nmstate.nmstate_config(context, ["test"])

        default_routes = [
            r for r in result["routes"]["config"]
            if r["destination"] == "0.0.0.0/0"]
        self.assertEqual(len(default_routes), 1)
        self.assertEqual(default_routes[0]["next-hop-address"],
                         "10.0.0.254")

    def test_defroute_false_dhcp(self):
        """Test defroute=false disables auto-routes for DHCP."""
        variables = {
            "inventory_hostname": "test-host",
            "test_interface": "eth0",
            "test_bootproto": "dhcp",
            "test_gateway": "10.0.0.1",
            "test_defroute": "false",
        }
        context = self._make_context(variables)
        result = nmstate.nmstate_config(context, ["test"])

        eth_iface = next(
            i for i in result["interfaces"]
            if i["name"] == "eth0")
        self.assertTrue(eth_iface["ipv4"]["dhcp"])
        self.assertFalse(eth_iface["ipv4"]["auto-routes"])

        default_routes = [
            r for r in result["routes"]["config"]
            if r["destination"] == "0.0.0.0/0"]
        self.assertEqual(len(default_routes), 0)

    def test_defroute_true_dhcp(self):
        """Test defroute=true allows default routes for DHCP."""
        variables = {
            "inventory_hostname": "test-host",
            "test_interface": "eth0",
            "test_bootproto": "dhcp",
            "test_gateway": "10.0.0.1",
            "test_defroute": "true",
        }
        context = self._make_context(variables)
        result = nmstate.nmstate_config(context, ["test"])

        eth_iface = next(
            i for i in result["interfaces"]
            if i["name"] == "eth0")
        self.assertTrue(eth_iface["ipv4"]["dhcp"])
        self.assertNotIn("auto-routes", eth_iface["ipv4"])

        default_routes = [
            r for r in result["routes"]["config"]
            if r["destination"] == "0.0.0.0/0"]
        self.assertEqual(len(default_routes), 1)
        self.assertEqual(default_routes[0]["next-hop-address"],
                         "10.0.0.1")

    def test_ovs_patch_links(self):
        variables = {
            "inventory_hostname": "test-host",
            "ansible_facts": {"os_family": "RedHat"},
            "net3_interface": "br0",
            "net3_bridge_ports": ["eth1"],
            "provision_wl_net_name": "net3",
            "network_patch_prefix": "p-",
            "network_patch_suffix_phy": "-phy",
            "network_patch_suffix_ovs": "-ovs",
        }
        context = self._make_context(variables)

        result = nmstate.nmstate_config(context, ["net3"])
        interfaces = {iface["name"]: iface for iface in result["interfaces"]}

        self.assertIn("p-br0-phy", interfaces)
        self.assertIn("p-br0-ovs", interfaces)
        self.assertEqual(interfaces["p-br0-phy"]["type"], "veth")
        self.assertEqual(
            interfaces["p-br0-phy"]["veth"],
            {"peer": "p-br0-ovs"}
        )
        self.assertEqual(interfaces["p-br0-phy"]["ipv4"], {"enabled": False})
        self.assertEqual(interfaces["p-br0-phy"]["ipv6"], {"enabled": False})

        self.assertEqual(interfaces["p-br0-ovs"]["type"], "veth")
        self.assertEqual(
            interfaces["p-br0-ovs"]["veth"],
            {"peer": "p-br0-phy"}
        )
        self.assertEqual(interfaces["p-br0-ovs"]["ipv4"], {"enabled": False})
        self.assertEqual(interfaces["p-br0-ovs"]["ipv6"], {"enabled": False})

        bridge_ports = interfaces["br0"]["bridge"]["port"]
        self.assertIn({"name": "eth1"}, bridge_ports)
        self.assertIn({"name": "p-br0-phy"}, bridge_ports)

    def test_route_without_table(self):
        """Test route without table-id omits the field."""
        variables = {
            "inventory_hostname": "test-host",
            "test_interface": "eth0",
            "test_routes": [
                {"cidr": "10.0.0.0/24", "gateway": "192.168.1.1"}
            ],
        }
        context = self._make_context(variables)
        result = nmstate.nmstate_config(context, ["test"])

        routes = result["routes"]["config"]
        self.assertEqual(len(routes), 1)
        self.assertEqual(routes[0]["destination"], "10.0.0.0/24")
        self.assertEqual(routes[0]["next-hop-address"], "192.168.1.1")
        self.assertNotIn("table-id", routes[0])

    def test_route_with_supported_attributes(self):
        """Test route maps supported nmstate attributes."""
        variables = {
            "inventory_hostname": "test-host",
            "test_interface": "eth0",
            "test_routes": [
                {
                    "cidr": "10.0.0.0/24",
                    "gateway": "192.168.1.1",
                    "metric": "400",
                    "onlink": "true",
                    "src": "192.168.1.2",
                }
            ],
        }
        context = self._make_context(variables)
        result = nmstate.nmstate_config(context, ["test"])

        routes = result["routes"]["config"]
        self.assertEqual(len(routes), 1)
        self.assertEqual(routes[0]["metric"], 400)
        self.assertTrue(routes[0]["on-link"])
        self.assertEqual(routes[0]["source"], "192.168.1.2")

    def test_route_with_supported_options(self):
        """Test documented route options map to nmstate attributes."""
        variables = {
            "inventory_hostname": "test-host",
            "test_interface": "eth0",
            "test_routes": [
                {
                    "cidr": "10.0.0.0/24",
                    "gateway": "192.168.1.1",
                    "options": [
                        "onlink",
                        "metric 400",
                        "src 192.168.1.2",
                    ],
                }
            ],
        }
        context = self._make_context(variables)
        result = nmstate.nmstate_config(context, ["test"])

        routes = result["routes"]["config"]
        self.assertEqual(len(routes), 1)
        self.assertEqual(routes[0]["metric"], 400)
        self.assertTrue(routes[0]["on-link"])
        self.assertEqual(routes[0]["source"], "192.168.1.2")

    def test_route_with_table_name_lookup(self):
        """Test route with table name looks up ID from network_route_tables."""
        variables = {
            "inventory_hostname": "test-host",
            "test_interface": "eth0",
            "test_routes": [
                {"cidr": "10.0.0.0/24", "gateway": "192.168.1.1",
                 "table": "custom-table"}
            ],
            "network_route_tables": [
                {"name": "custom-table", "id": 100}
            ],
        }
        context = self._make_context(variables)
        result = nmstate.nmstate_config(context, ["test"])

        routes = result["routes"]["config"]
        self.assertEqual(len(routes), 1)
        self.assertEqual(routes[0]["table-id"], 100)

    def test_route_with_undefined_table_name(self):
        """Test route with undefined table name raises ValueError."""
        variables = {
            "inventory_hostname": "test-host",
            "test_interface": "eth0",
            "test_routes": [
                {"cidr": "10.0.0.0/24", "gateway": "192.168.1.1",
                 "table": "undefined-table"}
            ],
            "network_route_tables": [],
        }
        context = self._make_context(variables)

        with self.assertRaises(ValueError) as cm:
            nmstate.nmstate_config(context, ["test"])
        self.assertIn("undefined-table", str(cm.exception))
        self.assertIn("not defined in network_route_tables", str(cm.exception))

    def test_route_with_table_id(self):
        """Test route with numeric table ID includes table-id."""
        variables = {
            "inventory_hostname": "test-host",
            "test_interface": "eth0",
            "test_routes": [
                {"cidr": "10.0.0.0/24", "gateway": "192.168.1.1",
                 "table": 100}
            ],
        }
        context = self._make_context(variables)
        result = nmstate.nmstate_config(context, ["test"])

        routes = result["routes"]["config"]
        self.assertEqual(len(routes), 1)
        self.assertEqual(routes[0]["table-id"], 100)

    def test_route_with_string_numeric_table_id(self):
        """Test route with string numeric table ID converts to int."""
        variables = {
            "inventory_hostname": "test-host",
            "test_interface": "eth0",
            "test_routes": [
                {"cidr": "10.0.0.0/24", "gateway": "192.168.1.1",
                 "table": "100"}
            ],
        }
        context = self._make_context(variables)
        result = nmstate.nmstate_config(context, ["test"])

        routes = result["routes"]["config"]
        self.assertEqual(len(routes), 1)
        self.assertEqual(routes[0]["table-id"], 100)

    def test_route_string_not_supported(self):
        """Test string-format routing route raises ValueError."""
        variables = {
            "inventory_hostname": "test-host",
            "test_interface": "eth0",
            "test_routes": [
                "10.0.0.0/24 via 192.168.1.1"
            ],
        }
        context = self._make_context(variables)

        with self.assertRaises(ValueError) as cm:
            nmstate.nmstate_config(context, ["test"])
        self.assertIn(
            "Network 'test' has invalid routing route format at index 0",
            str(cm.exception)
        )
        self.assertIn(
            "String format routes are only supported by the default network "
            "engine",
            str(cm.exception)
        )

    def test_route_unsupported_option_not_supported(self):
        """Test unsupported route options raise ValueError."""
        variables = {
            "inventory_hostname": "test-host",
            "test_interface": "eth0",
            "test_routes": [
                {
                    "cidr": "10.0.0.0/24",
                    "gateway": "192.168.1.1",
                    "options": ["mtu 1400"],
                }
            ],
        }
        context = self._make_context(variables)

        with self.assertRaises(ValueError) as cm:
            nmstate.nmstate_config(context, ["test"])
        self.assertIn(
            "unsupported routing route option",
            str(cm.exception)
        )

    def test_route_conflicting_option_not_supported(self):
        """Test conflicting route keys and options raise ValueError."""
        variables = {
            "inventory_hostname": "test-host",
            "test_interface": "eth0",
            "test_routes": [
                {
                    "cidr": "10.0.0.0/24",
                    "gateway": "192.168.1.1",
                    "metric": 100,
                    "options": ["metric 400"],
                }
            ],
        }
        context = self._make_context(variables)

        with self.assertRaises(ValueError) as cm:
            nmstate.nmstate_config(context, ["test"])
        self.assertIn(
            "conflicting routing route option",
            str(cm.exception)
        )

    def test_rule_string_not_supported(self):
        """Test string-format routing rule raises ValueError."""
        variables = {
            "inventory_hostname": "test-host",
            "test_interface": "eth0",
            "test_rules": [
                "from 192.168.1.0/24 table 200"
            ],
        }
        context = self._make_context(variables)

        with self.assertRaises(ValueError) as cm:
            nmstate.nmstate_config(context, ["test"])
        self.assertIn("Network 'test' has invalid routing rule format",
                      str(cm.exception))
        self.assertIn("String format rules are only supported by the default "
                      "network engine", str(cm.exception))

    def test_rule_minimal(self):
        """Test rule with minimal fields omits optional ones."""
        variables = {
            "inventory_hostname": "test-host",
            "test_interface": "eth0",
            "test_rules": [
                {"to": "10.0.0.0/24", "table": "custom-table"}
            ],
            "network_route_tables": [
                {"name": "custom-table", "id": 200}
            ],
        }
        context = self._make_context(variables)
        result = nmstate.nmstate_config(context, ["test"])

        rules = result["route-rules"]["config"]
        self.assertEqual(len(rules), 1)
        self.assertEqual(rules[0]["ip-to"], "10.0.0.0/24")
        self.assertEqual(rules[0]["route-table"], 200)
        self.assertNotIn("ip-from", rules[0])
        self.assertNotIn("priority", rules[0])

    def test_rule_complete(self):
        """Test rule with all fields includes them."""
        variables = {
            "inventory_hostname": "test-host",
            "test_interface": "eth0",
            "test_rules": [
                {"from": "192.168.1.0/24", "to": "10.0.0.0/24",
                 "priority": 100, "table": "custom-table"}
            ],
            "network_route_tables": [
                {"name": "custom-table", "id": 200}
            ],
        }
        context = self._make_context(variables)
        result = nmstate.nmstate_config(context, ["test"])

        rules = result["route-rules"]["config"]
        self.assertEqual(len(rules), 1)
        self.assertEqual(rules[0]["ip-from"], "192.168.1.0/24")
        self.assertEqual(rules[0]["ip-to"], "10.0.0.0/24")
        self.assertEqual(rules[0]["priority"], 100)
        self.assertEqual(rules[0]["route-table"], 200)

    def test_rule_with_undefined_table_name(self):
        """Test rule with undefined table name raises ValueError."""
        variables = {
            "inventory_hostname": "test-host",
            "test_interface": "eth0",
            "test_rules": [
                {"to": "10.0.0.0/24", "table": "undefined-table"}
            ],
            "network_route_tables": [],
        }
        context = self._make_context(variables)

        with self.assertRaises(ValueError) as cm:
            nmstate.nmstate_config(context, ["test"])
        self.assertIn("undefined-table", str(cm.exception))
        self.assertIn("not defined in network_route_tables", str(cm.exception))

    def test_bond_without_mode(self):
        """Test bond without mode gets default balance-rr mode."""
        variables = {
            "inventory_hostname": "test-host",
            "test_interface": "bond0",
            "test_bond_slaves": ["eth0", "eth1"],
        }
        context = self._make_context(variables)
        result = nmstate.nmstate_config(context, ["test"])

        bond_iface = next(i for i in result["interfaces"]
                          if i["name"] == "bond0")
        self.assertEqual(bond_iface["type"], "bond")
        # nmstate requires bond mode, so default is provided
        self.assertEqual(bond_iface["link-aggregation"]["mode"], "balance-rr")
        self.assertEqual(set(bond_iface["link-aggregation"]["port"]),
                         {"eth0", "eth1"})

    def test_bond_with_explicit_mode(self):
        """Test bond with explicit mode uses specified mode."""
        variables = {
            "inventory_hostname": "test-host",
            "test_interface": "bond0",
            "test_bond_slaves": ["eth0", "eth1"],
            "test_bond_mode": "802.3ad",
        }
        context = self._make_context(variables)
        result = nmstate.nmstate_config(context, ["test"])

        bond_iface = next(i for i in result["interfaces"]
                          if i["name"] == "bond0")
        self.assertEqual(bond_iface["type"], "bond")
        self.assertEqual(bond_iface["link-aggregation"]["mode"], "802.3ad")
        self.assertEqual(set(bond_iface["link-aggregation"]["port"]),
                         {"eth0", "eth1"})
