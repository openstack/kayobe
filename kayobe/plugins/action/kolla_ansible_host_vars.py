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

from ansible.plugins.action import ActionBase


class ConfigError(Exception):
    pass


class ActionModule(ActionBase):
    """Kolla Ansible host vars action plugin

    This class provides an Ansible action module that returns facts
    representing host variables to be passed to Kolla Ansible.
    """

    TRANSFERS_FILES = False

    def run(self, tmp=None, task_vars=None):
        if task_vars is None:
            task_vars = dict()

        result = super(ActionModule, self).run(tmp, task_vars)
        del tmp  # tmp no longer has any effect

        # Module arguments:
        # interfaces: a list of dicts, each containing 'network', 'required',
        #             and 'description' keys. Each describes a Kolla Ansible
        #             interface variable.
        # external_networks: a list of dicts, each containing 'network', and
        #                    'required' keys. Each describes an external
        #                    network.
        interfaces = self._task.args["interfaces"]
        external_networks = self._task.args.get('external_networks', [])
        result.update(self._run(interfaces, external_networks))
        return result

    def _run(self, interfaces, external_networks):
        result = {}
        facts = {}
        errors = []

        # Kolla Ansible interface facts.
        for interface in interfaces:
            try:
                iface = self._get_interface_fact(interface["network"],
                                                 interface["required"],
                                                 interface["description"])
                if iface:
                    facts[interface["var_name"]] = iface
            except ConfigError as e:
                errors.append(str(e))

        # Build a list of external network interfaces.
        external_interfaces = []
        for network in external_networks:
            try:
                iface = self._get_external_interface(network["network"],
                                                     network["required"])
                if iface and iface not in external_interfaces:
                    external_interfaces.append(iface)
            except ConfigError as e:
                errors.append(str(e))

        if external_interfaces:
            facts.update(self._get_external_interface_facts(
                external_interfaces))

        result['changed'] = False
        if errors:
            result['failed'] = True
            result['msg'] = "; ".join(errors)
        else:
            result['ansible_facts'] = facts
            result['_ansible_facts_cacheable'] = False
        return result

    def _get_interface_fact(self, net_name, required, description):
        # Check whether the network is mapped to this host.
        condition = "{{ '%s' in network_interfaces }}" % net_name
        condition = self._templar.template(condition)
        if condition:
            # Get the network interface for this network.
            iface = ("{{ '%s' | net_interface }}" % net_name)
            iface = self._templar.template(iface)
            if iface:
                # Ansible fact names replace dashes with underscores.
                # FIXME(mgoddard): Is this still required?
                iface = iface.replace('-', '_')
            if required and not iface:
                msg = ("Required network '%s' (%s) does not have an interface "
                       "configured for this host" % (net_name, description))
                raise ConfigError(msg)
            return iface
        elif required:
            msg = ("Required network '%s' (%s) is not mapped to this host" %
                   (net_name, description))
            raise ConfigError(msg)

    def _get_external_interface(self, net_name, required):
        condition = "{{ '%s' in network_interfaces }}" % net_name
        condition = self._templar.template(condition)
        if condition:
            iface = self._templar.template("{{ '%s' | net_interface }}" %
                                           net_name)
            if iface:
                # When these networks are VLANs, we need to use the
                # underlying tagged bridge interface rather than the
                # untagged interface. We therefore strip the .<vlan> suffix
                # of the interface name. We use a union here as a single
                # tagged interface may be shared between these networks.
                vlan = self._templar.template("{{ '%s' | net_vlan }}" %
                                              net_name)
                if vlan and iface.endswith(".%s" % vlan):
                    iface = iface.replace(".%s" % vlan, "")
                return iface
            elif required:
                raise ConfigError("Required external network '%s' does not "
                                  "have an interface configured for this host"
                                  % net_name)
        elif required:
            raise ConfigError("Required external network '%s' is not mapped "
                              "to this host" % net_name)

    def _get_external_interface_facts(self, external_interfaces):
        neutron_bridge_names = []
        neutron_external_interfaces = []
        bridge_suffix = self._templar.template(
            "{{ network_bridge_suffix_ovs }}")
        patch_prefix = self._templar.template("{{ network_patch_prefix }}")
        patch_suffix = self._templar.template("{{ network_patch_suffix_ovs }}")
        for interface in external_interfaces:
            is_bridge = ("{{ '%s' in (network_interfaces |"
                         "net_select_bridges |"
                         "map('net_interface')) }}" % interface)
            is_bridge = self._templar.template(is_bridge)
            neutron_bridge_names.append(interface + bridge_suffix)
            # For a bridge, use a veth pair connected to the bridge. Otherwise
            # use the interface directly.
            if is_bridge:
                external_interface = patch_prefix + interface + patch_suffix
            else:
                external_interface = interface
            neutron_external_interfaces.append(external_interface)
        return {
            "kolla_neutron_bridge_names": ",".join(neutron_bridge_names),
            "kolla_neutron_external_interfaces": ",".join(
                neutron_external_interfaces),
        }
