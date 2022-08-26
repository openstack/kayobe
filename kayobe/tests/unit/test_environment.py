# Copyright (c) 2021 StackHPC Ltd.
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

from kayobe import ansible
from kayobe import environment
from kayobe import utils


class TestCase(unittest.TestCase):

    maxDiff = None

    @mock.patch.object(utils, "is_readable_dir")
    def test_unreadable_environments_directory(self, mock_readable_dir):
        mock_readable_dir.return_value = {
            "result": False,
            "message": "Directory is not readable"
        }
        parser = argparse.ArgumentParser()
        args = [
            "--config-path", "/path/to/config",
            "--environment", "foo",
        ]
        ansible.add_args(parser)
        environment.add_args(parser)
        parsed_args = parser.parse_args(args)
        self.assertRaises(SystemExit,
                          environment.create_kayobe_environment, parsed_args)

    @mock.patch.object(utils, "is_readable_dir")
    def test_environment_exists(self, mock_readable_dir):
        mock_readable_dir.side_effect = [{"result": True}, {"result": True}]
        parser = argparse.ArgumentParser()
        args = [
            "--config-path", "/path/to/config",
            "--environment", "foo",
        ]
        ansible.add_args(parser)
        environment.add_args(parser)
        parsed_args = parser.parse_args(args)
        self.assertRaises(SystemExit,
                          environment.create_kayobe_environment, parsed_args)

    @mock.patch.object(utils, "copy_dir")
    @mock.patch.object(os, "mkdir")
    @mock.patch.object(utils, "is_readable_dir")
    def test_create_kayobe_environment(self, mock_readable_dir, mock_mkdir,
                                       mock_copy_dir):
        mock_readable_dir.return_value = {
            "result": False,
            "message": "Path does not exist"
        }
        parser = argparse.ArgumentParser()
        args = [
            "--config-path", "/path/to/config",
            "--source-config-path", "/path/to/foo",
            "--environment", "foo",
        ]
        ansible.add_args(parser)
        environment.add_args(parser)
        parsed_args = parser.parse_args(args)
        environment.create_kayobe_environment(parsed_args)
        expected_calls = [
            mock.call("/path/to/config/environments"),
            mock.call("/path/to/config/environments/foo"),
        ]
        self.assertListEqual(expected_calls, mock_mkdir.call_args_list)
        mock_copy_dir.assert_called_once_with(
            "/path/to/foo", "/path/to/config/environments/foo",
            exclude=["environments"])
