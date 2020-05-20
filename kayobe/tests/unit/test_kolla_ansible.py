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

import argparse
import os
import subprocess
import unittest
from unittest import mock

from kayobe import ansible
from kayobe import kolla_ansible
from kayobe import utils
from kayobe import vault


@mock.patch.object(os, "getcwd", new=lambda: "/path/to/cwd")
@mock.patch.dict(os.environ, clear=True)
class TestCase(unittest.TestCase):

    @mock.patch.object(utils, "run_command")
    @mock.patch.object(kolla_ansible, "_validate_args")
    def test_run(self, mock_validate, mock_run):
        parser = argparse.ArgumentParser()
        ansible.add_args(parser)
        kolla_ansible.add_args(parser)
        vault.add_args(parser)
        parsed_args = parser.parse_args([])
        kolla_ansible.run(parsed_args, "command", "overcloud")
        expected_cmd = [
            ".", "/path/to/cwd/venvs/kolla-ansible/bin/activate", "&&",
            "kolla-ansible", "command",
            "--inventory", "/etc/kolla/inventory/overcloud",
        ]
        expected_cmd = " ".join(expected_cmd)
        mock_run.assert_called_once_with(expected_cmd, shell=True, quiet=False,
                                         env={})

    @mock.patch.object(utils, "run_command")
    @mock.patch.object(kolla_ansible, "_validate_args")
    def test_run_all_the_args(self, mock_validate, mock_run):
        parser = argparse.ArgumentParser()
        ansible.add_args(parser)
        kolla_ansible.add_args(parser)
        vault.add_args(parser)
        args = [
            "--kolla-config-path", "/path/to/config",
            "-ke", "ev_name1=ev_value1",
            "-ki", "/path/to/inventory",
            "-kl", "host1:host2",
            "-kt", "tag1,tag2",
        ]
        parsed_args = parser.parse_args(args)
        kolla_ansible.run(parsed_args, "command", "overcloud")
        expected_cmd = [
            ".", "/path/to/cwd/venvs/kolla-ansible/bin/activate", "&&",
            "kolla-ansible", "command",
            "--inventory", "/path/to/inventory",
            "--configdir", "/path/to/config",
            "--passwords", "/path/to/config/passwords.yml",
            "-e", "ev_name1=ev_value1",
            "--limit", "host1:host2",
            "--tags", "tag1,tag2",
        ]
        expected_cmd = " ".join(expected_cmd)
        mock_run.assert_called_once_with(expected_cmd, shell=True, quiet=False,
                                         env={})

    @mock.patch.object(utils, "run_command")
    @mock.patch.object(kolla_ansible, "_validate_args")
    @mock.patch.object(vault, "_ask_vault_pass")
    def test_run_all_the_long_args(self, mock_ask, mock_validate, mock_run):
        parser = argparse.ArgumentParser()
        ansible.add_args(parser)
        kolla_ansible.add_args(parser)
        vault.add_args(parser)
        mock_ask.return_value = "test-pass"
        args = [
            "--ask-vault-pass",
            "--kolla-config-path", "/path/to/config",
            "--kolla-extra-vars", "ev_name1=ev_value1",
            "--kolla-inventory", "/path/to/inventory",
            "--kolla-limit", "host1:host2",
            "--kolla-skip-tags", "tag3,tag4",
            "--kolla-tags", "tag1,tag2",
        ]
        parsed_args = parser.parse_args(args)
        mock_run.return_value = "/path/to/kayobe-vault-password-helper"
        kolla_ansible.run(parsed_args, "command", "overcloud")
        expected_cmd = [
            ".", "/path/to/cwd/venvs/kolla-ansible/bin/activate", "&&",
            "kolla-ansible", "command",
            "--key", "/path/to/kayobe-vault-password-helper",
            "--inventory", "/path/to/inventory",
            "--configdir", "/path/to/config",
            "--passwords", "/path/to/config/passwords.yml",
            "-e", "ev_name1=ev_value1",
            "--limit", "host1:host2",
            "--skip-tags", "tag3,tag4",
            "--tags", "tag1,tag2",
        ]
        expected_cmd = " ".join(expected_cmd)
        expected_env = {"KAYOBE_VAULT_PASSWORD": "test-pass"}
        expected_calls = [
            mock.call(["which", "kayobe-vault-password-helper"],
                      check_output=True, universal_newlines=True),
            mock.call(expected_cmd, shell=True, quiet=False, env=expected_env)
        ]
        self.assertEqual(expected_calls, mock_run.mock_calls)

    @mock.patch.object(utils, "run_command")
    @mock.patch.object(kolla_ansible, "_validate_args")
    @mock.patch.object(vault, "update_environment")
    def test_run_vault_password_file(self, mock_update, mock_validate,
                                     mock_run):
        parser = argparse.ArgumentParser()
        ansible.add_args(parser)
        kolla_ansible.add_args(parser)
        vault.add_args(parser)
        args = [
            "--vault-password-file", "/path/to/vault/pw",
        ]
        parsed_args = parser.parse_args(args)
        kolla_ansible.run(parsed_args, "command", "overcloud")
        expected_cmd = [
            ".", "/path/to/cwd/venvs/kolla-ansible/bin/activate", "&&",
            "kolla-ansible", "command",
            "--key", "/path/to/vault/pw",
            "--inventory", "/etc/kolla/inventory/overcloud",
        ]
        expected_cmd = " ".join(expected_cmd)
        mock_run.assert_called_once_with(expected_cmd, shell=True, quiet=False,
                                         env={})
        mock_update.assert_called_once_with(mock.ANY, {})

    @mock.patch.dict(os.environ, {"KAYOBE_VAULT_PASSWORD": "test-pass"})
    @mock.patch.object(utils, "run_command")
    @mock.patch.object(kolla_ansible, "_validate_args")
    @mock.patch.object(vault, "update_environment")
    def test_run_vault_password_helper(self, mock_update, mock_vars, mock_run):
        mock_vars.return_value = []
        parser = argparse.ArgumentParser()
        mock_run.return_value = "/path/to/kayobe-vault-password-helper"
        ansible.add_args(parser)
        kolla_ansible.add_args(parser)
        vault.add_args(parser)
        mock_run.assert_called_once_with(
            ["which", "kayobe-vault-password-helper"], check_output=True,
            universal_newlines=True)
        mock_run.reset_mock()
        parsed_args = parser.parse_args([])
        kolla_ansible.run(parsed_args, "command", "overcloud")
        expected_cmd = [
            ".", "/path/to/cwd/venvs/kolla-ansible/bin/activate", "&&",
            "kolla-ansible", "command",
            "--key", "/path/to/kayobe-vault-password-helper",
            "--inventory", "/etc/kolla/inventory/overcloud",
        ]
        expected_cmd = " ".join(expected_cmd)
        expected_env = {"KAYOBE_VAULT_PASSWORD": "test-pass"}
        mock_run.assert_called_once_with(expected_cmd, shell=True, quiet=False,
                                         env=expected_env)
        mock_update.assert_called_once_with(mock.ANY, expected_env)

    @mock.patch.object(utils, "run_command")
    @mock.patch.object(kolla_ansible, "_validate_args")
    def test_run_func_args(self, mock_validate, mock_run):
        parser = argparse.ArgumentParser()
        ansible.add_args(parser)
        kolla_ansible.add_args(parser)
        vault.add_args(parser)
        args = [
            "--kolla-extra-vars", "ev_name1=ev_value1",
            "--kolla-tags", "tag1,tag2",
        ]
        parsed_args = parser.parse_args(args)
        kwargs = {
            "extra_vars": {"ev_name2": "ev_value2"},
            "tags": "tag3,tag4",
            "verbose_level": 1,
            "extra_args": ["--arg1", "--arg2"],
        }
        kolla_ansible.run(parsed_args, "command", "overcloud", **kwargs)
        expected_cmd = [
            ".", "/path/to/cwd/venvs/kolla-ansible/bin/activate", "&&",
            "kolla-ansible", "command",
            "-v",
            "--inventory", "/etc/kolla/inventory/overcloud",
            "-e", "ev_name1=ev_value1",
            "-e", "ev_name2='ev_value2'",
            "--tags", "tag1,tag2,tag3,tag4",
            "--arg1", "--arg2",
        ]
        expected_cmd = " ".join(expected_cmd)
        mock_run.assert_called_once_with(expected_cmd, shell=True, quiet=False,
                                         env={})

    @mock.patch.object(utils, "run_command")
    @mock.patch.object(utils, "is_readable_file")
    @mock.patch.object(kolla_ansible, "_validate_args")
    def test_run_custom_ansible_cfg(self, mock_validate, mock_readable,
                                    mock_run):
        mock_readable.return_value = {"result": True}
        parser = argparse.ArgumentParser()
        ansible.add_args(parser)
        kolla_ansible.add_args(parser)
        vault.add_args(parser)
        parsed_args = parser.parse_args([])
        kolla_ansible.run(parsed_args, "command", "overcloud")
        expected_cmd = [
            ".", "/path/to/cwd/venvs/kolla-ansible/bin/activate", "&&",
            "kolla-ansible", "command",
            "--inventory", "/etc/kolla/inventory/overcloud",
        ]
        expected_cmd = " ".join(expected_cmd)
        expected_env = {"ANSIBLE_CONFIG": "/etc/kayobe/kolla/ansible.cfg"}
        mock_run.assert_called_once_with(expected_cmd, shell=True, quiet=False,
                                         env=expected_env)
        mock_readable.assert_called_once_with("/etc/kayobe/kolla/ansible.cfg")

    @mock.patch.object(utils, "run_command")
    @mock.patch.object(utils, "is_readable_file")
    @mock.patch.object(kolla_ansible, "_validate_args")
    def test_run_custom_ansible_cfg_2(self, mock_validate, mock_readable,
                                      mock_run):
        mock_readable.side_effect = [{"result": False}, {"result": True}]
        parser = argparse.ArgumentParser()
        ansible.add_args(parser)
        kolla_ansible.add_args(parser)
        vault.add_args(parser)
        parsed_args = parser.parse_args([])
        kolla_ansible.run(parsed_args, "command", "overcloud")
        expected_cmd = [
            ".", "/path/to/cwd/venvs/kolla-ansible/bin/activate", "&&",
            "kolla-ansible", "command",
            "--inventory", "/etc/kolla/inventory/overcloud",
        ]
        expected_cmd = " ".join(expected_cmd)
        expected_env = {"ANSIBLE_CONFIG": "/etc/kayobe/ansible.cfg"}
        mock_run.assert_called_once_with(expected_cmd, shell=True, quiet=False,
                                         env=expected_env)
        expected_calls = [
            mock.call("/etc/kayobe/kolla/ansible.cfg"),
            mock.call("/etc/kayobe/ansible.cfg"),
        ]
        self.assertEqual(mock_readable.call_args_list, expected_calls)

    @mock.patch.object(utils, "run_command")
    @mock.patch.object(utils, "is_readable_file")
    @mock.patch.object(kolla_ansible, "_validate_args")
    def test_run_custom_ansible_cfg_env(self, mock_validate, mock_readable,
                                        mock_run):
        mock_readable.return_value = {"result": True}
        os.environ["ANSIBLE_CONFIG"] = "/path/to/ansible.cfg"
        parser = argparse.ArgumentParser()
        ansible.add_args(parser)
        kolla_ansible.add_args(parser)
        vault.add_args(parser)
        parsed_args = parser.parse_args([])
        kolla_ansible.run(parsed_args, "command", "overcloud")
        expected_cmd = [
            ".", "/path/to/cwd/venvs/kolla-ansible/bin/activate", "&&",
            "kolla-ansible", "command",
            "--inventory", "/etc/kolla/inventory/overcloud",
        ]
        expected_cmd = " ".join(expected_cmd)
        expected_env = {"ANSIBLE_CONFIG": "/path/to/ansible.cfg"}
        mock_run.assert_called_once_with(expected_cmd, shell=True, quiet=False,
                                         env=expected_env)
        mock_readable.assert_called_once_with("/etc/kayobe/kolla/ansible.cfg")

    @mock.patch.object(utils, "run_command")
    @mock.patch.object(kolla_ansible, "_validate_args")
    def test_run_failure(self, mock_validate, mock_run):
        parser = argparse.ArgumentParser()
        ansible.add_args(parser)
        kolla_ansible.add_args(parser)
        vault.add_args(parser)
        parsed_args = parser.parse_args([])
        mock_run.side_effect = subprocess.CalledProcessError(1, "dummy")
        self.assertRaises(SystemExit,
                          kolla_ansible.run, parsed_args, "command",
                          "overcloud")
