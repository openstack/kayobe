# Copyright (c) 2018 StackHPC Ltd.
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
import unittest
from unittest import mock

from kayobe import utils
from kayobe import vault


class TestCase(unittest.TestCase):

    @mock.patch.object(vault.utils, "run_command", autospec=True)
    def test__get_vault_password_helper(self, mock_run):
        mock_run.return_value = "fake-password\n"
        result = vault._get_vault_password_helper()
        mock_run.assert_called_once_with(
            ["which", "kayobe-vault-password-helper"], check_output=True,
            universal_newlines=True)
        self.assertEqual('fake-password', result)

    def test_validate_args_ok(self):
        parser = argparse.ArgumentParser()
        vault.add_args(parser)
        parsed_args = parser.parse_args([])
        vault.validate_args(parsed_args)

    @mock.patch.dict(os.environ, {"KAYOBE_VAULT_PASSWORD": "test-pass"})
    def test_validate_args_env(self):
        parser = argparse.ArgumentParser()
        vault.add_args(parser)
        parsed_args = parser.parse_args([])
        vault.validate_args(parsed_args)

    @mock.patch.dict(os.environ, {"KAYOBE_VAULT_PASSWORD": "test-pass"})
    def test_validate_args_ask_vault_pass(self):
        parser = argparse.ArgumentParser()
        vault.add_args(parser)
        parsed_args = parser.parse_args(["--ask-vault-pass"])
        self.assertRaises(SystemExit, vault.validate_args, parsed_args)

    @mock.patch.dict(os.environ, {"KAYOBE_VAULT_PASSWORD": "test-pass"})
    def test_validate_args_vault_password_file(self):
        parser = argparse.ArgumentParser()
        vault.add_args(parser)
        parsed_args = parser.parse_args(["--vault-password-file",
                                         "/path/to/file"])
        self.assertRaises(SystemExit, vault.validate_args, parsed_args)

    @mock.patch.object(vault.getpass, 'getpass')
    def test__ask_vault_pass(self, mock_getpass):
        mock_getpass.return_value = 'test-pass'

        # Call twice to verify that the user is only prompted once.
        result = vault._ask_vault_pass()
        self.assertEqual('test-pass', result)
        mock_getpass.assert_called_once_with("Vault password: ")

        result = vault._ask_vault_pass()
        self.assertEqual('test-pass', result)
        mock_getpass.assert_called_once_with("Vault password: ")

    @mock.patch.object(utils, 'read_file')
    def test__read_vault_password_file(self, mock_read):
        mock_read.return_value = "test-pass\n"
        result = vault._read_vault_password_file("/path/to/file")
        self.assertEqual("test-pass", result)
        mock_read.assert_called_once_with("/path/to/file")

    def test_update_environment_no_vault(self):
        parser = argparse.ArgumentParser()
        vault.add_args(parser)
        parsed_args = parser.parse_args([])
        env = {}
        vault.update_environment(parsed_args, env)
        self.assertEqual({}, env)

    @mock.patch.object(vault, '_ask_vault_pass')
    def test_update_environment_prompt(self, mock_ask):
        mock_ask.return_value = "test-pass"
        parser = argparse.ArgumentParser()
        vault.add_args(parser)
        parsed_args = parser.parse_args(["--ask-vault-pass"])
        env = {}
        vault.update_environment(parsed_args, env)
        self.assertEqual({"KAYOBE_VAULT_PASSWORD": "test-pass"}, env)
        mock_ask.assert_called_once_with()

    @mock.patch.object(vault, '_read_vault_password_file')
    def test_update_environment_file(self, mock_read):
        mock_read.return_value = "test-pass"
        parser = argparse.ArgumentParser()
        vault.add_args(parser)
        args = ["--vault-password-file", "/path/to/file"]
        parsed_args = parser.parse_args(args)
        env = {}
        vault.update_environment(parsed_args, env)
        self.assertEqual({"KAYOBE_VAULT_PASSWORD": "test-pass"}, env)
        mock_read.assert_called_once_with("/path/to/file")
