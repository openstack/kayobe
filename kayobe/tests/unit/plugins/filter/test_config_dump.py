# Copyright (c) 2026 StackHPC Ltd.
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

import unittest
from unittest import mock

import jinja2

from ansible._internal._datatag._tags import TrustedAsTemplate
from ansible import errors
from ansible.module_utils._internal._datatag._tags import Deprecated
from ansible.module_utils._internal._datatag import AnsibleTagHelper
from ansible.parsing.dataloader import DataLoader
from kayobe.plugins.filter import config_dump


class FakeHostVarsVars(object):
    """A minimal stand-in for Ansible's HostVarsVars."""

    def __init__(self, variables):
        self._vars = variables


def _trust(value):
    """Mark a variable as a trusted template, as the inventory does."""
    if isinstance(value, str):
        return AnsibleTagHelper.tag(value, TrustedAsTemplate())
    return value


def _deprecate(value):
    """Mark a value as deprecated, as top-level facts are."""
    return Deprecated(msg='deprecated', version='2.24').tag(value)


class TestConfigDump(unittest.TestCase):

    maxDiff = None

    def setUp(self):
        # Bandit complains about Jinja2 autoescaping without nosec.
        self.env = jinja2.Environment()  # nosec
        self.hostvars_vars = DataLoader().load("""
inventory_hostname: host1
plain: hello
# A variable referencing hostvars, as Kayobe's network interface variables
# do.
self_ref: >-
  {{ 'a' if 'ansible_dummy1' in
     hostvars[inventory_hostname] else [] }}
# A variable referencing an undefined variable.
undefined_nested: "{{ ansible_facts.architecture }}"
# A variable resolving to the omit sentinel.
omit_var: "{{ omit }}"
a_dict:
  key: value
a_list:
  - a
  - b
""")
        for key in ("self_ref", "undefined_nested", "omit_var"):
            self.hostvars_vars[key] = _trust(self.hostvars_vars[key])
        # The templating context must provide the hostvars variable, but the
        # host's variables themselves do not include it.
        context_vars = dict(self.hostvars_vars)
        context_vars["hostvars"] = {"host1": self.hostvars_vars}
        self.context = self._make_context(context_vars)
        self.hostvars = FakeHostVarsVars(self.hostvars_vars)

    def _make_context(self, parent):
        return self.env.context_class(
            self.env, parent=parent, name='dummy', blocks={})

    def test_kayobe_config_dump(self):
        result = config_dump.kayobe_config_dump(self.context, self.hostvars)
        self.assertEqual("hello", result["plain"])
        # Variables referencing hostvars are resolved.
        self.assertEqual([], result["self_ref"])
        # Variables referencing undefined variables are preserved.
        self.assertEqual("{{ ansible_facts.architecture }}",
                         result["undefined_nested"])
        # Omitted variables are preserved.
        self.assertEqual("{{ omit }}", result["omit_var"])
        self.assertEqual({"key": "value"}, result["a_dict"])
        self.assertEqual(["a", "b"], result["a_list"])

    def test_kayobe_config_dump_var_name(self):
        result = config_dump.kayobe_config_dump(
            self.context, self.hostvars, "self_ref")
        self.assertEqual([], result)

    def test_kayobe_config_dump_var_name_missing(self):
        self.assertRaises(
            errors.AnsibleFilterError,
            config_dump.kayobe_config_dump,
            self.context, self.hostvars, "does_not_exist")

    def test_kayobe_config_dump_plain_dict(self):
        variables = {"plain": "hello"}
        result = config_dump.kayobe_config_dump(self.context, variables)
        self.assertEqual("hello", result["plain"])

    def test_kayobe_config_dump_top_level_facts(self):
        variables = {
            "inventory_hostname": "host1",
            # A top-level fact, as injected when inject_facts_as_vars is
            # enabled. It is deprecated, but is still templated, for example
            # because a user may have overridden it.
            "ansible_hostname": _trust(
                _deprecate("{{ 'resolved-host1' }}")),
        }
        context_vars = dict(variables)
        context_vars["hostvars"] = {"host1": variables}
        context = self._make_context(context_vars)
        hostvars = FakeHostVarsVars(variables)

        result = config_dump.kayobe_config_dump(context, hostvars)

        self.assertEqual("resolved-host1", result["ansible_hostname"])

    @mock.patch.object(config_dump.display, 'warning')
    def test_kayobe_config_dump_deprecated_fact_unresolved(self, mock_warning):
        variables = {
            "inventory_hostname": "host1",
            # A deprecated top-level fact that cannot be templated.
            "ansible_hostname": _trust(_deprecate("{{ omit }}")),
        }
        context_vars = dict(variables)
        context_vars["hostvars"] = {"host1": variables}
        context = self._make_context(context_vars)
        hostvars = FakeHostVarsVars(variables)

        result = config_dump.kayobe_config_dump(context, hostvars)

        self.assertTrue(mock_warning.called)
        self.assertEqual("{{ omit }}", result["ansible_hostname"])
