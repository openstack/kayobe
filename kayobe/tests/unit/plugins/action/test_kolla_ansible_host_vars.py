# Copyright (c) 2020 StackHPC Ltd.
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

from kayobe.plugins.action import kolla_ansible_host_vars


@jinja2.pass_context
def _net_interface(context, name):
    return context.get(name + '_interface')


@jinja2.pass_context
def _net_parent(context, name):
    return context.get(name + '_parent')


@jinja2.pass_context
def _net_vlan(context, name):
    return context.get(name + '_vlan')


@jinja2.pass_context
def _net_select_bridges(context, names):
    return [name for name in names
            if (_net_interface(context, name) or "").startswith("br")]


@jinja2.pass_context
def _net_physical_network(context, name):
    return context.get(name + '_physical_network')


class FakeTemplar(object):

    def __init__(self, variables):
        self.variables = variables
        self.env = jinja2.Environment()
        self.env.filters['net_interface'] = _net_interface
        self.env.filters['net_parent'] = _net_parent
        self.env.filters['net_vlan'] = _net_vlan
        self.env.filters['net_select_bridges'] = _net_select_bridges
        self.env.filters['net_physical_network'] = _net_physical_network

    def template(self, string):
        template = self.env.from_string(string)
        result = template.render(**self.variables)
        return {
            "None": None,
            "True": True,
            "False": False,
        }.get(result, result)


class TestCase(unittest.TestCase):

    variables = {
        "network_interfaces": [
            "foo",
            "bar",
        ],
        "foo_interface": "eth0",
        "foo_vlan": 1,
        "bar_interface": "eth1",
        "bar_vlan": 2,
        "network_bridge_suffix_ovs": "-ovs",
        "network_patch_prefix": "p-",
        "network_patch_suffix_ovs": "-ovs",
    }

    def _create_module(self, variables=None):
        if not variables:
            variables = self.variables
        templar = FakeTemplar(variables)
        return kolla_ansible_host_vars.ActionModule(None, None, None, None,
                                                    templar, None)

    def test__run_empty_args(self):
        module = self._create_module()
        result = module._run([], [])
        expected = {
            "changed": False,
            "ansible_facts": {},
            "_ansible_facts_cacheable": False,
        }
        self.assertEqual(expected, result)

    def test__run_one_interface(self):
        module = self._create_module()
        interfaces = [{
            "var_name": "kolla_foo_interface",
            "network": "foo",
            "description": "Foo network",
            "required": False,
        }]
        result = module._run(interfaces, [])
        expected = {
            "changed": False,
            "ansible_facts": {
                "kolla_foo_interface": "eth0",
            },
            "_ansible_facts_cacheable": False,
        }
        self.assertEqual(expected, result)

    def test__run_two_interfaces(self):
        module = self._create_module()
        interfaces = [{
            "var_name": "kolla_foo_interface",
            "network": "foo",
            "description": "Foo network",
            "required": False,
        }, {
            "var_name": "kolla_bar_interface",
            "network": "bar",
            "description": "Bar network",
            "required": False,
        }]
        result = module._run(interfaces, [])
        expected = {
            "changed": False,
            "ansible_facts": {
                "kolla_foo_interface": "eth0",
                "kolla_bar_interface": "eth1",
            },
            "_ansible_facts_cacheable": False,
        }
        self.assertEqual(expected, result)

    def test__run_interface_not_mapped(self):
        module = self._create_module()
        interfaces = [{
            "var_name": "kolla_baz_interface",
            "network": "baz",
            "description": "Baz network",
            "required": True,
        }]
        result = module._run(interfaces, [])
        expected = {
            "changed": False,
            "failed": True,
            "msg": ("Required network 'baz' (Baz network) is not mapped to "
                    "this host"),
        }
        self.assertEqual(expected, result)

    def test__run_interface_not_mapped_not_required(self):
        module = self._create_module()
        interfaces = [{
            "var_name": "kolla_baz_interface",
            "network": "baz",
            "description": "Baz network",
            "required": False,
        }]
        result = module._run(interfaces, [])
        expected = {
            "changed": False,
            "ansible_facts": {},
            "_ansible_facts_cacheable": False,
        }
        self.assertEqual(expected, result)

    def test__run_interface_no_interface(self):
        variables = copy.deepcopy(self.variables)
        del variables["bar_interface"]
        module = self._create_module(variables)
        interfaces = [{
            "var_name": "kolla_bar_interface",
            "network": "bar",
            "description": "Bar network",
            "required": True,
        }]
        result = module._run(interfaces, [])
        expected = {
            "changed": False,
            "failed": True,
            "msg": ("Required network 'bar' (Bar network) does not have an "
                    "interface configured for this host"),
        }
        self.assertEqual(expected, result)

    def test__run_interface_no_interface_not_required(self):
        variables = copy.deepcopy(self.variables)
        del variables["bar_interface"]
        module = self._create_module(variables)
        interfaces = [{
            "var_name": "kolla_bar_interface",
            "network": "bar",
            "description": "Bar network",
            "required": False,
        }]
        result = module._run(interfaces, [])
        expected = {
            "changed": False,
            "ansible_facts": {},
            "_ansible_facts_cacheable": False,
        }
        self.assertEqual(expected, result)

    def test__run_interface_no_interface_not_mapped(self):
        variables = copy.deepcopy(self.variables)
        del variables["bar_interface"]
        module = self._create_module(variables)
        interfaces = [{
            "var_name": "kolla_bar_interface",
            "network": "bar",
            "description": "Bar network",
            "required": True,
        }, {
            "var_name": "kolla_baz_interface",
            "network": "baz",
            "description": "Baz network",
            "required": True,
        }]
        result = module._run(interfaces, [])
        expected = {
            "changed": False,
            "failed": True,
            "msg": ("Required network 'bar' (Bar network) does not have an "
                    "interface configured for this host; Required network "
                    "'baz' (Baz network) is not mapped to this host"),
        }
        self.assertEqual(expected, result)

    def test_run_external_networks_one(self):
        module = self._create_module()
        external_networks = [{
            "network": "foo",
            "required": False,
        }]
        result = module._run([], external_networks)
        expected = {
            "changed": False,
            "ansible_facts": {
                "kolla_neutron_bridge_names": "eth0-ovs",
                "kolla_neutron_external_interfaces": "eth0",
            },
            "_ansible_facts_cacheable": False,
        }
        self.assertEqual(expected, result)

    def test_run_external_networks_one_with_physnet(self):
        variables = copy.deepcopy(self.variables)
        variables["foo_physical_network"] = "custom1"
        module = self._create_module(variables)
        external_networks = [{
            "network": "foo",
            "required": False,
        }]
        result = module._run([], external_networks)
        expected = {
            "changed": False,
            "ansible_facts": {
                "kolla_neutron_bridge_names": "eth0-ovs",
                "kolla_neutron_external_interfaces": "eth0",
                "kolla_neutron_physical_networks": "custom1",
            },
            "_ansible_facts_cacheable": False,
        }
        self.assertEqual(expected, result)

    def test_run_external_networks_two(self):
        module = self._create_module()
        external_networks = [{
            "network": "foo",
            "required": False,
        }, {
            "network": "bar",
            "required": False,
        }]
        result = module._run([], external_networks)
        expected = {
            "changed": False,
            "ansible_facts": {
                "kolla_neutron_bridge_names": "eth0-ovs,eth1-ovs",
                "kolla_neutron_external_interfaces": "eth0,eth1",
            },
            "_ansible_facts_cacheable": False,
        }
        self.assertEqual(expected, result)

    def test_run_external_networks_two_with_physnet(self):
        variables = copy.deepcopy(self.variables)
        variables["foo_physical_network"] = "custom1"
        variables["bar_physical_network"] = "custom2"
        module = self._create_module(variables)
        external_networks = [{
            "network": "foo",
            "required": False,
        }, {
            "network": "bar",
            "required": False,
        }]
        result = module._run([], external_networks)
        expected = {
            "changed": False,
            "ansible_facts": {
                "kolla_neutron_bridge_names": "eth0-ovs,eth1-ovs",
                "kolla_neutron_external_interfaces": "eth0,eth1",
                "kolla_neutron_physical_networks": "custom1,custom2",
            },
            "_ansible_facts_cacheable": False,
        }
        self.assertEqual(expected, result)

    def test_run_external_networks_two_with_one_physnet(self):
        variables = copy.deepcopy(self.variables)
        variables["foo_physical_network"] = "custom1"
        module = self._create_module(variables)
        external_networks = [{
            "network": "foo",
            "required": False,
        }, {
            "network": "bar",
            "required": False,
        }]
        result = module._run([], external_networks)
        expected = {
            "changed": False,
            "failed": True,
            "msg": ("Some external networks have a 'physical_network' "
                    "attribute defined but the following do not: bar"),
        }
        self.assertEqual(expected, result)

    def test_run_external_networks_two_same_interface(self):
        variables = copy.deepcopy(self.variables)
        variables["bar_interface"] = "eth0"
        module = self._create_module(variables)
        external_networks = [{
            "network": "foo",
            "required": False,
        }, {
            "network": "bar",
            "required": False,
        }]
        result = module._run([], external_networks)
        expected = {
            "changed": False,
            "ansible_facts": {
                "kolla_neutron_bridge_names": "eth0-ovs",
                "kolla_neutron_external_interfaces": "eth0",
            },
            "_ansible_facts_cacheable": False,
        }
        self.assertEqual(expected, result)

    def test_run_external_networks_two_same_interface_with_physnet(self):
        variables = copy.deepcopy(self.variables)
        variables["bar_interface"] = "eth0"
        variables["foo_physical_network"] = "custom1"
        module = self._create_module(variables)
        external_networks = [{
            "network": "foo",
            "required": False,
        }, {
            "network": "bar",
            "required": False,
        }]
        result = module._run([], external_networks)
        expected = {
            "changed": False,
            "ansible_facts": {
                "kolla_neutron_bridge_names": "eth0-ovs",
                "kolla_neutron_external_interfaces": "eth0",
                "kolla_neutron_physical_networks": "custom1",
            },
            "_ansible_facts_cacheable": False,
        }
        self.assertEqual(expected, result)

    def test_run_external_networks_two_same_interface_with_different_physnets(
            self):
        variables = copy.deepcopy(self.variables)
        variables["bar_interface"] = "eth0"
        variables["foo_physical_network"] = "custom1"
        variables["bar_physical_network"] = "custom2"
        module = self._create_module(variables)
        external_networks = [{
            "network": "foo",
            "required": False,
        }, {
            "network": "bar",
            "required": False,
        }]
        result = module._run([], external_networks)
        expected = {
            "changed": False,
            "failed": True,
            "msg": ("Inconsistent 'physical_network' attributes for external "
                    "networks foo, bar using interface eth0: custom1, "
                    "custom2"),
        }
        self.assertEqual(expected, result)

    def test_run_external_networks_two_vlans(self):
        variables = copy.deepcopy(self.variables)
        variables["foo_interface"] = "eth0.1"
        variables["bar_interface"] = "eth0.2"
        module = self._create_module(variables)
        external_networks = [{
            "network": "foo",
            "required": False,
        }, {
            "network": "bar",
            "required": False,
        }]
        result = module._run([], external_networks)
        expected = {
            "changed": False,
            "ansible_facts": {
                "kolla_neutron_bridge_names": "eth0-ovs",
                "kolla_neutron_external_interfaces": "eth0",
            },
            "_ansible_facts_cacheable": False,
        }
        self.assertEqual(expected, result)

    def test_run_external_networks_bridge(self):
        variables = copy.deepcopy(self.variables)
        variables["foo_interface"] = "breth0"
        module = self._create_module(variables)
        external_networks = [{
            "network": "foo",
            "required": False,
        }]
        result = module._run([], external_networks)
        expected = {
            "changed": False,
            "ansible_facts": {
                "kolla_neutron_bridge_names": "breth0-ovs",
                "kolla_neutron_external_interfaces": "p-breth0-ovs",
            },
            "_ansible_facts_cacheable": False,
        }
        self.assertEqual(expected, result)

    def test_run_external_networks_bridge_vlan(self):
        variables = copy.deepcopy(self.variables)
        variables["foo_interface"] = "breth0.1"
        variables["bar_interface"] = "breth0"
        module = self._create_module(variables)
        external_networks = [{
            "network": "foo",
            "required": False,
        }]
        result = module._run([], external_networks)
        expected = {
            "changed": False,
            "ansible_facts": {
                "kolla_neutron_bridge_names": "breth0-ovs",
                "kolla_neutron_external_interfaces": "p-breth0-ovs",
            },
            "_ansible_facts_cacheable": False,
        }
        self.assertEqual(expected, result)

    def test_run_external_networks_not_mapped(self):
        module = self._create_module()
        external_networks = [{
            "network": "baz",
            "required": True,
        }]
        result = module._run([], external_networks)
        expected = {
            "changed": False,
            "failed": True,
            "msg": ("Required external network 'baz' is not mapped to "
                    "this host"),
        }
        self.assertEqual(expected, result)

    def test_run_external_networks_not_mapped_not_required(self):
        module = self._create_module()
        external_networks = [{
            "network": "baz",
            "required": False,
        }]
        result = module._run([], external_networks)
        expected = {
            "changed": False,
            "ansible_facts": {},
            "_ansible_facts_cacheable": False,
        }
        self.assertEqual(expected, result)

    def test_run_external_networks_no_interface(self):
        variables = copy.deepcopy(self.variables)
        del variables["bar_interface"]
        module = self._create_module(variables)
        external_networks = [{
            "network": "bar",
            "required": True,
        }]
        result = module._run([], external_networks)
        expected = {
            "changed": False,
            "failed": True,
            "msg": ("Required external network 'bar' does not have an "
                    "interface configured for this host"),
        }
        self.assertEqual(expected, result)

    def test_run_external_networks_no_interface_not_required(self):
        variables = copy.deepcopy(self.variables)
        del variables["bar_interface"]
        module = self._create_module(variables)
        external_networks = [{
            "network": "bar",
            "required": False,
        }]
        result = module._run([], external_networks)
        expected = {
            "changed": False,
            "ansible_facts": {},
            "_ansible_facts_cacheable": False,
        }
        self.assertEqual(expected, result)

    def test_run_external_networks_not_mapped_no_interface(self):
        variables = copy.deepcopy(self.variables)
        del variables["bar_interface"]
        module = self._create_module(variables)
        external_networks = [{
            "network": "baz",
            "required": True,
        }, {
            "network": "bar",
            "required": True,
        }]
        result = module._run([], external_networks)
        expected = {
            "changed": False,
            "failed": True,
            "msg": ("Required external network 'baz' is not mapped to "
                    "this host; Required external network 'bar' does not "
                    "have an interface configured for this host"),
        }
        self.assertEqual(expected, result)
