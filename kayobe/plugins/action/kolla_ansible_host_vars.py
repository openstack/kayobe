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

# TODO(dougszu): From Ansible 12 onwards we must explicitly trust templates.
# Since this feature is not supported in previous releases, we define a
# noop method here for backwards compatibility. This can be removed in the
# G cycle.
try:
    from ansible.template import trust_as_template
except ImportError:
    def trust_as_template(template):
        return template


class ConfigError(Exception):
    pass


class ActionModule(ActionBase):
    """Kolla Ansible host vars action plugin

    This class provides an Ansible action module that returns facts
    representing host variables to be passed to Kolla Ansible.
    """

    TRANSFERS_FILES = False

    def trusted_template(self, input):
        # Mark all input as trusted.
        trusted_input = trust_as_template(input)
        return self._templar.template(trusted_input)

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

        # Build a dict mapping external network interfaces to a list of Kayobe
        # network names that they provide connectivity for.
        external_interfaces = {}
        for network in external_networks:
            try:
                iface = self._get_external_interface(network["network"],
                                                     network["required"])
                if iface:
                    iface_networks = external_interfaces.get(iface, [])
                    if network["network"] not in iface_networks:
                        iface_networks.append(network["network"])
                    external_interfaces[iface] = iface_networks
            except ConfigError as e:
                errors.append(str(e))

        if external_interfaces:
            try:
                facts.update(self._get_external_interface_facts(
                    external_interfaces))
            except ConfigError as e:
                errors.append(str(e))

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
        condition = self.trusted_template(condition)
        if condition:
            # Get the network interface for this network.
            iface = ("{{ '%s' | net_interface }}" % net_name)
            iface = self.trusted_template(iface)
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
        condition = self.trusted_template(condition)
        if condition:
            iface = self.trusted_template("{{ '%s' | net_interface }}" %
                                          net_name)
            if iface:
                # When these networks are VLANs, we need to use the
                # underlying tagged bridge interface rather than the
                # untagged interface. We therefore strip the .<vlan> suffix
                # of the interface name. We use a union here as a single
                # tagged interface may be shared between these networks.
                vlan = self.trusted_template("{{ '%s' | net_vlan }}" %
                                             net_name)
                parent = self.trusted_template("{{ '%s' | net_parent }}" %
                                               net_name)
                if vlan and parent:
                    iface = parent
                elif vlan and iface.endswith(".%s" % vlan):
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
        neutron_physical_networks = []
        missing_physical_networks = []
        bridge_suffix = self.trusted_template(
            "{{ network_bridge_suffix_ovs }}")
        patch_prefix = self.trusted_template("{{ network_patch_prefix }}")
        patch_suffix = self.trusted_template("{{ network_patch_suffix_ovs }}")
        for interface, iface_networks in external_interfaces.items():
            is_bridge = ("{{ '%s' in (network_interfaces |"
                         "net_select_bridges |"
                         "map('net_interface')) }}" % interface)
            is_bridge = self.trusted_template(is_bridge)
            neutron_bridge_names.append(interface + bridge_suffix)
            # For a bridge, use a veth pair connected to the bridge. Otherwise
            # use the interface directly.
            if is_bridge:
                # interface names can't be longer than 15 characters
                char_limit = 15 - len(patch_prefix) - len(patch_suffix)
                external_interface = patch_prefix + interface[:char_limit] + \
                    patch_suffix
            else:
                external_interface = interface
            neutron_external_interfaces.append(external_interface)
            # One external network interface may be referenced by multiple
            # external networks. Check if they have a physical_network
            # attribute set, and if so, whether they are consistent.
            iface_physical_networks = []
            for iface_network in iface_networks:
                physical_network = self.trusted_template(
                    "{{ '%s' | net_physical_network }}" % iface_network)
                if (physical_network and
                        physical_network not in iface_physical_networks):
                    iface_physical_networks.append(physical_network)
            if iface_physical_networks:
                if len(iface_physical_networks) > 1:
                    raise ConfigError(
                        "Inconsistent 'physical_network' attributes for "
                        "external networks %s using interface %s: %s" %
                        (", ".join(iface_networks), interface,
                         ", ".join(iface_physical_networks)))
                neutron_physical_networks += iface_physical_networks
            else:
                missing_physical_networks += iface_networks
        facts = {
            "kolla_neutron_bridge_names": ",".join(neutron_bridge_names),
            "kolla_neutron_external_interfaces": ",".join(
                neutron_external_interfaces),
        }
        if neutron_physical_networks:
            if missing_physical_networks:
                raise ConfigError(
                    "Some external networks have a 'physical_network' "
                    "attribute defined but the following do not: %s" %
                    ", ".join(missing_physical_networks))

            facts["kolla_neutron_physical_networks"] = ",".join(
                neutron_physical_networks)
        return facts
