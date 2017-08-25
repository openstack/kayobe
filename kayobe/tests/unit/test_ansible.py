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
import shutil
import subprocess
import tempfile
import unittest

import mock

from kayobe import ansible
from kayobe import utils
from kayobe import vault


class TestCase(unittest.TestCase):

    @mock.patch.object(utils, "run_command")
    @mock.patch.object(ansible, "_get_vars_files")
    @mock.patch.object(ansible, "_validate_args")
    def test_run_playbooks(self, mock_validate, mock_vars, mock_run):
        mock_vars.return_value = ["/etc/kayobe/vars-file1.yml",
                                  "/etc/kayobe/vars-file2.yaml"]
        parser = argparse.ArgumentParser()
        ansible.add_args(parser)
        vault.add_args(parser)
        parsed_args = parser.parse_args([])
        ansible.run_playbooks(parsed_args, ["playbook1.yml", "playbook2.yml"])
        expected_cmd = [
            "ansible-playbook",
            "--inventory", "/etc/kayobe/inventory",
            "-e", "@/etc/kayobe/vars-file1.yml",
            "-e", "@/etc/kayobe/vars-file2.yaml",
            "playbook1.yml",
            "playbook2.yml",
        ]
        mock_run.assert_called_once_with(expected_cmd, quiet=False)
        mock_vars.assert_called_once_with("/etc/kayobe")

    @mock.patch.object(utils, "run_command")
    @mock.patch.object(ansible, "_get_vars_files")
    @mock.patch.object(ansible, "_validate_args")
    def test_run_playbooks_all_the_args(self, mock_validate, mock_vars,
                                        mock_run):
        mock_vars.return_value = ["/path/to/config/vars-file1.yml",
                                  "/path/to/config/vars-file2.yaml"]
        parser = argparse.ArgumentParser()
        ansible.add_args(parser)
        vault.add_args(parser)
        args = [
            "-b",
            "-C",
            "--config-path", "/path/to/config",
            "-e", "ev_name1=ev_value1",
            "-i", "/path/to/inventory",
            "-l", "group1:host",
            "-t", "tag1,tag2",
            "-lt",
        ]
        parsed_args = parser.parse_args(args)
        ansible.run_playbooks(parsed_args, ["playbook1.yml", "playbook2.yml"],
                              verbose_level=2)
        expected_cmd = [
            "ansible-playbook",
            "-vv",
            "--list-tasks",
            "--inventory", "/path/to/inventory",
            "-e", "@/path/to/config/vars-file1.yml",
            "-e", "@/path/to/config/vars-file2.yaml",
            "-e", "ev_name1=ev_value1",
            "--become",
            "--check",
            "--limit", "group1:host",
            "--tags", "tag1,tag2",
            "playbook1.yml",
            "playbook2.yml",
        ]
        mock_run.assert_called_once_with(expected_cmd, quiet=False)
        mock_vars.assert_called_once_with("/path/to/config")

    @mock.patch.object(utils, "run_command")
    @mock.patch.object(ansible, "_get_vars_files")
    @mock.patch.object(ansible, "_validate_args")
    def test_run_playbooks_all_the_long_args(self, mock_validate, mock_vars,
                                             mock_run):
        mock_vars.return_value = ["/path/to/config/vars-file1.yml",
                                  "/path/to/config/vars-file2.yaml"]
        parser = argparse.ArgumentParser()
        ansible.add_args(parser)
        vault.add_args(parser)
        args = [
            "--ask-vault-pass",
            "--become",
            "--check",
            "--config-path", "/path/to/config",
            "--extra-vars", "ev_name1=ev_value1",
            "--inventory", "/path/to/inventory",
            "--limit", "group1:host1",
            "--tags", "tag1,tag2",
            "--list-tasks",
        ]
        parsed_args = parser.parse_args(args)
        ansible.run_playbooks(parsed_args, ["playbook1.yml", "playbook2.yml"])
        expected_cmd = [
            "ansible-playbook",
            "--list-tasks",
            "--ask-vault-pass",
            "--inventory", "/path/to/inventory",
            "-e", "@/path/to/config/vars-file1.yml",
            "-e", "@/path/to/config/vars-file2.yaml",
            "-e", "ev_name1=ev_value1",
            "--become",
            "--check",
            "--limit", "group1:host1",
            "--tags", "tag1,tag2",
            "playbook1.yml",
            "playbook2.yml",
        ]
        mock_run.assert_called_once_with(expected_cmd, quiet=False)
        mock_vars.assert_called_once_with("/path/to/config")

    @mock.patch.object(utils, "run_command")
    @mock.patch.object(ansible, "_get_vars_files")
    @mock.patch.object(ansible, "_validate_args")
    def test_run_playbooks_vault_password_file(self, mock_validate, mock_vars,
                                               mock_run):
        mock_vars.return_value = []
        parser = argparse.ArgumentParser()
        ansible.add_args(parser)
        vault.add_args(parser)
        args = [
            "--vault-password-file", "/path/to/vault/pw",
        ]
        parsed_args = parser.parse_args(args)
        ansible.run_playbooks(parsed_args, ["playbook1.yml"])
        expected_cmd = [
            "ansible-playbook",
            "--vault-password-file", "/path/to/vault/pw",
            "--inventory", "/etc/kayobe/inventory",
            "playbook1.yml",
        ]
        mock_run.assert_called_once_with(expected_cmd, quiet=False)

    @mock.patch.dict(os.environ, {"KAYOBE_VAULT_PASSWORD": "test-pass"})
    @mock.patch.object(utils, "run_command")
    @mock.patch.object(ansible, "_get_vars_files")
    @mock.patch.object(ansible, "_validate_args")
    def test_run_playbooks_vault_password_helper(self, mock_validate,
                                                 mock_vars, mock_run):
        mock_vars.return_value = []
        parser = argparse.ArgumentParser()
        mock_run.return_value = "/path/to/kayobe-vault-password-helper"
        ansible.add_args(parser)
        vault.add_args(parser)
        mock_run.assert_called_once_with(
            ["which", "kayobe-vault-password-helper"], check_output=True)
        mock_run.reset_mock()
        parsed_args = parser.parse_args([])
        ansible.run_playbooks(parsed_args, ["playbook1.yml"])
        expected_cmd = [
            "ansible-playbook",
            "--vault-password-file", "/path/to/kayobe-vault-password-helper",
            "--inventory", "/etc/kayobe/inventory",
            "playbook1.yml",
        ]
        mock_run.assert_called_once_with(expected_cmd, quiet=False)

    @mock.patch.object(utils, "run_command")
    @mock.patch.object(ansible, "_get_vars_files")
    @mock.patch.object(ansible, "_validate_args")
    def test_run_playbooks_vault_ask_and_file(self, mock_validate, mock_vars,
                                              mock_run):
        mock_vars.return_value = []
        parser = argparse.ArgumentParser()
        ansible.add_args(parser)
        vault.add_args(parser)
        args = [
            "--ask-vault-pass",
            "--vault-password-file", "/path/to/vault/pw",
        ]
        self.assertRaises(SystemExit, parser.parse_args, args)

    @mock.patch.object(utils, "run_command")
    @mock.patch.object(ansible, "_get_vars_files")
    @mock.patch.object(ansible, "_validate_args")
    def test_run_playbooks_func_args(self, mock_validate, mock_vars, mock_run):
        mock_vars.return_value = ["/etc/kayobe/vars-file1.yml",
                                  "/etc/kayobe/vars-file2.yaml"]
        parser = argparse.ArgumentParser()
        ansible.add_args(parser)
        vault.add_args(parser)
        args = [
            "--extra-vars", "ev_name1=ev_value1",
            "--limit", "group1:host1",
            "--tags", "tag1,tag2",
        ]
        parsed_args = parser.parse_args(args)
        kwargs = {
            "extra_vars": {"ev_name2": "ev_value2"},
            "limit": "group2:host2",
            "tags": "tag3,tag4",
            "verbose_level": 0,
            "check": True,
        }
        ansible.run_playbooks(parsed_args, ["playbook1.yml", "playbook2.yml"],
                              **kwargs)
        expected_cmd = [
            "ansible-playbook",
            "--inventory", "/etc/kayobe/inventory",
            "-e", "@/etc/kayobe/vars-file1.yml",
            "-e", "@/etc/kayobe/vars-file2.yaml",
            "-e", "ev_name1=ev_value1",
            "-e", "ev_name2=ev_value2",
            "--check",
            "--limit", "group1:host1:&group2:host2",
            "--tags", "tag1,tag2,tag3,tag4",
            "playbook1.yml",
            "playbook2.yml",
        ]
        mock_run.assert_called_once_with(expected_cmd, quiet=False)
        mock_vars.assert_called_once_with("/etc/kayobe")

    @mock.patch.object(utils, "run_command")
    @mock.patch.object(ansible, "_get_vars_files")
    @mock.patch.object(ansible, "_validate_args")
    def test_run_playbooks_failure(self, mock_validate, mock_vars, mock_run):
        parser = argparse.ArgumentParser()
        ansible.add_args(parser)
        vault.add_args(parser)
        parsed_args = parser.parse_args([])
        mock_run.side_effect = subprocess.CalledProcessError(1, "dummy")
        self.assertRaises(SystemExit,
                          ansible.run_playbooks, parsed_args, ["command"])

    @mock.patch.object(shutil, 'rmtree')
    @mock.patch.object(utils, 'read_yaml_file')
    @mock.patch.object(os, 'listdir')
    @mock.patch.object(ansible, 'run_playbook')
    @mock.patch.object(tempfile, 'mkdtemp')
    def test_config_dump(self, mock_mkdtemp, mock_run, mock_listdir, mock_read,
                         mock_rmtree):
        parser = argparse.ArgumentParser()
        parsed_args = parser.parse_args([])
        dump_dir = mock_mkdtemp.return_value
        mock_listdir.return_value = ["host1.yml", "host2.yml"]
        mock_read.side_effect = [
            {"var1": "value1"},
            {"var2": "value2"}
        ]
        result = ansible.config_dump(parsed_args)
        expected_result = {
            "host1": {"var1": "value1"},
            "host2": {"var2": "value2"},
        }
        self.assertEqual(result, expected_result)
        mock_run.assert_called_once_with(parsed_args,
                                         "ansible/dump-config.yml",
                                         extra_vars={
                                             "dump_path": dump_dir,
                                         },
                                         quiet=True, verbose_level=None,
                                         check=False)
        mock_rmtree.assert_called_once_with(dump_dir)
        mock_listdir.assert_called_once_with(dump_dir)
        mock_read.assert_has_calls([
            mock.call(os.path.join(dump_dir, "host1.yml")),
            mock.call(os.path.join(dump_dir, "host2.yml")),
        ])
