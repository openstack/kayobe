import argparse
import subprocess
import unittest

import mock

from kayobe import kolla_ansible
from kayobe import utils


class TestCase(unittest.TestCase):

    @mock.patch.object(utils, "run_command")
    @mock.patch.object(kolla_ansible, "_validate_args")
    def test_run(self, mock_validate, mock_run):
        parser = argparse.ArgumentParser()
        kolla_ansible.add_args(parser)
        parsed_args = parser.parse_args([])
        kolla_ansible.run(parsed_args, "command", "overcloud")
        expected_cmd = [
            "source", "ansible/kolla-venv/bin/activate", "&&",
            "kolla-ansible", "command",
            "--inventory", "/etc/kolla/inventory/overcloud",
        ]
        expected_cmd = " ".join(expected_cmd)
        mock_run.assert_called_once_with(expected_cmd, shell=True, quiet=False)

    @mock.patch.object(utils, "run_command")
    @mock.patch.object(kolla_ansible, "_validate_args")
    def test_run_all_the_args(self, mock_validate, mock_run):
        parser = argparse.ArgumentParser()
        kolla_ansible.add_args(parser)
        args = [
            "--kolla-config-path", "/path/to/config",
            "-ke", "ev_name1=ev_value1",
            "-ki", "/path/to/inventory",
            "-kt", "tag1,tag2",
        ]
        parsed_args = parser.parse_args(args)
        kolla_ansible.run(parsed_args, "command", "overcloud")
        expected_cmd = [
            "source", "ansible/kolla-venv/bin/activate", "&&",
            "kolla-ansible", "command",
            "--inventory", "/path/to/inventory",
            "--configdir", "/path/to/config",
            "--passwords", "/path/to/config/passwords.yml",
            "-e", "ev_name1=ev_value1",
            "--tags", "tag1,tag2",
        ]
        expected_cmd = " ".join(expected_cmd)
        mock_run.assert_called_once_with(expected_cmd, shell=True, quiet=False)

    @mock.patch.object(utils, "run_command")
    @mock.patch.object(kolla_ansible, "_validate_args")
    def test_run_all_the_long_args(self, mock_validate, mock_run):
        parser = argparse.ArgumentParser()
        kolla_ansible.add_args(parser)
        args = [
            "--kolla-config-path", "/path/to/config",
            "--kolla-extra-vars", "ev_name1=ev_value1",
            "--kolla-inventory", "/path/to/inventory",
            "--kolla-tags", "tag1,tag2",
        ]
        parsed_args = parser.parse_args(args)
        kolla_ansible.run(parsed_args, "command", "overcloud")
        expected_cmd = [
            "source", "ansible/kolla-venv/bin/activate", "&&",
            "kolla-ansible", "command",
            "--inventory", "/path/to/inventory",
            "--configdir", "/path/to/config",
            "--passwords", "/path/to/config/passwords.yml",
            "-e", "ev_name1=ev_value1",
            "--tags", "tag1,tag2",
        ]
        expected_cmd = " ".join(expected_cmd)
        mock_run.assert_called_once_with(expected_cmd, shell=True, quiet=False)

    @mock.patch.object(utils, "run_command")
    @mock.patch.object(kolla_ansible, "_validate_args")
    def test_run_func_args(self, mock_validate, mock_run):
        parser = argparse.ArgumentParser()
        kolla_ansible.add_args(parser)
        args = [
            "--kolla-extra-vars", "ev_name1=ev_value1",
            "--kolla-tags", "tag1,tag2",
        ]
        parsed_args = parser.parse_args(args)
        kwargs = {
            "extra_vars": {"ev_name2": "ev_value2"},
            "tags": "tag3,tag4",
        }
        kolla_ansible.run(parsed_args, "command", "overcloud", **kwargs)
        expected_cmd = [
            "source", "ansible/kolla-venv/bin/activate", "&&",
            "kolla-ansible", "command",
            "--inventory", "/etc/kolla/inventory/overcloud",
            "-e", "ev_name1=ev_value1",
            "-e", "ev_name2=ev_value2",
            "--tags", "tag1,tag2,tag3,tag4",
        ]
        expected_cmd = " ".join(expected_cmd)
        mock_run.assert_called_once_with(expected_cmd, shell=True, quiet=False)

    @mock.patch.object(utils, "run_command")
    @mock.patch.object(kolla_ansible, "_validate_args")
    def test_run_failure(self, mock_validate, mock_run):
        parser = argparse.ArgumentParser()
        kolla_ansible.add_args(parser)
        parsed_args = parser.parse_args([])
        mock_run.side_effect = subprocess.CalledProcessError(1, "dummy")
        self.assertRaises(SystemExit,
                          kolla_ansible.run, parsed_args, "command",
                          "overcloud")
