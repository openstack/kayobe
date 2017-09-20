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

import json
import sys

from cliff.command import Command

from kayobe import ansible
from kayobe import kolla_ansible
from kayobe import utils
from kayobe import vault


def _build_playbook_list(*playbooks):
    """Return a list of names of playbook files given their basenames."""
    return ["ansible/%s.yml" % playbook for playbook in playbooks]


class VaultMixin(object):
    """Mixin class for commands requiring Ansible vault."""

    def get_parser(self, prog_name):
        parser = super(VaultMixin, self).get_parser(prog_name)
        group = parser.add_argument_group("Ansible vault")
        vault.add_args(group)
        return parser


class KayobeAnsibleMixin(object):
    """Mixin class for commands running Kayobe Ansible playbooks."""

    def get_parser(self, prog_name):
        parser = super(KayobeAnsibleMixin, self).get_parser(prog_name)
        group = parser.add_argument_group("Kayobe Ansible")
        self.add_kayobe_ansible_args(group)
        return parser

    def add_kayobe_ansible_args(self, group):
        ansible.add_args(group)

    def _get_verbosity_args(self):
        """Add quietness and verbosity level arguments."""
        # Cliff's default verbosity level is 1, 0 means quiet.
        verbosity_args = {}
        if self.app.options.verbose_level:
            ansible_verbose_level = self.app.options.verbose_level - 1
            verbosity_args["verbose_level"] = ansible_verbose_level
        else:
            verbosity_args["quiet"] = True
        return verbosity_args

    def run_kayobe_playbooks(self, *args, **kwargs):
        kwargs.update(self._get_verbosity_args())
        return ansible.run_playbooks(*args, **kwargs)

    def run_kayobe_playbook(self, *args, **kwargs):
        kwargs.update(self._get_verbosity_args())
        return ansible.run_playbook(*args, **kwargs)

    def run_kayobe_config_dump(self, *args, **kwargs):
        kwargs.update(self._get_verbosity_args())
        return ansible.config_dump(*args, **kwargs)


class KollaAnsibleMixin(object):
    """Mixin class for commands running Kolla Ansible."""

    def get_parser(self, prog_name):
        parser = super(KollaAnsibleMixin, self).get_parser(prog_name)
        group = parser.add_argument_group("Kolla Ansible")
        self.add_kolla_ansible_args(group)
        return parser

    def add_kolla_ansible_args(self, group):
        kolla_ansible.add_args(group)

    def _get_verbosity_args(self):
        """Add quietness and verbosity level arguments."""
        # Cliff's default verbosity level is 1, 0 means quiet.
        verbosity_args = {}
        if self.app.options.verbose_level:
            ansible_verbose_level = self.app.options.verbose_level - 1
            verbosity_args["verbose_level"] = ansible_verbose_level
        else:
            verbosity_args["quiet"] = True
        return verbosity_args

    def run_kolla_ansible(self, *args, **kwargs):
        kwargs.update(self._get_verbosity_args())
        return kolla_ansible.run(*args, **kwargs)

    def run_kolla_ansible_overcloud(self, *args, **kwargs):
        kwargs.update(self._get_verbosity_args())
        return kolla_ansible.run_overcloud(*args, **kwargs)

    def run_kolla_ansible_seed(self, *args, **kwargs):
        kwargs.update(self._get_verbosity_args())
        return kolla_ansible.run_seed(*args, **kwargs)


class ControlHostBootstrap(KayobeAnsibleMixin, VaultMixin, Command):
    """Bootstrap the Kayobe control environment.

    * Downloads and installs Ansible roles from Galaxy.
    * Generates an SSH key for the ansible control host, if one does not exist.
    * Installs kolla-ansible on the ansible control host.
    """

    def take_action(self, parsed_args):
        self.app.LOG.debug("Bootstrapping Kayobe control host")
        utils.galaxy_install("ansible/requirements.yml", "ansible/roles")
        playbooks = _build_playbook_list("bootstrap")
        self.run_kayobe_playbooks(parsed_args, playbooks)
        playbooks = _build_playbook_list("kolla-ansible")
        self.run_kayobe_playbooks(parsed_args, playbooks, tags="install")


class ControlHostUpgrade(KayobeAnsibleMixin, VaultMixin, Command):
    """Upgrade the Kayobe control environment.

    * Downloads and installs updated Ansible roles from Galaxy.
    * Generates an SSH key for the ansible control host, if one does not exist.
    * Updates kolla-ansible on the ansible control host.
    """

    def take_action(self, parsed_args):
        self.app.LOG.debug("Upgrading Kayobe control host")
        # Use force to upgrade roles.
        utils.galaxy_install("ansible/requirements.yml", "ansible/roles",
                             force=True)
        playbooks = _build_playbook_list("bootstrap")
        self.run_kayobe_playbooks(parsed_args, playbooks)
        playbooks = _build_playbook_list("kolla-ansible")
        self.run_kayobe_playbooks(parsed_args, playbooks, tags="install")


class ConfigurationDump(KayobeAnsibleMixin, VaultMixin, Command):
    """Dump Kayobe configuration.

    Dumps kayobe Ansible host variables to standard output. The output may be
    filtered by selecting one or more hosts, or a specific variable.
    """

    def get_parser(self, prog_name):
        parser = super(ConfigurationDump, self).get_parser(prog_name)
        group = parser.add_argument_group("Configuration Dump")
        group.add_argument("--dump-facts", default=False,
                           help="whether to gather and dump host facts")
        group.add_argument("--host",
                           help="name of a host to dump config for")
        group.add_argument("--hosts",
                           help="name of hosts and/or groups to dump config "
                                "for")
        group.add_argument("--var-name",
                           help="name of a variable to dump")
        return parser

    def take_action(self, parsed_args):
        self.app.LOG.debug("Dumping Ansible configuration")
        hostvars = self.run_kayobe_config_dump(
            parsed_args, host=parsed_args.host, hosts=parsed_args.hosts,
            facts=parsed_args.dump_facts, var_name=parsed_args.var_name)
        try:
            json.dump(hostvars, sys.stdout, sort_keys=True, indent=4)
        except TypeError as e:
            self.app.LOG.error("Failed to JSON encode configuration: %s",
                               repr(e))
            sys.exit(1)


class PlaybookRun(KayobeAnsibleMixin, VaultMixin, Command):
    """Run a Kayobe Ansible playbook.

    Allows a single Kayobe ansible playbook to be run. For advanced users only.
    """

    def add_kayobe_ansible_args(self, group):
        super(PlaybookRun, self).add_kayobe_ansible_args(group)
        group.add_argument("playbook", nargs="+",
                           help="name of the playbook(s) to run")

    def take_action(self, parsed_args):
        self.app.LOG.debug("Running Kayobe playbook(s)")
        self.run_kayobe_playbooks(parsed_args, parsed_args.playbook)


class KollaAnsibleRun(KollaAnsibleMixin, VaultMixin, Command):
    """Run a Kolla Ansible command.

    Allows a single kolla-ansible command to be run. For advanced users only.
    """

    def add_kolla_ansible_args(self, group):
        super(KollaAnsibleRun, self).add_kolla_ansible_args(group)
        group.add_argument("--kolla-inventory-filename", default="overcloud",
                           choices=["seed", "overcloud"],
                           help="name of the kolla-ansible inventory file, "
                                "one of seed or overcloud (default "
                                "overcloud)")
        group.add_argument("command",
                           help="name of the kolla-ansible command to run")

    def take_action(self, parsed_args):
        self.app.LOG.debug("Running Kolla Ansible command")
        self.run_kolla_ansible(parsed_args, parsed_args.command,
                               parsed_args.kolla_inventory_filename)


class PhysicalNetworkConfigure(KayobeAnsibleMixin, VaultMixin, Command):
    """Configure a set of physical network devices."""

    def get_parser(self, prog_name):
        parser = super(PhysicalNetworkConfigure, self).get_parser(
            prog_name)
        group = parser.add_argument_group("Physical Networking")
        group.add_argument("--group", required=True,
                           help="the Ansible group to apply configuration to")
        group.add_argument("--enable-discovery", action="store_true",
                           help="configure the network for hardware discovery")
        return parser

    def take_action(self, parsed_args):
        self.app.LOG.debug("Configuring a physical network")
        extra_vars = {}
        if parsed_args.enable_discovery:
            extra_vars["physical_network_enable_discovery"] = True
        self.run_kayobe_playbook(parsed_args, "ansible/physical-network.yml",
                                 limit=parsed_args.group,
                                 extra_vars=extra_vars)


class SeedHypervisorHostConfigure(KollaAnsibleMixin, KayobeAnsibleMixin,
                                  VaultMixin, Command):
    """Configure the seed hypervisor node host OS and services.

    * Allocate IP addresses for all configured networks.
    * Add the host to SSH known hosts.
    * Configure user accounts, group associations, and authorised SSH keys.
    * Configure the host's network interfaces.
    * Set sysctl parameters.
    * Configure NTP.
    * Configure the host as a libvirt hypervisor.
    """

    def take_action(self, parsed_args):
        self.app.LOG.debug("Configuring seed hypervisor host OS")
        playbooks = _build_playbook_list(
            "ip-allocation", "ssh-known-host", "users", "dev-tools", "network",
            "sysctl", "ntp", "seed-hypervisor-libvirt-host")
        self.run_kayobe_playbooks(parsed_args, playbooks,
                                  limit="seed-hypervisor")


class SeedVMProvision(KollaAnsibleMixin, KayobeAnsibleMixin, VaultMixin,
                      Command):
    """Provision the seed VM.

    * Allocate IP addresses for all configured networks.
    * Provision a virtual machine using libvirt.
    * Configure the kolla-ansible inventory for the seed VM.
    """

    def take_action(self, parsed_args):
        self.app.LOG.debug("Provisioning seed VM")
        self.run_kayobe_playbook(parsed_args, "ansible/ip-allocation.yml",
                                 limit="seed")
        self.run_kayobe_playbook(parsed_args, "ansible/seed-vm-provision.yml")
        # Now populate the Kolla Ansible inventory.
        self.run_kayobe_playbook(parsed_args, "ansible/kolla-ansible.yml",
                                 tags="config")


class SeedVMDeprovision(KollaAnsibleMixin, KayobeAnsibleMixin, VaultMixin,
                        Command):
    """Deprovision the seed VM.

    This will destroy the seed VM and all associated volumes.
    """

    def take_action(self, parsed_args):
        self.app.LOG.debug("Deprovisioning seed VM")
        self.run_kayobe_playbook(parsed_args,
                                 "ansible/seed-vm-deprovision.yml")


class SeedHostConfigure(KollaAnsibleMixin, KayobeAnsibleMixin, VaultMixin,
                        Command):
    """Configure the seed node host OS and services.

    * Allocate IP addresses for all configured networks.
    * Add the host to SSH known hosts.
    * Configure a user account for use by kayobe for SSH access.
    * Optionally, wipe unmounted disk partitions (--wipe-disks).
    * Configure user accounts, group associations, and authorised SSH keys.
    * Disable SELinux.
    * Configure the host's network interfaces.
    * Set sysctl parameters.
    * Configure IP routing and source NAT.
    * Disable bootstrap interface configuration.
    * Configure NTP.
    * Configure LVM volumes.
    * Configure a user account for kolla-ansible.
    * Configure Docker engine.
    """

    def get_parser(self, prog_name):
        parser = super(SeedHostConfigure, self).get_parser(prog_name)
        group = parser.add_argument_group("Host Configuration")
        group.add_argument("--wipe-disks", action='store_true',
                           help="wipe partition and LVM data from all disks "
                                "that are not mounted. Warning: this can "
                                "result in the loss of data")
        return parser

    def take_action(self, parsed_args):
        self.app.LOG.debug("Configuring seed host OS")
        ansible_user = self.run_kayobe_config_dump(
            parsed_args, host="seed", var_name="kayobe_ansible_user")
        if not ansible_user:
            self.app.LOG.error("Could not determine kayobe_ansible_user "
                               "variable for seed host")
            sys.exit(1)
        playbooks = _build_playbook_list(
            "ip-allocation", "ssh-known-host", "kayobe-ansible-user")
        if parsed_args.wipe_disks:
            playbooks += _build_playbook_list("wipe-disks")
        playbooks += _build_playbook_list(
            "users", "dev-tools", "disable-selinux", "network", "sysctl",
            "ip-routing", "snat", "disable-glean", "ntp", "lvm")
        self.run_kayobe_playbooks(parsed_args, playbooks, limit="seed")
        playbooks = _build_playbook_list("kolla-ansible")
        self.run_kayobe_playbooks(parsed_args, playbooks, tags="config")
        self.run_kolla_ansible_seed(parsed_args, "bootstrap-servers",
                                    extra_vars={"ansible_user": ansible_user})
        playbooks = _build_playbook_list("kolla-host", "docker")
        self.run_kayobe_playbooks(parsed_args, playbooks, limit="seed")


class SeedServiceDeploy(KollaAnsibleMixin, KayobeAnsibleMixin, VaultMixin,
                        Command):
    """Deploy the seed services.

    * Configures kolla-ansible.
    * Configures the bifrost service.
    * Deploys the bifrost container using kolla-ansible.
    * Builds disk images for the overcloud hosts using Diskimage Builder (DIB).
    * Configures ironic inspector introspection rules in the bifrost inspector
      service.
    * When enabled, configures a Bare Metal Provisioning (BMP) environment for
      Dell Force10 switches, hosted by the bifrost dnsmasq and nginx services.
    """

    def take_action(self, parsed_args):
        self.app.LOG.debug("Deploying seed services")
        playbooks = _build_playbook_list("kolla-ansible")
        self.run_kayobe_playbooks(parsed_args, playbooks, tags="config")

        self.run_kayobe_playbook(parsed_args, "ansible/kolla-bifrost.yml")
        self.run_kolla_ansible_seed(parsed_args, "deploy-bifrost")
        playbooks = _build_playbook_list(
            "seed-introspection-rules", "dell-switch-bmp")
        self.run_kayobe_playbooks(parsed_args, playbooks)


class SeedContainerImageBuild(KayobeAnsibleMixin, VaultMixin, Command):
    """Build the seed container images.

    * Installs and configures kolla build environment on the seed.
    * Builds container images for the seed services.
    """

    def get_parser(self, prog_name):
        parser = super(SeedContainerImageBuild, self).get_parser(
            prog_name)
        group = parser.add_argument_group("Container Image Build")
        group.add_argument("--push", action="store_true",
                           help="whether to push images to a registry after "
                                "building")
        group.add_argument("regex", nargs='*',
                           help="regular expression matching names of images "
                                "to build. Builds all images if unspecified")
        return parser

    def take_action(self, parsed_args):
        self.app.LOG.debug("Building seed container images")
        playbooks = _build_playbook_list(
            "kolla-build", "container-image-build")
        extra_vars = {"push_images": parsed_args.push}
        if parsed_args.regex:
            regexes = "'%s'" % " ".join(parsed_args.regex)
            extra_vars["container_image_regexes"] = regexes
        self.run_kayobe_playbooks(parsed_args, playbooks, limit="seed",
                                  extra_vars=extra_vars)


class SeedDeploymentImageBuild(KayobeAnsibleMixin, VaultMixin, Command):
    """Build the seed deployment kernel and ramdisk images.

    Builds Ironic Python Agent (IPA) deployment images using Diskimage Builder
    (DIB) for use when provisioning and inspecting the overcloud hosts.
    """

    def take_action(self, parsed_args):
        self.app.LOG.debug("Building seed deployment images")
        playbooks = _build_playbook_list("seed-ipa-build")
        self.run_kayobe_playbooks(parsed_args, playbooks)


class OvercloudInventoryDiscover(KayobeAnsibleMixin, VaultMixin, Command):
    """Discover the overcloud inventory from the seed's Ironic service.

    * Query the ironic inventory on the seed, and use this to populate kayobe's
      ansible inventory.
    * Allocate IP addresses for all configured networks.
    * Configure the bifrost service with host variables for provisioning the
      overcloud hosts.
    * Update the kolla-ansible configuration for the new overcloud hosts.
    """

    def take_action(self, parsed_args):
        self.app.LOG.debug("Discovering overcloud inventory")
        # Run the inventory discovery playbook separately, else the discovered
        # hosts will not be present in the following playbooks in which they
        # are used to populate other inventories.
        self.run_kayobe_playbook(parsed_args,
                                 "ansible/overcloud-inventory-discover.yml")
        # If necessary, allocate IP addresses for the discovered hosts.
        self.run_kayobe_playbook(parsed_args,
                                 "ansible/ip-allocation.yml")
        # Now populate the Kolla Ansible and Bifrost inventories.
        self.run_kayobe_playbook(parsed_args,
                                 "ansible/kolla-bifrost-hostvars.yml")
        self.run_kayobe_playbook(parsed_args, "ansible/kolla-ansible.yml",
                                 tags="config")


class OvercloudIntrospectionDataSave(KayobeAnsibleMixin, VaultMixin, Command):
    """Save hardware introspection data for the overcloud.

    Save hardware introspection data from the seed's ironic inspector service
    to the control host.
    """

    def get_parser(self, prog_name):
        parser = super(OvercloudIntrospectionDataSave, self).get_parser(
            prog_name)
        group = parser.add_argument_group("Introspection data")
        # Defaults for these are applied in the playbook.
        group.add_argument("--output-dir", type=str,
                           help="Path to directory in which to save "
                                "introspection data. Default: "
                                "$PWD/overcloud-introspection-data")
        group.add_argument("--output-format", type=str,
                           help="Format in which to save output data. One of "
                                "JSON or YAML. Default: JSON",
                           choices=["JSON", "YAML"])
        return parser

    def take_action(self, parsed_args):
        self.app.LOG.debug("Saving introspection data")
        extra_vars = {}
        if parsed_args.output_dir:
            extra_vars['output_dir'] = parsed_args.output_dir
        if parsed_args.output_format:
            extra_vars['output_format'] = parsed_args.output_format
        playbooks = _build_playbook_list("overcloud-introspection-data-save")
        self.run_kayobe_playbooks(parsed_args, playbooks,
                                  extra_vars=extra_vars)


class OvercloudBIOSRAIDConfigure(KayobeAnsibleMixin, VaultMixin, Command):
    """Configure BIOS and RAID for the overcloud hosts."""

    def take_action(self, parsed_args):
        self.app.LOG.debug("Configure overcloud BIOS and RAID")
        playbooks = _build_playbook_list("overcloud-bios-raid")
        self.run_kayobe_playbooks(parsed_args, playbooks)


class OvercloudHardwareInspect(KayobeAnsibleMixin, VaultMixin, Command):
    """Inspect the overcloud hardware using ironic inspector.

    Perform hardware inspection of existing ironic nodes in the seed's
    ironic inventory.
    """

    def take_action(self, parsed_args):
        self.app.LOG.debug("Inspecting overcloud")
        playbooks = _build_playbook_list("overcloud-hardware-inspect")
        self.run_kayobe_playbooks(parsed_args, playbooks)


class OvercloudProvision(KayobeAnsibleMixin, VaultMixin, Command):
    """Provision the overcloud.

    Provision the overcloud hosts using the seed host's bifrost service. This
    will image the hosts and perform some minimal network configuration using
    glean/simple-init.
    """

    def take_action(self, parsed_args):
        self.app.LOG.debug("Provisioning overcloud")
        playbooks = _build_playbook_list("overcloud-provision")
        self.run_kayobe_playbooks(parsed_args, playbooks)


class OvercloudDeprovision(KayobeAnsibleMixin, VaultMixin, Command):
    """Deprovision the overcloud.

    Deprovision the overcloud hosts using the seed host's bifrost service. This
    will clear the instance state of the nodes from the seed's ironic service
    and power them off.
    """

    def take_action(self, parsed_args):
        self.app.LOG.debug("Deprovisioning overcloud")
        playbooks = _build_playbook_list("overcloud-deprovision")
        self.run_kayobe_playbooks(parsed_args, playbooks)


class OvercloudHostConfigure(KollaAnsibleMixin, KayobeAnsibleMixin, VaultMixin,
                             Command):
    """Configure the overcloud host OS and services.

    * Allocate IP addresses for all configured networks.
    * Add the host to SSH known hosts.
    * Configure a user account for use by kayobe for SSH access.
    * Optionally, wipe unmounted disk partitions (--wipe-disks).
    * Configure user accounts, group associations, and authorised SSH keys.
    * Disable SELinux.
    * Configure the host's network interfaces.
    * Set sysctl parameters.
    * Disable bootstrap interface configuration.
    * Configure NTP.
    * Configure LVM volumes.
    * Configure a user account for kolla-ansible.
    * Configure Docker engine.
    """

    def get_parser(self, prog_name):
        parser = super(OvercloudHostConfigure, self).get_parser(prog_name)
        group = parser.add_argument_group("Host Configuration")
        group.add_argument("--wipe-disks", action='store_true',
                           help="wipe partition and LVM data from all disks "
                                "that are not mounted. Warning: this can "
                                "result in the loss of data")
        return parser

    def take_action(self, parsed_args):
        self.app.LOG.debug("Configuring overcloud host OS")
        ansible_user = self.run_kayobe_config_dump(
            parsed_args, hosts="overcloud", var_name="kayobe_ansible_user")
        if not ansible_user:
            self.app.LOG.error("Could not determine kayobe_ansible_user "
                               "variable for overcloud hosts")
            sys.exit(1)
        ansible_user = ansible_user.values()[0]
        playbooks = _build_playbook_list(
            "ip-allocation", "ssh-known-host", "kayobe-ansible-user")
        if parsed_args.wipe_disks:
            playbooks += _build_playbook_list("wipe-disks")
        playbooks += _build_playbook_list(
            "users", "dev-tools", "disable-selinux", "network", "sysctl",
            "disable-glean", "ntp", "lvm")
        self.run_kayobe_playbooks(parsed_args, playbooks, limit="overcloud")
        playbooks = _build_playbook_list("kolla-ansible")
        self.run_kayobe_playbooks(parsed_args, playbooks, tags="config")
        extra_vars = {"ansible_user": ansible_user}
        self.run_kolla_ansible_overcloud(parsed_args, "bootstrap-servers",
                                         extra_vars=extra_vars)
        playbooks = _build_playbook_list("kolla-host", "docker")
        self.run_kayobe_playbooks(parsed_args, playbooks, limit="overcloud")


class OvercloudHostUpgrade(KollaAnsibleMixin, KayobeAnsibleMixin, VaultMixin,
                           Command):
    """Upgrade the overcloud host services.

    Performs the changes necessary to make the host services suitable for the
    configured OpenStack release.
    """

    def take_action(self, parsed_args):
        self.app.LOG.debug("Upgrading overcloud host services")
        playbooks = _build_playbook_list(
            "overcloud-etc-hosts-fixup")
        self.run_kayobe_playbooks(parsed_args, playbooks)


class OvercloudServiceDeploy(KollaAnsibleMixin, KayobeAnsibleMixin, VaultMixin,
                             Command):
    """Deploy the overcloud services.

    * Configure kolla-ansible.
    * Configure overcloud services in kolla-ansible.
    * Perform kolla-ansible prechecks to verify the system state for
      deployment.
    * Perform a kolla-ansible deployment of the overcloud services.
    * Configure and deploy kayobe extra services.
    * Generate openrc files for the admin user.

    This can be used in conjunction with the --tags and --kolla-tags arguments
    to deploy specific services.
    """

    def get_parser(self, prog_name):
        parser = super(OvercloudServiceDeploy, self).get_parser(prog_name)
        group = parser.add_argument_group("Service Deployment")
        group.add_argument("--skip-prechecks", action='store_true',
                           help="skip the kolla-ansible prechecks command")
        return parser

    def take_action(self, parsed_args):
        self.app.LOG.debug("Deploying overcloud services")

        # First prepare configuration.
        playbooks = _build_playbook_list("kolla-ansible")
        self.run_kayobe_playbooks(parsed_args, playbooks, tags="config")

        playbooks = _build_playbook_list("kolla-openstack", "swift-setup")
        self.run_kayobe_playbooks(parsed_args, playbooks)

        # Run kolla-ansible prechecks before deployment.
        if not parsed_args.skip_prechecks:
            self.run_kolla_ansible_overcloud(parsed_args, "prechecks")

        # Perform the kolla-ansible deployment.
        self.run_kolla_ansible_overcloud(parsed_args, "deploy")

        # Deploy kayobe extra services.
        playbooks = _build_playbook_list("overcloud-extras")
        extra_vars = {"action": "deploy"}
        self.run_kayobe_playbooks(parsed_args, playbooks,
                                  extra_vars=extra_vars)

        # Post-deployment configuration.
        # FIXME: Fudge to work around incorrect configuration path.
        extra_vars = {"node_config_directory": parsed_args.kolla_config_path}
        self.run_kolla_ansible_overcloud(parsed_args, "post-deploy",
                                         extra_vars=extra_vars)
        # Create an environment file for accessing the public API as the admin
        # user.
        playbooks = _build_playbook_list("public-openrc")
        self.run_kayobe_playbooks(parsed_args, playbooks)


class OvercloudServiceReconfigure(KollaAnsibleMixin, KayobeAnsibleMixin,
                                  VaultMixin, Command):
    """Reconfigure the overcloud services.

    * Configure kolla-ansible.
    * Configure overcloud services in kolla-ansible.
    * Perform kolla-ansible prechecks to verify the system state for
      deployment.
    * Perform a kolla-ansible reconfiguration of the overcloud services.
    * Configure and deploy kayobe extra services.
    * Generate openrc files for the admin user.

    This can be used in conjunction with the --tags and --kolla-tags arguments
    to reconfigure specific services.
    """

    def get_parser(self, prog_name):
        parser = super(OvercloudServiceReconfigure, self).get_parser(prog_name)
        group = parser.add_argument_group("Service Reconfiguration")
        group.add_argument("--skip-prechecks", action='store_true',
                           help="skip the kolla-ansible prechecks command")
        return parser

    def take_action(self, parsed_args):
        self.app.LOG.debug("Reconfiguring overcloud services")

        # First prepare configuration.
        playbooks = _build_playbook_list("kolla-ansible")
        self.run_kayobe_playbooks(parsed_args, playbooks, tags="config")

        playbooks = _build_playbook_list("kolla-openstack", "swift-setup")
        self.run_kayobe_playbooks(parsed_args, playbooks)

        # Run kolla-ansible prechecks before reconfiguration.
        if not parsed_args.skip_prechecks:
            self.run_kolla_ansible_overcloud(parsed_args, "prechecks")

        # Perform the kolla-ansible reconfiguration.
        self.run_kolla_ansible_overcloud(parsed_args, "reconfigure")

        # Reconfigure kayobe extra services.
        playbooks = _build_playbook_list("overcloud-extras")
        extra_vars = {"action": "reconfigure"}
        self.run_kayobe_playbooks(parsed_args, playbooks,
                                  extra_vars=extra_vars)

        # Post-deployment configuration.
        # FIXME: Fudge to work around incorrect configuration path.
        extra_vars = {"node_config_directory": parsed_args.kolla_config_path}
        self.run_kolla_ansible_overcloud(parsed_args, "post-deploy",
                                         extra_vars=extra_vars)
        # Create an environment file for accessing the public API as the admin
        # user.
        playbooks = _build_playbook_list("public-openrc")
        self.run_kayobe_playbooks(parsed_args, playbooks)


class OvercloudServiceUpgrade(KollaAnsibleMixin, KayobeAnsibleMixin,
                              VaultMixin, Command):
    """Upgrade the overcloud services.

    * Configure kolla-ansible.
    * Configure overcloud services in kolla-ansible.
    * Perform kolla-ansible prechecks to verify the system state for
      deployment.
    * Perform a kolla-ansible upgrade of the overcloud services.
    * Configure and upgrade kayobe extra services.

    This can be used in conjunction with the --tags and --kolla-tags arguments
    to upgrade specific services.
    """

    def get_parser(self, prog_name):
        parser = super(OvercloudServiceUpgrade, self).get_parser(prog_name)
        group = parser.add_argument_group("Service Upgrade")
        group.add_argument("--skip-prechecks", action='store_true',
                           help="skip the kolla-ansible prechecks command")
        return parser

    def take_action(self, parsed_args):
        self.app.LOG.debug("Upgrading overcloud services")

        # First prepare configuration.
        playbooks = _build_playbook_list("kolla-ansible", "kolla-openstack")
        self.run_kayobe_playbooks(parsed_args, playbooks)

        # Run kolla-ansible prechecks before upgrade.
        if not parsed_args.skip_prechecks:
            self.run_kolla_ansible_overcloud(parsed_args, "prechecks")

        # Perform the kolla-ansible upgrade.
        self.run_kolla_ansible_overcloud(parsed_args, "upgrade")

        # Upgrade kayobe extra services.
        playbooks = _build_playbook_list("overcloud-extras")
        extra_vars = {"action": "upgrade"}
        self.run_kayobe_playbooks(parsed_args, playbooks,
                                  extra_vars=extra_vars)


class OvercloudServiceDestroy(KollaAnsibleMixin, KayobeAnsibleMixin,
                              VaultMixin, Command):
    """Destroy the overcloud services.

    Permanently destroy the overcloud containers, container images, and
    container volumes.
    """

    def get_parser(self, prog_name):
        parser = super(OvercloudServiceDestroy, self).get_parser(prog_name)
        group = parser.add_argument_group("Services")
        group.add_argument("--yes-i-really-really-mean-it",
                           action='store_true',
                           help="confirm that you understand that this will "
                                "permantently destroy all services and data.")
        return parser

    def take_action(self, parsed_args):
        if not parsed_args.yes_i_really_really_mean_it:
            self.app.LOG.error("This will permanently destroy all services "
                               "and data. Specify "
                               "--yes-i-really-really-mean-it to confirm that "
                               "you understand this.")
            sys.exit(1)

        self.app.LOG.debug("Destroying overcloud services")

        # First prepare configuration.
        playbooks = _build_playbook_list("kolla-ansible")
        self.run_kayobe_playbooks(parsed_args, playbooks, tags="config")

        playbooks = _build_playbook_list("kolla-openstack")
        self.run_kayobe_playbooks(parsed_args, playbooks)

        # Run kolla-ansible destroy.
        extra_args = ["--yes-i-really-really-mean-it"]
        self.run_kolla_ansible_overcloud(parsed_args, "destroy",
                                         extra_args=extra_args)

        # Destroy kayobe extra services.
        playbooks = _build_playbook_list("overcloud-extras")
        extra_vars = {"action": "destroy"}
        self.run_kayobe_playbooks(parsed_args, playbooks,
                                  extra_vars=extra_vars)


class OvercloudContainerImagePull(KayobeAnsibleMixin, KollaAnsibleMixin,
                                  VaultMixin, Command):
    """Pull the overcloud container images from a registry."""

    def take_action(self, parsed_args):
        self.app.LOG.debug("Pulling overcloud container images")

        # First prepare configuration.
        playbooks = _build_playbook_list("kolla-ansible")
        self.run_kayobe_playbooks(parsed_args, playbooks, tags="config")

        # Pull updated kolla container images.
        self.run_kolla_ansible_overcloud(parsed_args, "pull")

        # Pull container images for kayobe extra services.
        playbooks = _build_playbook_list("overcloud-extras")
        extra_vars = {"action": "pull"}
        self.run_kayobe_playbooks(parsed_args, playbooks,
                                  extra_vars=extra_vars)


class OvercloudContainerImageBuild(KayobeAnsibleMixin, VaultMixin, Command):
    """Build the overcloud container images."""

    def get_parser(self, prog_name):
        parser = super(OvercloudContainerImageBuild, self).get_parser(
            prog_name)
        group = parser.add_argument_group("Container Image Build")
        group.add_argument("--push", action="store_true",
                           help="whether to push images to a registry after "
                                "building")
        group.add_argument("regex", nargs='*',
                           help="regular expression matching names of images "
                                "to build. Builds all images if unspecified")
        return parser

    def take_action(self, parsed_args):
        self.app.LOG.debug("Building overcloud container images")
        playbooks = _build_playbook_list(
            "kolla-build", "container-image-build")
        extra_vars = {"push_images": parsed_args.push}
        if parsed_args.regex:
            regexes = "'%s'" % " ".join(parsed_args.regex)
            extra_vars["container_image_regexes"] = regexes
        self.run_kayobe_playbooks(parsed_args, playbooks, limit="controllers",
                                  extra_vars=extra_vars)


class OvercloudDeploymentImageBuild(KayobeAnsibleMixin, VaultMixin, Command):
    """Build the overcloud deployment kernel and ramdisk images."""

    def take_action(self, parsed_args):
        self.app.LOG.debug("Building overcloud deployment images")
        playbooks = _build_playbook_list("overcloud-ipa-build")
        self.run_kayobe_playbooks(parsed_args, playbooks)


class OvercloudPostConfigure(KayobeAnsibleMixin, VaultMixin, Command):
    """Perform post-deployment configuration.

    * Register Ironic Python Agent (IPA) deployment images using Diskimage
      Builder (DIB), if building deployment images locally.
    * Register ironic inspector introspection rules with the overcloud
      inspector service.
    * Register a provisioning network with glance.
    """

    def take_action(self, parsed_args):
        self.app.LOG.debug("Performing post-deployment configuration")
        playbooks = _build_playbook_list(
            "overcloud-ipa-images", "overcloud-introspection-rules",
            "overcloud-introspection-rules-dell-lldp-workaround",
            "provision-net")
        self.run_kayobe_playbooks(parsed_args, playbooks)
