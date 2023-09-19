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

import os
import subprocess
import unittest
from unittest import mock

import yaml

from kayobe import exception
from kayobe import utils


class TestCase(unittest.TestCase):

    maxDiff = None

    @mock.patch.object(utils, "run_command")
    def test_galaxy_role_install(self, mock_run):
        utils.galaxy_role_install("/path/to/role/file", "/path/to/roles")
        mock_run.assert_called_once_with(["ansible-galaxy", "role", "install",
                                          "--roles-path", "/path/to/roles",
                                          "--role-file", "/path/to/role/file"])

    @mock.patch.object(utils, "run_command")
    def test_galaxy_role_install_failure(self, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(1, "command")
        self.assertRaises(SystemExit,
                          utils.galaxy_role_install, "/path/to/role/file",
                          "/path/to/roles")

    @mock.patch.object(utils, "run_command")
    @mock.patch.object(utils, "read_yaml_file")
    def test_galaxy_collection_install(self, mock_read, mock_run):
        mock_read.return_value = {"collections": []}
        utils.galaxy_collection_install("/path/to/collection/file",
                                        "/path/to/collections")
        mock_run.assert_called_once_with(["ansible-galaxy", "collection",
                                          "install", "--collections-path",
                                          "/path/to/collections",
                                          "--requirements-file",
                                          "/path/to/collection/file"])

    @mock.patch.object(utils, "run_command")
    @mock.patch.object(utils, "read_yaml_file")
    def test_galaxy_collection_install_failure(self, mock_read, mock_run):
        mock_read.return_value = {"collections": []}
        mock_run.side_effect = subprocess.CalledProcessError(1, "command")
        self.assertRaises(SystemExit,
                          utils.galaxy_collection_install,
                          "/path/to/collection/file", "/path/to/collections")

    @mock.patch.object(utils, "run_command")
    @mock.patch.object(utils, "read_file")
    def test_galaxy_collection_read_failure(self, mock_read, mock_run):
        mock_read.side_effect = IOError
        self.assertRaises(SystemExit,
                          utils.galaxy_collection_install,
                          "/path/to/collection/file", "/path/to/collections")

    @mock.patch.object(utils, "run_command")
    @mock.patch.object(utils, "read_yaml_file")
    def test_galaxy_collection_no_collections(self, mock_read, mock_run):
        mock_read.return_value = {"roles": []}
        utils.galaxy_collection_install("/path/to/collection/file",
                                        "/path/to/collections")
        mock_run.assert_called_once_with(["ansible-galaxy", "collection",
                                          "install", "--collections-path",
                                          "/path/to/collections",
                                          "--requirements-file",
                                          "/path/to/collection/file"])

    @mock.patch.object(utils, "run_command")
    @mock.patch.object(utils, "read_yaml_file")
    def test_galaxy_collection_legacy_format(self, mock_read, mock_run):
        mock_read.return_value = []
        utils.galaxy_collection_install("/path/to/collection/file",
                                        "/path/to/collections")
        self.assertFalse(mock_run.called)

    @mock.patch.object(utils, "run_command")
    def test_galaxy_remove(self, mock_run):
        utils.galaxy_remove(["role1", "role2"], "/path/to/roles")
        mock_run.assert_called_once_with(["ansible-galaxy", "role", "remove",
                                          "--roles-path", "/path/to/roles",
                                          "role1", "role2"])

    @mock.patch.object(utils, "run_command")
    def test_galaxy_remove_failure(self, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(1, "command")
        self.assertRaises(SystemExit,
                          utils.galaxy_remove, ["role1", "role2"],
                          "/path/to/roles")

    @mock.patch.object(utils, "read_file")
    @mock.patch.object(yaml, "safe_load", wraps=yaml.safe_load)
    def test_read_yaml_file(self, mock_load, mock_read):
        config = """---
key1: value1
key2: value2
"""
        mock_read.return_value = config
        result = utils.read_yaml_file("/path/to/file")
        self.assertEqual(result, {"key1": "value1", "key2": "value2"})
        mock_read.assert_called_once_with("/path/to/file")
        mock_load.assert_called_once_with(config)

    @mock.patch.object(utils, "read_file")
    def test_read_yaml_file_open_failure(self, mock_read):
        mock_read.side_effect = IOError
        self.assertRaises(SystemExit, utils.read_yaml_file, "/path/to/file")

    @mock.patch.object(utils, "read_file")
    def test_read_yaml_file_not_yaml(self, mock_read):
        mock_read.return_value = "[1{!"
        self.assertRaises(SystemExit, utils.read_yaml_file, "/path/to/file")

    @mock.patch.object(subprocess, "check_call")
    def test_run_command(self, mock_call):
        output = utils.run_command(["command", "to", "run"])
        mock_call.assert_called_once_with(["command", "to", "run"])
        self.assertIsNone(output)

    @mock.patch("kayobe.utils.open")
    @mock.patch.object(subprocess, "check_call")
    def test_run_command_quiet(self, mock_call, mock_open):
        mock_devnull = mock_open.return_value.__enter__.return_value
        output = utils.run_command(["command", "to", "run"], quiet=True)
        mock_call.assert_called_once_with(["command", "to", "run"],
                                          stdout=mock_devnull,
                                          stderr=mock_devnull)
        self.assertIsNone(output)

    @mock.patch.object(subprocess, "check_output")
    def test_run_command_check_output(self, mock_output):
        mock_output.return_value = "command output"
        output = utils.run_command(["command", "to", "run"], check_output=True)
        mock_output.assert_called_once_with(["command", "to", "run"])
        self.assertEqual(output, "command output")

    @mock.patch.object(subprocess, "check_call")
    def test_run_command_failure(self, mock_call):
        mock_call.side_effect = subprocess.CalledProcessError(1, "command")
        self.assertRaises(subprocess.CalledProcessError, utils.run_command,
                          ["command", "to", "run"])

    def test_quote_and_escape_no_whitespace(self):
        self.assertEqual("'foo'", utils.quote_and_escape("foo"))

    def test_quote_and_escape_whitespace(self):
        self.assertEqual("'foo bar'", utils.quote_and_escape("foo bar"))

    def test_quote_and_escape_whitespace_with_quotes(self):
        self.assertEqual("'foo '\\''bar'\\'''",
                         utils.quote_and_escape("foo 'bar'"))

    def test_quote_and_escape_non_string(self):
        self.assertEqual(True, utils.quote_and_escape(True))

    def test_escape_jinja(self):
        value = "string to escape"
        expected = "{{'c3RyaW5nIHRvIGVzY2FwZQ==' | b64decode }}"
        self.assertEqual(expected, utils.escape_jinja(value))

    def test_detect_install_prefix(self):
        tmp_path = os.path.realpath('/tmp')
        path = "%s/test/local/lib/python3.6/dist-packages" % tmp_path
        expected = os.path.normpath("%s/test/local/" % tmp_path)
        result = utils._detect_install_prefix(path)
        self.assertEqual(expected, os.path.normpath(result))

    def test_detect_install_prefix_multiple_lib_components(self):
        tmp_path = os.path.realpath('/tmp')
        path = "%s/lib/test/local/lib/python3.6/dist-packages" % tmp_path
        expected = os.path.normpath("%s/lib/test/local/" % tmp_path)
        result = utils._detect_install_prefix(path)
        self.assertEqual(expected, os.path.normpath(result))

    def test_intersect_limits_no_arg_no_cli(self):
        result = utils.intersect_limits(None, None)
        self.assertEqual("", result)

    def test_intersect_limits_arg_no_cli(self):
        result = utils.intersect_limits("foo", None)
        self.assertEqual("foo", result)

    def test_intersect_limits_arg_no_cli_comma(self):
        result = utils.intersect_limits("foo,bar", None)
        self.assertEqual("foo,bar", result)

    def test_intersect_limits_arg_no_cli_colon(self):
        result = utils.intersect_limits("foo:bar", None)
        self.assertEqual("foo:bar", result)

    def test_intersect_limits_arg_no_cli_colon_and_comma(self):
        self.assertRaises(exception.Error,
                          utils.intersect_limits, "foo:bar,baz", None)

    def test_intersect_limits_no_arg_cli(self):
        result = utils.intersect_limits(None, "foo")
        self.assertEqual("foo", result)

    def test_intersect_limits_arg_and_cli(self):
        result = utils.intersect_limits("foo", "bar")
        self.assertEqual("foo:&bar", result)

    def test_intersect_limits_arg_and_cli_comma(self):
        result = utils.intersect_limits("foo,bar", "baz")
        self.assertEqual("foo,bar,&baz", result)

    def test_intersect_limits_arg_and_cli_colon(self):
        result = utils.intersect_limits("foo:bar", "baz")
        self.assertEqual("foo:bar:&baz", result)

    def test_environment_finder_with_single_environment(self):
        finder = utils.EnvironmentFinder('/etc/kayobe', 'environment-A')
        environments = finder.ordered()
        expected = ["environment-A"]
        self.assertEqual(expected, environments)

        expected = ["/etc/kayobe/environments/environment-A"]
        paths = finder.ordered_paths()
        self.assertEqual(expected, paths)

    @mock.patch.object(utils.EnvironmentFinder, "_read_metadata")
    def test_environment_finder_with_dependency_chain(self, mock_yaml):
        def yaml_replacement(path):
            if path == ("/etc/kayobe/environments/environment-C/"
                        ".kayobe-environment"):
                return {"dependencies": ["environment-A", "environment-B"]}
            if path == ("/etc/kayobe/environments/environment-B/"
                        ".kayobe-environment"):
                return {"dependencies": ["environment-A"]}
            return {}
        mock_yaml.side_effect = yaml_replacement
        finder = utils.EnvironmentFinder('/etc/kayobe', 'environment-C')
        result = finder.ordered()
        expected = ["environment-A", "environment-B", "environment-C"]
        self.assertEqual(expected, result)

        expected = ["/etc/kayobe/environments/environment-A",
                    "/etc/kayobe/environments/environment-B",
                    "/etc/kayobe/environments/environment-C"]
        paths = finder.ordered_paths()
        self.assertEqual(expected, paths)

    @mock.patch.object(utils.EnvironmentFinder, "_read_metadata")
    def test_environment_finder_with_cycle(self, mock_yaml):
        # The cycle is: C - B - C
        def yaml_replacement(path):
            if path == ("/etc/kayobe/environments/environment-C/"
                        ".kayobe-environment"):
                return {"dependencies": ["environment-A", "environment-B"]}
            if path == ("/etc/kayobe/environments/environment-B/"
                        ".kayobe-environment"):
                return {"dependencies": ["environment-A", "environment-C"]}
            return {}
        mock_yaml.side_effect = yaml_replacement
        finder = utils.EnvironmentFinder('/etc/kayobe', 'environment-C')
        self.assertRaises(exception.Error, finder.ordered)
        self.assertRaises(exception.Error, finder.ordered_paths)

    def test_environment_finder_no_environment(self):
        finder = utils.EnvironmentFinder('/etc/kayobe', None)
        self.assertEqual([], finder.ordered())
        self.assertEqual([], finder.ordered_paths())
