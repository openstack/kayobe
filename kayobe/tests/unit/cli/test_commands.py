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

import glob
import os
import unittest
from unittest import mock

import cliff.app
import cliff.commandmanager

from kayobe import ansible
from kayobe.cli import commands
from kayobe import utils


class TestApp(cliff.app.App):

    def __init__(self):
        super(TestApp, self).__init__(
            description='Test app',
            version='0.1',
            command_manager=cliff.commandmanager.CommandManager('kayobe.cli'))


class TestCase(unittest.TestCase):

    maxDiff = None

    @mock.patch.object(ansible, "install_galaxy_roles", autospec=True)
    @mock.patch.object(ansible, "install_galaxy_collections", autospec=True)
    @mock.patch.object(ansible, "passwords_yml_exists", autospec=True)
    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbooks")
    def test_control_host_bootstrap(self, mock_run, mock_passwords,
                                    mock_install_collections,
                                    mock_install_roles):
        mock_passwords.return_value = False
        command = commands.ControlHostBootstrap(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args([])
        result = command.run(parsed_args)
        self.assertEqual(0, result)
        mock_install_roles.assert_called_once_with(parsed_args)
        mock_install_collections.assert_called_once_with(parsed_args)
        expected_calls = [
            mock.call(
                mock.ANY,
                [utils.get_data_files_path("ansible", "bootstrap.yml")],
                ignore_limit=True,
            ),
            mock.call(
                mock.ANY,
                [utils.get_data_files_path("ansible", "kolla-ansible.yml")],
                tags="install",
                ignore_limit=True,
                check=False,
            ),
        ]
        self.assertListEqual(expected_calls, mock_run.call_args_list)

    @mock.patch.object(ansible, "install_galaxy_roles", autospec=True)
    @mock.patch.object(ansible, "install_galaxy_collections", autospec=True)
    @mock.patch.object(ansible, "passwords_yml_exists", autospec=True)
    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbooks")
    @mock.patch.object(commands.KollaAnsibleMixin,
                       "run_kolla_ansible_overcloud")
    def test_control_host_bootstrap_with_passwords(
            self, mock_kolla_run, mock_run, mock_passwords,
            mock_install_collections, mock_install_roles):
        mock_passwords.return_value = True
        command = commands.ControlHostBootstrap(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args([])
        result = command.run(parsed_args)
        self.assertEqual(0, result)
        mock_install_roles.assert_called_once_with(parsed_args)
        mock_install_collections.assert_called_once_with(parsed_args)
        expected_calls = [
            mock.call(
                mock.ANY,
                [utils.get_data_files_path("ansible", "bootstrap.yml")],
                ignore_limit=True
            ),
            mock.call(
                mock.ANY,
                [utils.get_data_files_path("ansible", "kolla-ansible.yml")],
                tags=None,
                ignore_limit=True,
                check=False,
            ),
            mock.call(
                mock.ANY,
                [utils.get_data_files_path("ansible", "public-openrc.yml")],
                ignore_limit=True
            ),
        ]
        self.assertListEqual(expected_calls, mock_run.call_args_list)

        expected_calls = [
            mock.call(
                mock.ANY,
                "post-deploy",
            )
        ]
        self.assertListEqual(expected_calls, mock_kolla_run.call_args_list)

    @mock.patch.object(ansible, "install_galaxy_roles", autospec=True)
    @mock.patch.object(ansible, "install_galaxy_collections", autospec=True)
    @mock.patch.object(ansible, "prune_galaxy_roles", autospec=True)
    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbooks")
    def test_control_host_upgrade(self, mock_run, mock_prune,
                                  mock_install_roles,
                                  mock_install_collections):
        command = commands.ControlHostUpgrade(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args([])
        result = command.run(parsed_args)
        self.assertEqual(0, result)
        mock_install_roles.assert_called_once_with(parsed_args, force=True)
        mock_install_collections.assert_called_once_with(parsed_args,
                                                         force=True)
        mock_prune.assert_called_once_with(parsed_args)
        expected_calls = [
            mock.call(
                mock.ANY,
                [utils.get_data_files_path("ansible", "bootstrap.yml")],
                ignore_limit=True,
            ),
            mock.call(
                mock.ANY,
                [utils.get_data_files_path("ansible", "kolla-ansible.yml")],
                tags="install",
                ignore_limit=True,
                check=False,
            ),
        ]
        self.assertListEqual(expected_calls, mock_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbook")
    def test_physical_network_configure(self, mock_run):
        command = commands.PhysicalNetworkConfigure(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args(["--group", "switches"])
        result = command.run(parsed_args)
        self.assertEqual(0, result)
        expected_calls = [
            mock.call(
                mock.ANY,
                utils.get_data_files_path("ansible", "physical-network.yml"),
                limit="switches",
                extra_vars={
                    "physical_network_display": False
                }
            )
        ]
        self.assertListEqual(expected_calls, mock_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbook")
    def test_physical_network_configure_display(self, mock_run):
        command = commands.PhysicalNetworkConfigure(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args(["--group", "switches", "--display"])
        result = command.run(parsed_args)
        self.assertEqual(0, result)
        expected_calls = [
            mock.call(
                mock.ANY,
                utils.get_data_files_path("ansible", "physical-network.yml"),
                limit="switches",
                extra_vars={
                    "physical_network_display": True
                }
            )
        ]
        self.assertListEqual(expected_calls, mock_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbook")
    def test_physical_network_configure_enable_disco(self, mock_run):
        command = commands.PhysicalNetworkConfigure(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args(
            ["--group", "switches", "--enable-discovery"])
        result = command.run(parsed_args)
        self.assertEqual(0, result)
        expected_calls = [
            mock.call(
                mock.ANY,
                utils.get_data_files_path("ansible", "physical-network.yml"),
                limit="switches",
                extra_vars={
                    "physical_network_display": False,
                    "physical_network_enable_discovery": True
                }
            )
        ]
        self.assertListEqual(expected_calls, mock_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbook")
    def test_physical_network_configure_disable_disco(self, mock_run):
        command = commands.PhysicalNetworkConfigure(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args(
            ["--group", "switches", "--disable-discovery"])
        result = command.run(parsed_args)
        self.assertEqual(0, result)
        expected_calls = [
            mock.call(
                mock.ANY,
                utils.get_data_files_path("ansible", "physical-network.yml"),
                limit="switches",
                extra_vars={
                    "physical_network_display": False,
                    "physical_network_disable_discovery": True
                }
            )
        ]
        self.assertListEqual(expected_calls, mock_run.call_args_list)

    def test_physical_network_configure_enable_disable_disco(self):
        command = commands.PhysicalNetworkConfigure(TestApp(), [])
        parser = command.get_parser("test")
        self.assertRaises(
            SystemExit,
            parser.parse_args,
            ["--group", "switches", "--enable-discovery",
             "--disable-discovery"])

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbook")
    def test_physical_network_configure_interface_limit(self, mock_run):
        command = commands.PhysicalNetworkConfigure(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args(
            ["--group", "switches", "--interface-limit", "eth0,eth1"])
        result = command.run(parsed_args)
        self.assertEqual(0, result)
        expected_calls = [
            mock.call(
                mock.ANY,
                utils.get_data_files_path("ansible", "physical-network.yml"),
                limit="switches",
                extra_vars={
                    "physical_network_display": False,
                    "physical_network_interface_limit": "eth0,eth1"
                }
            )
        ]
        self.assertListEqual(expected_calls, mock_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbook")
    def test_physical_network_configure_interface_description_limit(
            self, mock_run):
        command = commands.PhysicalNetworkConfigure(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args(
            ["--group", "switches",
             "--interface-description-limit", "host1,host2"])
        result = command.run(parsed_args)
        self.assertEqual(0, result)
        expected_calls = [
            mock.call(
                mock.ANY,
                utils.get_data_files_path("ansible", "physical-network.yml"),
                limit="switches",
                extra_vars={
                    "physical_network_display": False,
                    "physical_network_interface_description_limit": (
                        "host1,host2")
                }
            )
        ]
        self.assertListEqual(expected_calls, mock_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbooks")
    def test_network_connectivity_check(self, mock_run):
        command = commands.NetworkConnectivityCheck(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args([])
        result = command.run(parsed_args)
        self.assertEqual(0, result)
        expected_calls = [
            mock.call(mock.ANY, [utils.get_data_files_path(
                "ansible", "network-connectivity.yml")]),
        ]
        self.assertListEqual(expected_calls, mock_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbooks")
    def test_seed_hypervisor_host_configure(self, mock_run):
        command = commands.SeedHypervisorHostConfigure(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args([])

        result = command.run(parsed_args)
        self.assertEqual(0, result)

        expected_calls = [
            mock.call(
                mock.ANY,
                [utils.get_data_files_path("ansible", "ip-allocation.yml")],
                limit="seed-hypervisor",
            ),
            mock.call(
                mock.ANY,
                [
                    utils.get_data_files_path(
                        "ansible", "seed-hypervisor-host-configure.yml"),
                ],
                limit="seed-hypervisor",
            ),
        ]
        self.assertListEqual(expected_calls, mock_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbooks")
    def test_seed_hypervisor_host_configure_wipe_disks(self, mock_run):
        command = commands.SeedHypervisorHostConfigure(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args(["--wipe-disks"])

        result = command.run(parsed_args)
        self.assertEqual(0, result)

        expected_calls = [
            mock.call(
                mock.ANY,
                [utils.get_data_files_path("ansible", "ip-allocation.yml")],
                limit="seed-hypervisor",
            ),
            mock.call(
                mock.ANY,
                [
                    utils.get_data_files_path(
                        "ansible", "seed-hypervisor-host-configure.yml"),
                ],
                limit="seed-hypervisor",
                extra_vars={"wipe_disks": True},
            ),
        ]
        self.assertListEqual(expected_calls, mock_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbooks")
    def test_seed_hypervisor_host_command_run(self, mock_run):
        command = commands.SeedHypervisorHostCommandRun(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args(["--command", "ls -a",
                                         "--show-output"])

        result = command.run(parsed_args)
        self.assertEqual(0, result)

        expected_calls = [
            mock.call(
                mock.ANY,
                [
                    utils.get_data_files_path("ansible",
                                              "host-command-run.yml"),
                ],
                limit="seed-hypervisor",
                extra_vars={
                    "host_command_to_run": utils.escape_jinja("ls -a"),
                    "show_output": True}
            ),
        ]
        self.assertListEqual(expected_calls, mock_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbooks")
    def test_seed_hypervisor_host_package_update_all(self, mock_run):
        command = commands.SeedHypervisorHostPackageUpdate(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args(["--packages", "*"])

        result = command.run(parsed_args)
        self.assertEqual(0, result)

        expected_calls = [
            mock.call(
                mock.ANY,
                [
                    utils.get_data_files_path(
                        "ansible", "host-package-update.yml"),
                ],
                limit="seed-hypervisor",
                extra_vars={
                    "host_package_update_packages": "*",
                    "host_package_update_security": False,
                },
            ),
        ]
        self.assertListEqual(expected_calls, mock_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbooks")
    def test_seed_hypervisor_host_package_update_list(self, mock_run):
        command = commands.SeedHypervisorHostPackageUpdate(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args(["--packages", "p1,p2"])

        result = command.run(parsed_args)
        self.assertEqual(0, result)

        expected_calls = [
            mock.call(
                mock.ANY,
                [
                    utils.get_data_files_path(
                        "ansible", "host-package-update.yml"),
                ],
                limit="seed-hypervisor",
                extra_vars={
                    "host_package_update_packages": "p1,p2",
                    "host_package_update_security": False,
                },
            ),
        ]
        self.assertListEqual(expected_calls, mock_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbooks")
    def test_seed_hypervisor_host_package_update_security(self, mock_run):
        command = commands.SeedHypervisorHostPackageUpdate(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args(["--packages", "*", "--security"])

        result = command.run(parsed_args)
        self.assertEqual(0, result)

        expected_calls = [
            mock.call(
                mock.ANY,
                [
                    utils.get_data_files_path(
                        "ansible", "host-package-update.yml"),
                ],
                limit="seed-hypervisor",
                extra_vars={
                    "host_package_update_packages": "*",
                    "host_package_update_security": True,
                },
            ),
        ]
        self.assertListEqual(expected_calls, mock_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbooks")
    def test_seed_hypervisor_host_upgrade(self, mock_run):
        command = commands.SeedHypervisorHostUpgrade(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args([])

        result = command.run(parsed_args)
        self.assertEqual(0, result)

        expected_calls = [
            mock.call(
                mock.ANY,
                [
                    utils.get_data_files_path(
                        "ansible", "kayobe-target-venv.yml"),
                ],
                limit="seed-hypervisor",
            ),
        ]
        self.assertListEqual(expected_calls, mock_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbooks")
    def test_seed_host_configure(self, mock_run):
        command = commands.SeedHostConfigure(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args([])

        result = command.run(parsed_args)
        self.assertEqual(0, result)

        expected_calls = [
            mock.call(
                mock.ANY,
                [utils.get_data_files_path("ansible", "ip-allocation.yml")],
                limit="seed",
            ),
            mock.call(
                mock.ANY,
                [
                    utils.get_data_files_path(
                        "ansible", "seed-host-configure.yml"),
                ],
                limit="seed",
                extra_vars={"kayobe_action": "deploy"},
            ),
        ]
        self.assertListEqual(expected_calls, mock_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbooks")
    def test_seed_host_configure_wipe_disks(self, mock_run):
        command = commands.SeedHostConfigure(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args(["--wipe-disks"])

        result = command.run(parsed_args)
        self.assertEqual(0, result)

        expected_calls = [
            mock.call(
                mock.ANY,
                [utils.get_data_files_path("ansible", "ip-allocation.yml")],
                limit="seed",
            ),
            mock.call(
                mock.ANY,
                [
                    utils.get_data_files_path(
                        "ansible", "seed-host-configure.yml"),
                ],
                limit="seed",
                extra_vars={"kayobe_action": "deploy", "wipe_disks": True},
            ),
        ]
        print(expected_calls)
        print(mock_run.call_args_list)
        self.assertListEqual(expected_calls, mock_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbooks")
    def test_seed_host_command_run(self, mock_run):
        command = commands.SeedHostCommandRun(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args(["--command", "ls -a",
                                         "--show-output"])

        result = command.run(parsed_args)
        self.assertEqual(0, result)

        expected_calls = [
            mock.call(
                mock.ANY,
                [
                    utils.get_data_files_path("ansible",
                                              "host-command-run.yml"),
                ],
                limit="seed",
                extra_vars={
                    "host_command_to_run": utils.escape_jinja("ls -a"),
                    "show_output": True}
            ),
        ]
        self.assertListEqual(expected_calls, mock_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbooks")
    def test_seed_host_package_update_all(self, mock_run):
        command = commands.SeedHostPackageUpdate(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args(["--packages", "*"])

        result = command.run(parsed_args)
        self.assertEqual(0, result)

        expected_calls = [
            mock.call(
                mock.ANY,
                [
                    utils.get_data_files_path(
                        "ansible", "host-package-update.yml"),
                ],
                limit="seed",
                extra_vars={
                    "host_package_update_packages": "*",
                    "host_package_update_security": False,
                },
            ),
        ]
        self.assertListEqual(expected_calls, mock_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbooks")
    def test_seed_host_package_update_list(self, mock_run):
        command = commands.SeedHostPackageUpdate(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args(["--packages", "p1,p2"])

        result = command.run(parsed_args)
        self.assertEqual(0, result)

        expected_calls = [
            mock.call(
                mock.ANY,
                [
                    utils.get_data_files_path(
                        "ansible", "host-package-update.yml"),
                ],
                limit="seed",
                extra_vars={
                    "host_package_update_packages": "p1,p2",
                    "host_package_update_security": False,
                },
            ),
        ]
        self.assertListEqual(expected_calls, mock_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbooks")
    def test_seed_host_package_update_security(self, mock_run):
        command = commands.SeedHostPackageUpdate(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args(["--packages", "*", "--security"])

        result = command.run(parsed_args)
        self.assertEqual(0, result)

        expected_calls = [
            mock.call(
                mock.ANY,
                [
                    utils.get_data_files_path(
                        "ansible", "host-package-update.yml"),
                ],
                limit="seed",
                extra_vars={
                    "host_package_update_packages": "*",
                    "host_package_update_security": True,
                },
            ),
        ]
        self.assertListEqual(expected_calls, mock_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbooks")
    def test_seed_host_upgrade(self, mock_run):
        command = commands.SeedHostUpgrade(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args([])

        result = command.run(parsed_args)
        self.assertEqual(0, result)

        expected_calls = [
            mock.call(
                mock.ANY,
                [
                    utils.get_data_files_path(
                        "ansible", "seed-host-upgrade.yml"),
                ],
                limit="seed",
            ),
        ]
        self.assertListEqual(expected_calls, mock_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbooks")
    def test_seed_container_image_build(self, mock_run):
        command = commands.SeedContainerImageBuild(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args([])
        result = command.run(parsed_args)
        self.assertEqual(0, result)
        expected_calls = [
            mock.call(
                mock.ANY,
                [
                    utils.get_data_files_path(
                        "ansible", "container-image-builders-check.yml"),
                    utils.get_data_files_path("ansible", "kolla-build.yml"),
                    utils.get_data_files_path(
                        "ansible", "container-image-build.yml")
                ],
                extra_vars={
                    "container_image_sets": (
                        "{{ seed_container_image_sets }}"),
                    "push_images": False,
                    "nocache": False
                }
            ),
        ]
        self.assertListEqual(expected_calls, mock_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbooks")
    def test_seed_container_image_build_with_regex(self, mock_run):
        command = commands.SeedContainerImageBuild(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args(["--push", "^regex1$", "^regex2$"])
        result = command.run(parsed_args)
        self.assertEqual(0, result)
        expected_calls = [
            mock.call(
                mock.ANY,
                [
                    utils.get_data_files_path(
                        "ansible", "container-image-builders-check.yml"),
                    utils.get_data_files_path("ansible", "kolla-build.yml"),
                    utils.get_data_files_path(
                        "ansible", "container-image-build.yml")
                ],
                extra_vars={
                    "container_image_regexes": "^regex1$ ^regex2$",
                    "push_images": True,
                    "nocache": False
                }
            ),
        ]
        self.assertListEqual(expected_calls, mock_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbooks")
    def test_seed_container_image_build_with_nocache(self, mock_run):
        command = commands.SeedContainerImageBuild(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args(["--nocache"])
        result = command.run(parsed_args)
        self.assertEqual(0, result)
        expected_calls = [
            mock.call(
                mock.ANY,
                [
                    utils.get_data_files_path(
                        "ansible", "container-image-builders-check.yml"),
                    utils.get_data_files_path("ansible", "kolla-build.yml"),
                    utils.get_data_files_path(
                        "ansible", "container-image-build.yml")
                ],
                extra_vars={
                    "container_image_sets": (
                        "{{ seed_container_image_sets }}"),
                    "push_images": False,
                    "nocache": True
                }
            ),
        ]
        self.assertListEqual(expected_calls, mock_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbooks")
    def test_seed_deployment_image_build(self, mock_run):
        command = commands.SeedDeploymentImageBuild(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args([])

        result = command.run(parsed_args)
        self.assertEqual(0, result)

        expected_calls = [
            mock.call(
                mock.ANY,
                [
                    utils.get_data_files_path("ansible", "seed-ipa-build.yml"),
                ],
                extra_vars={},
            ),
        ]
        self.assertListEqual(expected_calls, mock_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbooks")
    def test_seed_deployment_image_build_force_rebuild(self, mock_run):
        command = commands.SeedDeploymentImageBuild(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args(["--force-rebuild"])

        result = command.run(parsed_args)
        self.assertEqual(0, result)

        expected_calls = [
            mock.call(
                mock.ANY,
                [
                    utils.get_data_files_path("ansible", "seed-ipa-build.yml"),
                ],
                extra_vars={"ipa_image_force_rebuild": True},
            ),
        ]
        self.assertListEqual(expected_calls, mock_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbooks")
    @mock.patch.object(commands.KollaAnsibleMixin,
                       "run_kolla_ansible_seed")
    def test_seed_service_deploy(self, mock_kolla_run, mock_run):
        command = commands.SeedServiceDeploy(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args([])

        result = command.run(parsed_args)
        self.assertEqual(0, result)

        expected_calls = [
            mock.call(
                mock.ANY,
                [utils.get_data_files_path("ansible", "seed-manage-containers.yml")],  # noqa
                extra_vars={'kayobe_action': 'deploy'}
            ),
            mock.call(
                mock.ANY,
                [utils.get_data_files_path("ansible", "kolla-ansible.yml")],
                tags="config",
                ignore_limit=True,
                check=False,
            ),
            mock.call(
                mock.ANY,
                [utils.get_data_files_path("ansible", "kolla-bifrost.yml")],
                ignore_limit=True,
                check=False,
            ),
            mock.call(
                mock.ANY,
                [
                    utils.get_data_files_path(
                        "ansible", "seed-credentials.yml"),
                    utils.get_data_files_path(
                        "ansible", "seed-introspection-rules.yml"),
                    utils.get_data_files_path(
                        "ansible", "dell-switch-bmp.yml"),
                ],
                extra_vars={'kayobe_action': 'deploy'}
            ),
        ]
        self.assertListEqual(expected_calls, mock_run.call_args_list)

        expected_calls = [
            mock.call(
                mock.ANY,
                "deploy-bifrost",
            ),
        ]
        self.assertListEqual(expected_calls, mock_kolla_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbooks")
    @mock.patch.object(commands.KollaAnsibleMixin,
                       "run_kolla_ansible_seed")
    def test_seed_service_upgrade(self, mock_kolla_run, mock_run):
        command = commands.SeedServiceUpgrade(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args([])

        result = command.run(parsed_args)
        self.assertEqual(0, result)

        expected_calls = [
            mock.call(
                mock.ANY,
                [utils.get_data_files_path("ansible", "seed-manage-containers.yml")],  # noqa
                extra_vars={'kayobe_action': 'deploy'}
            ),
            mock.call(
                mock.ANY,
                [utils.get_data_files_path("ansible", "kolla-ansible.yml")],
                tags="config",
                ignore_limit=True,
                check=False,
            ),
            mock.call(
                mock.ANY,
                [utils.get_data_files_path("ansible", "kolla-bifrost.yml")],
                ignore_limit=True,
                check=False,
            ),
            mock.call(
                mock.ANY,
                [
                    utils.get_data_files_path("ansible",
                                              "seed-service-upgrade-prep.yml")
                ],
            ),
            mock.call(
                mock.ANY,
                [
                    utils.get_data_files_path(
                        "ansible", "seed-credentials.yml"),
                    utils.get_data_files_path(
                        "ansible",
                        "seed-introspection-rules.yml"),
                    utils.get_data_files_path(
                        "ansible",
                        "dell-switch-bmp.yml"),
                ],
            ),
        ]
        self.assertListEqual(expected_calls, mock_run.call_args_list)

        expected_calls = [
            mock.call(
                mock.ANY,
                "upgrade-bifrost",
            ),
        ]
        self.assertListEqual(expected_calls, mock_kolla_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbook")
    def test_infra_vm_provision(self, mock_run):
        command = commands.InfraVMProvision(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args([])

        result = command.run(parsed_args)
        self.assertEqual(0, result)

        expected_calls = [
            mock.call(
                mock.ANY,
                utils.get_data_files_path(
                    "ansible", "ip-allocation.yml"),
                limit="infra-vms"
            ),
            mock.call(
                mock.ANY,
                utils.get_data_files_path(
                    "ansible", "infra-vm-provision.yml"),
                ignore_limit=True,
                extra_vars={'infra_vm_limit': 'infra-vms'}
            ),
        ]
        self.assertListEqual(expected_calls, mock_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbook")
    def test_infra_vm_deprovision(self, mock_run):
        command = commands.InfraVMDeprovision(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args([])

        result = command.run(parsed_args)
        self.assertEqual(0, result)

        expected_calls = [
            mock.call(
                mock.ANY,
                utils.get_data_files_path(
                    "ansible", "infra-vm-deprovision.yml"),
                ignore_limit=True,
                extra_vars={'infra_vm_limit': 'infra-vms'}
            ),
        ]
        self.assertListEqual(expected_calls, mock_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbooks")
    def test_infra_vm_host_configure(self, mock_run):
        command = commands.InfraVMHostConfigure(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args([])

        result = command.run(parsed_args)
        self.assertEqual(0, result)

        expected_calls = [
            mock.call(
                mock.ANY,
                [utils.get_data_files_path("ansible", "ip-allocation.yml")],
                limit="infra-vms",
            ),
            mock.call(
                mock.ANY,
                [
                    utils.get_data_files_path(
                        "ansible", "infra-vm-host-configure.yml"),
                ],
                limit="infra-vms",
            ),
        ]
        self.assertListEqual(expected_calls, mock_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbooks")
    def test_infra_vm_host_configure_wipe_disks(self, mock_run):
        command = commands.InfraVMHostConfigure(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args(["--wipe-disks"])

        result = command.run(parsed_args)
        self.assertEqual(0, result)

        expected_calls = [
            mock.call(
                mock.ANY,
                [utils.get_data_files_path("ansible", "ip-allocation.yml")],
                limit="infra-vms",
            ),
            mock.call(
                mock.ANY,
                [
                    utils.get_data_files_path(
                        "ansible", "infra-vm-host-configure.yml"),
                ],
                limit="infra-vms",
                extra_vars={"wipe_disks": True},
            ),
        ]
        self.assertListEqual(expected_calls, mock_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbooks")
    def test_infra_vm_host_upgrade(self, mock_run):
        command = commands.InfraVMHostUpgrade(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args([])

        result = command.run(parsed_args)
        self.assertEqual(0, result)

        expected_calls = [
            mock.call(
                mock.ANY,
                [
                    utils.get_data_files_path(
                        "ansible", "kayobe-target-venv.yml"),
                ],
                limit="infra-vms",
            ),
        ]
        self.assertListEqual(expected_calls, mock_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbooks")
    def test_infra_vm_host_command_run(self, mock_run):
        command = commands.InfraVMHostCommandRun(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args(["--command", "ls -a",
                                         "--show-output"])

        result = command.run(parsed_args)
        self.assertEqual(0, result)

        expected_calls = [
            mock.call(
                mock.ANY,
                [
                    utils.get_data_files_path("ansible",
                                              "host-command-run.yml"),
                ],
                limit="infra-vms",
                extra_vars={
                    "host_command_to_run": utils.escape_jinja("ls -a"),
                    "show_output": True}
            ),
        ]
        self.assertListEqual(expected_calls, mock_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbooks")
    def test_infra_vm_host_package_update_all(self, mock_run):
        command = commands.InfraVMHostPackageUpdate(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args(["--packages", "*"])

        result = command.run(parsed_args)
        self.assertEqual(0, result)

        expected_calls = [
            mock.call(
                mock.ANY,
                [
                    utils.get_data_files_path(
                        "ansible", "host-package-update.yml"),
                ],
                limit="infra-vms",
                extra_vars={
                    "host_package_update_packages": "*",
                    "host_package_update_security": False,
                },
            ),
        ]
        self.assertListEqual(expected_calls, mock_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbook")
    def test_infra_vm_service_deploy(self, mock_run):
        command = commands.InfraVMServiceDeploy(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args([])

        result = command.run(parsed_args)
        self.assertEqual(0, result)

        expected_calls = []
        self.assertListEqual(expected_calls, mock_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbooks")
    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbook")
    def test_overcloud_inventory_discover(self, mock_run_one, mock_run):
        command = commands.OvercloudInventoryDiscover(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args([])

        result = command.run(parsed_args)
        self.assertEqual(0, result)

        expected_calls = [
            mock.call(
                mock.ANY,
                utils.get_data_files_path(
                    "ansible", "overcloud-inventory-discover.yml"),
            ),
            mock.call(
                mock.ANY,
                utils.get_data_files_path("ansible", "ip-allocation.yml"),
                limit="overcloud",
            ),
        ]
        self.assertListEqual(expected_calls, mock_run_one.call_args_list)

        expected_calls = [
            mock.call(
                mock.ANY,
                [utils.get_data_files_path("ansible", "kolla-ansible.yml")],
                tags="config",
                ignore_limit=True,
                check=False,
            ),
        ]
        self.assertListEqual(expected_calls, mock_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbooks")
    def test_overcloud_hardware_inspect(self, mock_run):
        command = commands.OvercloudHardwareInspect(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args([])

        result = command.run(parsed_args)
        self.assertEqual(0, result)

        expected_calls = [
            mock.call(
                mock.ANY,
                [
                    utils.get_data_files_path(
                        "ansible", "kolla-bifrost-hostvars.yml"),
                    utils.get_data_files_path(
                        "ansible", "overcloud-hardware-inspect.yml"),
                ],
            ),
        ]
        self.assertListEqual(expected_calls, mock_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbooks")
    def test_overcloud_provision(self, mock_run):
        command = commands.OvercloudProvision(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args([])

        result = command.run(parsed_args)
        self.assertEqual(0, result)

        expected_calls = [
            mock.call(
                mock.ANY,
                [
                    utils.get_data_files_path(
                        "ansible", "kolla-bifrost-hostvars.yml"),
                    utils.get_data_files_path(
                        "ansible", "overcloud-provision.yml"),
                ],
            ),
        ]
        self.assertListEqual(expected_calls, mock_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbooks")
    def test_overcloud_deprovision(self, mock_run):
        command = commands.OvercloudDeprovision(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args([])

        result = command.run(parsed_args)
        self.assertEqual(0, result)

        expected_calls = [
            mock.call(
                mock.ANY,
                [
                    utils.get_data_files_path(
                        "ansible", "kolla-bifrost-hostvars.yml"),
                    utils.get_data_files_path(
                        "ansible", "overcloud-deprovision.yml"),
                ],
            ),
        ]
        self.assertListEqual(expected_calls, mock_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbooks")
    @mock.patch.object(commands.KollaAnsibleMixin,
                       "run_kolla_ansible_overcloud")
    def test_overcloud_facts_gather(self, mock_kolla_run, mock_run):
        command = commands.OvercloudFactsGather(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args([])

        result = command.run(parsed_args)
        self.assertEqual(0, result)

        expected_calls = [
            mock.call(
                mock.ANY,
                [
                    utils.get_data_files_path(
                        "ansible", "overcloud-facts-gather.yml"),
                ],
            ),
            mock.call(
                mock.ANY,
                [utils.get_data_files_path("ansible", "kolla-ansible.yml")],
                tags="config",
                ignore_limit=True,
                check=False,
            ),
        ]
        self.assertListEqual(expected_calls, mock_run.call_args_list)

        expected_calls = [
            mock.call(
                mock.ANY,
                "gather-facts"
            ),
        ]
        self.assertListEqual(expected_calls, mock_kolla_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbooks")
    def test_overcloud_host_configure(self, mock_run):
        command = commands.OvercloudHostConfigure(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args([])

        result = command.run(parsed_args)
        self.assertEqual(0, result)

        expected_calls = [
            mock.call(
                mock.ANY,
                [utils.get_data_files_path("ansible", "ip-allocation.yml")],
                limit="overcloud",
            ),
            mock.call(
                mock.ANY,
                [
                    utils.get_data_files_path(
                        "ansible", "overcloud-host-configure.yml"),
                ],
                limit="overcloud",
            ),
        ]
        self.assertListEqual(expected_calls, mock_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbooks")
    def test_overcloud_host_configure_wipe_disks(self, mock_run):
        command = commands.OvercloudHostConfigure(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args(["--wipe-disks"])

        result = command.run(parsed_args)
        self.assertEqual(0, result)

        expected_calls = [
            mock.call(
                mock.ANY,
                [utils.get_data_files_path("ansible", "ip-allocation.yml")],
                limit="overcloud",
            ),
            mock.call(
                mock.ANY,
                [
                    utils.get_data_files_path(
                        "ansible", "overcloud-host-configure.yml"),
                ],
                limit="overcloud",
                extra_vars={"wipe_disks": True},
            ),
        ]
        self.assertListEqual(expected_calls, mock_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbooks")
    def test_overcloud_host_command_run(self, mock_run):
        command = commands.OvercloudHostCommandRun(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args(["--command", "ls -a",
                                         "--show-output"])

        result = command.run(parsed_args)
        self.assertEqual(0, result)

        expected_calls = [
            mock.call(
                mock.ANY,
                [
                    utils.get_data_files_path("ansible",
                                              "host-command-run.yml"),
                ],
                limit="overcloud",
                extra_vars={
                    "host_command_to_run": utils.escape_jinja("ls -a"),
                    "show_output": True}
            ),
        ]
        self.assertListEqual(expected_calls, mock_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbooks")
    def test_overcloud_host_package_update_all(self, mock_run):
        command = commands.OvercloudHostPackageUpdate(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args(["--packages", "*"])

        result = command.run(parsed_args)
        self.assertEqual(0, result)

        expected_calls = [
            mock.call(
                mock.ANY,
                [
                    utils.get_data_files_path(
                        "ansible", "host-package-update.yml"),
                ],
                limit="overcloud",
                extra_vars={
                    "host_package_update_packages": "*",
                    "host_package_update_security": False,
                },
            ),
        ]
        self.assertListEqual(expected_calls, mock_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbooks")
    def test_overcloud_host_package_update_list(self, mock_run):
        command = commands.OvercloudHostPackageUpdate(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args(["--packages", "p1,p2"])

        result = command.run(parsed_args)
        self.assertEqual(0, result)

        expected_calls = [
            mock.call(
                mock.ANY,
                [
                    utils.get_data_files_path(
                        "ansible", "host-package-update.yml"),
                ],
                limit="overcloud",
                extra_vars={
                    "host_package_update_packages": "p1,p2",
                    "host_package_update_security": False,
                },
            ),
        ]
        self.assertListEqual(expected_calls, mock_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbooks")
    def test_overcloud_host_package_update_security(self, mock_run):
        command = commands.OvercloudHostPackageUpdate(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args(["--packages", "*", "--security"])

        result = command.run(parsed_args)
        self.assertEqual(0, result)

        expected_calls = [
            mock.call(
                mock.ANY,
                [
                    utils.get_data_files_path(
                        "ansible", "host-package-update.yml"),
                ],
                limit="overcloud",
                extra_vars={
                    "host_package_update_packages": "*",
                    "host_package_update_security": True,
                },
            ),
        ]
        self.assertListEqual(expected_calls, mock_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbooks")
    def test_overcloud_host_upgrade(self, mock_run):
        command = commands.OvercloudHostUpgrade(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args([])

        result = command.run(parsed_args)
        self.assertEqual(0, result)

        expected_calls = [
            mock.call(
                mock.ANY,
                [
                    utils.get_data_files_path(
                        "ansible", "overcloud-host-upgrade.yml"),
                ],
                limit="overcloud",
            ),
        ]
        self.assertListEqual(expected_calls, mock_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbooks")
    @mock.patch.object(commands.KollaAnsibleMixin,
                       "run_kolla_ansible_overcloud")
    def test_overcloud_database_backup(self, mock_kolla_run, mock_run):
        command = commands.OvercloudDatabaseBackup(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args([])
        result = command.run(parsed_args)
        self.assertEqual(0, result)

        expected_calls = [
            mock.call(
                mock.ANY,
                [utils.get_data_files_path("ansible", "kolla-ansible.yml")],
                tags="config",
                ignore_limit=True,
                check=False,
            ),
        ]
        self.assertListEqual(expected_calls, mock_run.call_args_list)

        expected_calls = [
            mock.call(
                mock.ANY,
                "mariadb-backup",
                extra_args=[]
            ),
        ]
        self.assertListEqual(expected_calls, mock_kolla_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbooks")
    @mock.patch.object(commands.KollaAnsibleMixin,
                       "run_kolla_ansible_overcloud")
    def test_overcloud_database_backup_incremental(self, mock_kolla_run,
                                                   mock_run):
        command = commands.OvercloudDatabaseBackup(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args(["--incremental"])
        result = command.run(parsed_args)
        self.assertEqual(0, result)

        expected_calls = [
            mock.call(
                mock.ANY,
                [utils.get_data_files_path("ansible", "kolla-ansible.yml")],
                tags="config",
                ignore_limit=True,
                check=False,
            ),
        ]
        self.assertListEqual(expected_calls, mock_run.call_args_list)

        expected_calls = [
            mock.call(
                mock.ANY,
                "mariadb-backup",
                extra_args=["--incremental"]
            ),
        ]
        self.assertListEqual(expected_calls, mock_kolla_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbooks")
    @mock.patch.object(commands.KollaAnsibleMixin,
                       "run_kolla_ansible_overcloud")
    def test_overcloud_database_recover(self, mock_kolla_run, mock_run):
        command = commands.OvercloudDatabaseRecover(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args([])
        result = command.run(parsed_args)
        self.assertEqual(0, result)

        expected_calls = [
            mock.call(
                mock.ANY,
                [utils.get_data_files_path("ansible", "kolla-ansible.yml")],
                tags="config",
                ignore_limit=True,
                check=False,
            ),
            mock.call(
                mock.ANY,
                [
                    utils.get_data_files_path("ansible",
                                              "kolla-openstack.yml"),
                ],
                ignore_limit=True,
                check=False,
            ),
        ]
        self.assertListEqual(expected_calls, mock_run.call_args_list)

        expected_calls = [
            mock.call(
                mock.ANY,
                "mariadb-recovery",
                extra_vars={}
            ),
        ]
        self.assertListEqual(expected_calls, mock_kolla_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbooks")
    @mock.patch.object(commands.KollaAnsibleMixin,
                       "run_kolla_ansible_overcloud")
    def test_overcloud_database_recover_force_host(self, mock_kolla_run,
                                                   mock_run):
        command = commands.OvercloudDatabaseRecover(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args(["--force-recovery-host", "foo"])
        result = command.run(parsed_args)
        self.assertEqual(0, result)

        expected_calls = [
            mock.call(
                mock.ANY,
                [utils.get_data_files_path("ansible", "kolla-ansible.yml")],
                tags="config",
                ignore_limit=True,
                check=False,
            ),
            mock.call(
                mock.ANY,
                [
                    utils.get_data_files_path("ansible",
                                              "kolla-openstack.yml"),
                ],
                ignore_limit=True,
                check=False,
            ),
        ]
        self.assertListEqual(expected_calls, mock_run.call_args_list)

        expected_calls = [
            mock.call(
                mock.ANY,
                "mariadb-recovery",
                extra_vars={
                    "mariadb_recover_inventory_name": "foo"
                }
            ),
        ]
        self.assertListEqual(expected_calls, mock_kolla_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbooks")
    def test_overcloud_service_configuration_save(self, mock_run):
        command = commands.OvercloudServiceConfigurationSave(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args([])
        result = command.run(parsed_args)
        self.assertEqual(0, result)
        expected_calls = [
            mock.call(
                mock.ANY,
                [
                    utils.get_data_files_path(
                        "ansible", "overcloud-service-config-save.yml"),
                ],
                extra_vars={}
            ),
        ]
        self.assertListEqual(expected_calls, mock_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbooks")
    @mock.patch.object(commands.KollaAnsibleMixin,
                       "run_kolla_ansible_overcloud")
    def test_overcloud_service_deploy(self, mock_kolla_run, mock_run):
        command = commands.OvercloudServiceDeploy(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args([])

        result = command.run(parsed_args)
        self.assertEqual(0, result)

        expected_calls = [
            mock.call(
                mock.ANY,
                [utils.get_data_files_path("ansible", "kolla-ansible.yml")],
                ignore_limit=True,
                tags="config",
                check=False,
            ),
            mock.call(
                mock.ANY,
                [
                    utils.get_data_files_path("ansible",
                                              "kolla-openstack.yml"),
                ],
                ignore_limit=True,
                check=False,
            ),
            mock.call(
                mock.ANY,
                [
                    utils.get_data_files_path("ansible",
                                              "overcloud-extras.yml"),
                ],
                limit="overcloud",
                extra_vars={
                    "kayobe_action": "deploy",
                },
            ),
            mock.call(
                mock.ANY,
                [
                    utils.get_data_files_path("ansible", "public-openrc.yml"),
                ],
                ignore_limit=True,
            ),
        ]
        self.assertListEqual(expected_calls, mock_run.call_args_list)

        expected_calls = [
            mock.call(
                mock.ANY,
                "prechecks",
            ),
            mock.call(
                mock.ANY,
                "deploy",
            ),
            mock.call(
                mock.ANY,
                "post-deploy",
            ),
        ]
        self.assertListEqual(expected_calls, mock_kolla_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbooks")
    @mock.patch.object(commands.KollaAnsibleMixin,
                       "run_kolla_ansible_overcloud")
    def test_overcloud_service_deploy_containers(self, mock_kolla_run,
                                                 mock_run):
        command = commands.OvercloudServiceDeployContainers(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args([])

        result = command.run(parsed_args)
        self.assertEqual(0, result)

        expected_calls = [
            mock.call(
                mock.ANY,
                [utils.get_data_files_path("ansible", "kolla-ansible.yml")],
                ignore_limit=True,
                tags="config",
                check=False,
            ),
            mock.call(
                mock.ANY,
                [
                    utils.get_data_files_path("ansible",
                                              "kolla-openstack.yml"),
                ],
                ignore_limit=True,
                check=False,
            ),
            mock.call(
                mock.ANY,
                [
                    utils.get_data_files_path("ansible",
                                              "overcloud-extras.yml"),
                ],
                limit="overcloud",
                extra_vars={
                    "kayobe_action": "deploy",
                },
            ),
        ]
        self.assertListEqual(expected_calls, mock_run.call_args_list)

        expected_calls = [
            mock.call(
                mock.ANY,
                "prechecks",
            ),
            mock.call(
                mock.ANY,
                "manage-containers",
            ),
        ]
        self.assertListEqual(expected_calls, mock_kolla_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbooks")
    @mock.patch.object(commands.KollaAnsibleMixin,
                       "run_kolla_ansible_overcloud")
    def test_overcloud_service_prechecks(self, mock_kolla_run, mock_run):
        command = commands.OvercloudServicePrechecks(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args([])

        result = command.run(parsed_args)
        self.assertEqual(0, result)

        expected_calls = [
            mock.call(
                mock.ANY,
                [utils.get_data_files_path("ansible", "kolla-ansible.yml")],
                ignore_limit=True,
                tags="config",
                check=False,
            ),
            mock.call(
                mock.ANY,
                [
                    utils.get_data_files_path("ansible",
                                              "kolla-openstack.yml"),
                ],
                ignore_limit=True,
                check=False,
            ),
        ]
        self.assertListEqual(expected_calls, mock_run.call_args_list)

        expected_calls = [
            mock.call(
                mock.ANY,
                "prechecks",
            ),
        ]
        self.assertListEqual(expected_calls, mock_kolla_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbooks")
    @mock.patch.object(commands.KollaAnsibleMixin,
                       "run_kolla_ansible_overcloud")
    def test_overcloud_service_reconfigure(self, mock_kolla_run, mock_run):
        command = commands.OvercloudServiceReconfigure(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args([])

        result = command.run(parsed_args)
        self.assertEqual(0, result)

        expected_calls = [
            mock.call(
                mock.ANY,
                [utils.get_data_files_path("ansible", "kolla-ansible.yml")],
                ignore_limit=True,
                tags="config",
                check=False,
            ),
            mock.call(
                mock.ANY,
                [
                    utils.get_data_files_path("ansible",
                                              "kolla-openstack.yml"),
                ],
                ignore_limit=True,
                check=False,
            ),
            mock.call(
                mock.ANY,
                [
                    utils.get_data_files_path("ansible",
                                              "overcloud-extras.yml"),
                ],
                limit="overcloud",
                extra_vars={
                    "kayobe_action": "reconfigure",
                },
            ),
            mock.call(
                mock.ANY,
                [
                    utils.get_data_files_path("ansible", "public-openrc.yml"),
                ],
                ignore_limit=True,
            ),
        ]
        self.assertListEqual(expected_calls, mock_run.call_args_list)

        expected_calls = [
            mock.call(
                mock.ANY,
                "prechecks",
            ),
            mock.call(
                mock.ANY,
                "reconfigure",
            ),
            mock.call(
                mock.ANY,
                "post-deploy",
            ),
        ]
        self.assertListEqual(expected_calls, mock_kolla_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbooks")
    @mock.patch.object(commands.KollaAnsibleMixin,
                       "run_kolla_ansible_overcloud")
    def test_overcloud_service_stop(self, mock_kolla_run, mock_run):
        command = commands.OvercloudServiceStop(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args(["--yes-i-really-really-mean-it"])

        result = command.run(parsed_args)
        self.assertEqual(0, result)

        expected_calls = [
            mock.call(
                mock.ANY,
                [utils.get_data_files_path("ansible", "kolla-ansible.yml")],
                ignore_limit=True,
                tags="config",
                check=False,
            ),
            mock.call(
                mock.ANY,
                [
                    utils.get_data_files_path("ansible",
                                              "kolla-openstack.yml"),
                ],
                ignore_limit=True,
                check=False,
            ),
            mock.call(
                mock.ANY,
                [
                    utils.get_data_files_path("ansible",
                                              "overcloud-extras.yml"),
                ],
                limit="overcloud",
                extra_vars={
                    "kayobe_action": "stop",
                },
            ),
        ]
        self.assertListEqual(expected_calls, mock_run.call_args_list)

        expected_calls = [
            mock.call(
                mock.ANY,
                "stop",
                extra_args=["--yes-i-really-really-mean-it"],
            ),
        ]
        self.assertListEqual(expected_calls, mock_kolla_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbooks")
    @mock.patch.object(commands.KollaAnsibleMixin,
                       "run_kolla_ansible_overcloud")
    def test_overcloud_service_stop_no_disclaimer(self, mock_kolla_run,
                                                  mock_run):
        command = commands.OvercloudServiceStop(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args([])

        self.assertRaises(
            SystemExit,
            command.run, parsed_args)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbooks")
    @mock.patch.object(commands.KollaAnsibleMixin,
                       "run_kolla_ansible_overcloud")
    def test_overcloud_service_upgrade(self, mock_kolla_run, mock_run):
        command = commands.OvercloudServiceUpgrade(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args([])

        result = command.run(parsed_args)
        self.assertEqual(0, result)

        expected_calls = [
            mock.call(
                mock.ANY,
                [utils.get_data_files_path("ansible", "kolla-ansible.yml")],
                ignore_limit=True,
                tags=None,
                check=False,
            ),
            mock.call(
                mock.ANY,
                [
                    utils.get_data_files_path("ansible",
                                              "kolla-openstack.yml"),
                ],
                ignore_limit=True,
                check=False,
            ),
            mock.call(
                mock.ANY,
                [
                    utils.get_data_files_path("ansible",
                                              "overcloud-extras.yml"),
                ],
                limit="overcloud",
                extra_vars={
                    "kayobe_action": "upgrade",
                }
            ),
            mock.call(
                mock.ANY,
                [
                    utils.get_data_files_path("ansible",
                                              "public-openrc.yml"),
                ],
                ignore_limit=True,
            ),
        ]
        self.assertListEqual(expected_calls, mock_run.call_args_list)

        expected_calls = [
            mock.call(
                mock.ANY,
                "prechecks"
            ),
            mock.call(
                mock.ANY,
                "upgrade"
            ),
            mock.call(
                mock.ANY,
                "post-deploy"
            ),
        ]
        self.assertListEqual(expected_calls, mock_kolla_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbooks")
    def test_overcloud_service_configuration_save_args(self, mock_run):
        command = commands.OvercloudServiceConfigurationSave(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args([
            "--exclude", "exclude1,exclude2",
            "--include", "include1,include2",
            "--node-config-dir", "/path/to/config",
            "--output-dir", "/path/to/output",
        ])
        result = command.run(parsed_args)
        self.assertEqual(0, result)
        expected_calls = [
            mock.call(
                mock.ANY,
                [
                    utils.get_data_files_path(
                        "ansible", "overcloud-service-config-save.yml"),
                ],
                extra_vars={
                    "exclude_patterns": "exclude1,exclude2",
                    "include_patterns": "include1,include2",
                    "config_save_path": "/path/to/output",
                    "node_config_directory": "/path/to/config",
                }
            ),
        ]
        self.assertListEqual(expected_calls, mock_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbooks")
    def test_overcloud_container_image_build(self, mock_run):
        command = commands.OvercloudContainerImageBuild(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args([])
        result = command.run(parsed_args)
        self.assertEqual(0, result)
        expected_calls = [
            mock.call(
                mock.ANY,
                [
                    utils.get_data_files_path(
                        "ansible", "container-image-builders-check.yml"),
                    utils.get_data_files_path("ansible", "kolla-build.yml"),
                    utils.get_data_files_path(
                        "ansible", "container-image-build.yml")
                ],
                extra_vars={
                    "container_image_sets": (
                        "{{ overcloud_container_image_sets }}"),
                    "push_images": False,
                    "nocache": False
                }
            ),
        ]
        self.assertListEqual(expected_calls, mock_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbooks")
    def test_overcloud_container_image_build_with_regex(self, mock_run):
        command = commands.OvercloudContainerImageBuild(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args(["--push", "^regex1$", "^regex2$"])
        result = command.run(parsed_args)
        self.assertEqual(0, result)
        expected_calls = [
            mock.call(
                mock.ANY,
                [
                    utils.get_data_files_path(
                        "ansible", "container-image-builders-check.yml"),
                    utils.get_data_files_path("ansible", "kolla-build.yml"),
                    utils.get_data_files_path(
                        "ansible", "container-image-build.yml")
                ],
                extra_vars={
                    "container_image_regexes": "^regex1$ ^regex2$",
                    "push_images": True,
                    "nocache": False
                }
            ),
        ]
        self.assertListEqual(expected_calls, mock_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbooks")
    def test_overcloud_host_image_build(self, mock_run):
        command = commands.OvercloudHostImageBuild(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args([])

        result = command.run(parsed_args)
        self.assertEqual(0, result)

        expected_calls = [
            mock.call(
                mock.ANY,
                [
                    utils.get_data_files_path(
                        "ansible", "overcloud-host-image-build.yml"),
                ],
                extra_vars={},
            ),
        ]
        self.assertListEqual(expected_calls, mock_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbooks")
    def test_overcloud_host_image_build_force_rebuild(self, mock_run):
        command = commands.OvercloudHostImageBuild(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args(["--force-rebuild"])

        result = command.run(parsed_args)
        self.assertEqual(0, result)

        expected_calls = [
            mock.call(
                mock.ANY,
                [
                    utils.get_data_files_path(
                        "ansible", "overcloud-host-image-build.yml"),
                ],
                extra_vars={"overcloud_host_image_force_rebuild": True},
            ),
        ]
        self.assertListEqual(expected_calls, mock_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbooks")
    def test_overcloud_deployment_image_build(self, mock_run):
        command = commands.OvercloudDeploymentImageBuild(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args([])

        result = command.run(parsed_args)
        self.assertEqual(0, result)

        expected_calls = [
            mock.call(
                mock.ANY,
                [
                    utils.get_data_files_path(
                        "ansible", "overcloud-ipa-build.yml"),
                ],
                extra_vars={},
            ),
        ]
        self.assertListEqual(expected_calls, mock_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbooks")
    def test_overcloud_deployment_image_build_force_rebuild(self, mock_run):
        command = commands.OvercloudDeploymentImageBuild(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args(["--force-rebuild"])

        result = command.run(parsed_args)
        self.assertEqual(0, result)

        expected_calls = [
            mock.call(
                mock.ANY,
                [
                    utils.get_data_files_path(
                        "ansible", "overcloud-ipa-build.yml"),
                ],
                extra_vars={"ipa_image_force_rebuild": True},
            ),
        ]
        self.assertListEqual(expected_calls, mock_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbooks")
    def test_overcloud_post_configure(self, mock_run):
        command = commands.OvercloudPostConfigure(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args([])

        result = command.run(parsed_args)
        self.assertEqual(0, result)

        expected_calls = [
            mock.call(
                mock.ANY,
                [
                    utils.get_data_files_path(
                        "ansible", "overcloud-ipa-images.yml"),
                    utils.get_data_files_path(
                        "ansible", "overcloud-introspection-rules.yml"),
                    utils.get_data_files_path("ansible", "overcloud-introspection-rules-dell-lldp-workaround.yml"),  # noqa
                    utils.get_data_files_path("ansible", "provision-net.yml"),
                    utils.get_data_files_path(
                        "ansible", "baremetal-compute-serial-console-post-config.yml"),  # noqa
                ],
            ),
        ]
        self.assertListEqual(expected_calls, mock_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbooks")
    def test_overcloud_swift_rings_generate(self, mock_run):
        command = commands.OvercloudSwiftRingsGenerate(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args([])

        result = command.run(parsed_args)
        self.assertEqual(0, result)

        expected_calls = [
            mock.call(
                mock.ANY,
                [
                    utils.get_data_files_path("ansible", "swift-rings.yml"),
                ],
            ),
        ]
        self.assertListEqual(expected_calls, mock_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbooks")
    def test_baremetal_compute_register(self, mock_run):
        command = commands.BaremetalComputeRegister(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args([])
        result = command.run(parsed_args)
        self.assertEqual(0, result)
        expected_calls = [
            mock.call(
                mock.ANY,
                [
                    utils.get_data_files_path(
                        "ansible", "baremetal-compute-register.yml"),
                ],
            ),
        ]
        self.assertListEqual(expected_calls, mock_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbooks")
    def test_baremetal_compute_inspect(self, mock_run):
        command = commands.BaremetalComputeInspect(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args([])
        result = command.run(parsed_args)
        self.assertEqual(0, result)
        expected_calls = [
            mock.call(
                mock.ANY,
                [
                    utils.get_data_files_path(
                        "ansible", "baremetal-compute-inspect.yml"),
                ],
            ),
        ]
        self.assertListEqual(expected_calls, mock_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbooks")
    def test_baremetal_compute_manage(self, mock_run):
        command = commands.BaremetalComputeManage(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args([])
        result = command.run(parsed_args)
        self.assertEqual(0, result)
        expected_calls = [
            mock.call(
                mock.ANY,
                [
                    utils.get_data_files_path(
                        "ansible", "baremetal-compute-manage.yml"),
                ],
            ),
        ]
        self.assertListEqual(expected_calls, mock_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbooks")
    def test_baremetal_compute_provide(self, mock_run):
        command = commands.BaremetalComputeProvide(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args([])
        result = command.run(parsed_args)
        self.assertEqual(0, result)
        expected_calls = [
            mock.call(
                mock.ANY,
                [
                    utils.get_data_files_path(
                        "ansible", "baremetal-compute-provide.yml"),
                ],
            ),
        ]
        self.assertListEqual(expected_calls, mock_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbooks")
    def test_baremetal_compute_rename(self, mock_run):
        command = commands.BaremetalComputeRename(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args([])
        result = command.run(parsed_args)
        self.assertEqual(0, result)
        expected_calls = [
            mock.call(
                mock.ANY,
                [
                    utils.get_data_files_path(
                        "ansible", "baremetal-compute-rename.yml"),
                ],
            ),
        ]
        self.assertListEqual(expected_calls, mock_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbooks")
    def test_baremetal_compute_serial_console_enable(self, mock_run):
        command = commands.BaremetalComputeSerialConsoleEnable(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args([])
        result = command.run(parsed_args)
        self.assertEqual(0, result)
        expected_calls = [
            mock.call(
                mock.ANY,
                [
                    utils.get_data_files_path(
                        "ansible", "baremetal-compute-serial-console.yml"),

                ],
                extra_vars={
                    "cmd": "enable",
                }
            ),
        ]
        self.assertListEqual(expected_calls, mock_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbooks")
    def test_baremetal_compute_serial_console_enable_with_limit(self,
                                                                mock_run):
        command = commands.BaremetalComputeSerialConsoleEnable(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args(["--baremetal-compute-limit",
                                         "sand-6-1"])
        result = command.run(parsed_args)
        self.assertEqual(0, result)
        expected_calls = [
            mock.call(
                mock.ANY,
                [
                    utils.get_data_files_path(
                        "ansible", "baremetal-compute-serial-console.yml"),

                ],
                extra_vars={
                    "cmd": "enable",
                    "console_compute_node_limit": "sand-6-1",
                }
            ),
        ]
        self.assertListEqual(expected_calls, mock_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbooks")
    def test_baremetal_compute_serial_console_disable(self, mock_run):
        command = commands.BaremetalComputeSerialConsoleDisable(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args([])
        result = command.run(parsed_args)
        self.assertEqual(0, result)
        expected_calls = [
            mock.call(
                mock.ANY,
                [
                    utils.get_data_files_path(
                        "ansible", "baremetal-compute-serial-console.yml"),

                ],
                extra_vars={
                    "cmd": "disable",
                }
            ),
        ]
        self.assertListEqual(expected_calls, mock_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbooks")
    def test_baremetal_compute_serial_console_disable_with_limit(self,
                                                                 mock_run):
        command = commands.BaremetalComputeSerialConsoleDisable(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args(["--baremetal-compute-limit",
                                         "sand-6-1"])
        result = command.run(parsed_args)
        self.assertEqual(0, result)
        expected_calls = [
            mock.call(
                mock.ANY,
                [
                    utils.get_data_files_path(
                        "ansible", "baremetal-compute-serial-console.yml"),

                ],
                extra_vars={
                    "cmd": "disable",
                    "console_compute_node_limit": "sand-6-1",
                }
            ),
        ]
        self.assertListEqual(expected_calls, mock_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbooks")
    def test_baremetal_compute_update_deployment_image(self, mock_run):
        command = commands.BaremetalComputeUpdateDeploymentImage(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args([])
        result = command.run(parsed_args)
        self.assertEqual(0, result)
        expected_calls = [
            mock.call(
                mock.ANY,
                [
                    utils.get_data_files_path(
                        "ansible", "overcloud-ipa-images.yml"),
                ],
                extra_vars={
                    "ipa_images_update_ironic_nodes": True,
                }
            ),
        ]
        self.assertListEqual(expected_calls, mock_run.call_args_list)

    @mock.patch.object(commands.KayobeAnsibleMixin,
                       "run_kayobe_playbooks")
    def test_baremetal_compute_update_deployment_image_with_limit(
            self, mock_run):
        command = commands.BaremetalComputeUpdateDeploymentImage(TestApp(), [])
        parser = command.get_parser("test")
        parsed_args = parser.parse_args(["--baremetal-compute-limit",
                                         "sand-6-1"])
        result = command.run(parsed_args)
        self.assertEqual(0, result)
        expected_calls = [
            mock.call(
                mock.ANY,
                [
                    utils.get_data_files_path(
                        "ansible", "overcloud-ipa-images.yml"),
                ],
                extra_vars={
                    "ipa_images_compute_node_limit": "sand-6-1",
                    "ipa_images_update_ironic_nodes": True,
                }
            ),
        ]
        self.assertListEqual(expected_calls, mock_run.call_args_list)


class TestHookDispatcher(unittest.TestCase):

    maxDiff = None

    @mock.patch.object(os.path, 'realpath')
    def test_hook_ordering(self, mock_realpath):
        mock_command = mock.MagicMock()
        dispatcher = commands.HookDispatcher(command=mock_command)
        dispatcher._find_hooks = mock.MagicMock()
        # Include multiple hook directories to show that they don't influence
        # the order.
        dispatcher._find_hooks.return_value = [
            "config/path/10-hook.yml",
            "config/path/5-hook.yml",
            "config/path/z-test-alphabetical.yml",
            "env/path/10-before-hook.yml",
            "env/path/5-multiple-dashes-in-name.yml",
            "env/path/no-prefix.yml"
        ]
        expected_result = [
            "config/path/5-hook.yml",
            "env/path/5-multiple-dashes-in-name.yml",
            "env/path/10-before-hook.yml",
            "config/path/10-hook.yml",
            "env/path/no-prefix.yml",
            "config/path/z-test-alphabetical.yml",
        ]
        mock_realpath.side_effect = lambda x: x
        actual = dispatcher.hooks(["config/path", "env/path"], "pre", None)
        self.assertListEqual(actual, expected_result)

    @mock.patch('kayobe.cli.commands.os.path')
    def test_hook_filter_all(self, mock_path):
        mock_command = mock.MagicMock()
        dispatcher = commands.HookDispatcher(command=mock_command)
        dispatcher._find_hooks = mock.MagicMock()
        dispatcher._find_hooks.return_value = [
            "5-hook.yml",
            "5-multiple-dashes-in-name.yml",
            "10-before-hook.yml",
            "10-hook.yml",
            "no-prefix.yml",
            "z-test-alphabetical.yml",
        ]
        mock_path.realpath.side_effect = lambda x: x
        actual = dispatcher.hooks(["config/path"], "pre", "all")
        self.assertListEqual(actual, [])

    @mock.patch('kayobe.cli.commands.os.path')
    def test_hook_filter_one(self, mock_path):
        mock_command = mock.MagicMock()
        dispatcher = commands.HookDispatcher(command=mock_command)
        dispatcher._find_hooks = mock.MagicMock()
        dispatcher._find_hooks.return_value = [
            "5-hook.yml",
            "5-multiple-dashes-in-name.yml",
            "10-before-hook.yml",
            "10-hook.yml",
            "no-prefix.yml",
            "z-test-alphabetical.yml",
        ]
        expected_result = [
            "5-hook.yml",
            "10-before-hook.yml",
            "10-hook.yml",
            "no-prefix.yml",
            "z-test-alphabetical.yml",
        ]
        mock_path.realpath.side_effect = lambda x: x
        actual = dispatcher.hooks(["config/path"], "pre",
                                  "5-multiple-dashes-in-name.yml")
        self.assertListEqual(actual, expected_result)

    @mock.patch.object(glob, 'glob')
    @mock.patch.object(os.path, 'exists')
    def test__find_hooks(self, mock_exists, mock_glob):
        mock_exists.return_value = True
        mock_command = mock.MagicMock()
        dispatcher = commands.HookDispatcher(command=mock_command)
        mock_glob.return_value = [
            "config/path/hooks/pre.d/1-hook.yml",
            "config/path/hooks/pre.d/5-hook.yml",
            "config/path/hooks/pre.d/10-hook.yml",
        ]
        expected_result = [
            "config/path/hooks/pre.d/1-hook.yml",
            "config/path/hooks/pre.d/10-hook.yml",
            "config/path/hooks/pre.d/5-hook.yml",
        ]
        actual = dispatcher._find_hooks(["config/path"], "pre")
        # Sort the result - it is not ordered at this stage.
        actual.sort()
        self.assertListEqual(actual, expected_result)

    @mock.patch.object(glob, 'glob')
    @mock.patch.object(os.path, 'exists')
    def test__find_hooks_with_env(self, mock_exists, mock_glob):
        mock_exists.return_value = True
        mock_command = mock.MagicMock()
        dispatcher = commands.HookDispatcher(command=mock_command)
        mock_glob.side_effect = [
            [
                "config/path/hooks/pre.d/all.yml",
                "config/path/hooks/pre.d/base-only.yml",
            ],
            [
                "env/path/hooks/pre.d/all.yml",
                "env/path/hooks/pre.d/env-only.yml",
            ]
        ]
        expected_result = [
            "config/path/hooks/pre.d/base-only.yml",
            "env/path/hooks/pre.d/all.yml",
            "env/path/hooks/pre.d/env-only.yml",
        ]
        actual = dispatcher._find_hooks(["config/path", "env/path"], "pre")
        # Sort the result - it is not ordered at this stage.
        actual.sort()
        self.assertListEqual(actual, expected_result)

    @mock.patch.object(glob, 'glob')
    @mock.patch.object(os.path, 'exists')
    def test__find_hooks_with_nested_envs(self, mock_exists, mock_glob):
        mock_exists.return_value = True
        mock_command = mock.MagicMock()
        dispatcher = commands.HookDispatcher(command=mock_command)
        mock_glob.side_effect = [
            [
                "config/path/hooks/pre.d/all.yml",
                "config/path/hooks/pre.d/base-only.yml",
                "config/path/hooks/pre.d/base-env1.yml",
                "config/path/hooks/pre.d/base-env2.yml",
            ],
            [
                "env1/path/hooks/pre.d/all.yml",
                "env1/path/hooks/pre.d/env1-only.yml",
                "env1/path/hooks/pre.d/base-env1.yml",
                "env1/path/hooks/pre.d/env1-env2.yml",
            ],
            [
                "env2/path/hooks/pre.d/all.yml",
                "env2/path/hooks/pre.d/env2-only.yml",
                "env2/path/hooks/pre.d/base-env2.yml",
                "env2/path/hooks/pre.d/env1-env2.yml",
            ]
        ]
        expected_result = [
            "config/path/hooks/pre.d/base-only.yml",
            "env1/path/hooks/pre.d/base-env1.yml",
            "env1/path/hooks/pre.d/env1-only.yml",
            "env2/path/hooks/pre.d/all.yml",
            "env2/path/hooks/pre.d/base-env2.yml",
            "env2/path/hooks/pre.d/env1-env2.yml",
            "env2/path/hooks/pre.d/env2-only.yml",
        ]
        actual = dispatcher._find_hooks(["config/path", "env1/path",
                                         "env2/path"], "pre")
        # Sort the result - it is not ordered at this stage.
        actual.sort()
        self.assertListEqual(actual, expected_result)

    @mock.patch.object(glob, 'glob')
    @mock.patch.object(os.path, 'exists')
    def test__find_hooks_non_existent(self, mock_exists, mock_glob):
        mock_exists.return_value = False
        mock_command = mock.MagicMock()
        dispatcher = commands.HookDispatcher(command=mock_command)
        expected_result = []
        actual = dispatcher._find_hooks(["config/path"], "pre")
        self.assertListEqual(actual, expected_result)
        mock_glob.assert_not_called()
