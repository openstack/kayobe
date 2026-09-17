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

import jinja2

from ansible import errors
from ansible.parsing.dataloader import DataLoader
from ansible.template import Templar
from ansible.utils.display import Display

try:
    from ansible.module_utils._internal._datatag._tags import Deprecated
except ImportError:  # pragma: no cover
    # Older ansible-core versions do not tag top-level facts as deprecated.
    Deprecated = None

display = Display()


def _make_serializable(value):
    """Recursively convert values that cannot be serialized to YAML.

    :param value: value to convert.
    :returns: a value that can be serialized to YAML.
    """
    if isinstance(value, dict):
        return {k: _make_serializable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_make_serializable(v) for v in value]
    if value is None or isinstance(value, (str, bytes, int, float, bool)):
        return value
    return str(value)


def _resolve(templar, name, value):
    """Resolve a raw Ansible variable in the current templating context.

    Top-level facts are tagged as deprecated by Ansible. They are already
    resolved, but may have been overridden by a user-provided template, so
    attempt to resolve them. If that fails, emit a warning and preserve the
    raw value.

    :param templar: an Ansible Templar with the current context's variables.
    :param name: name of the variable being resolved.
    :param value: raw variable value to resolve.
    :returns: the resolved value, or the raw value as a string if it could not
              be resolved, for example because it references an undefined
              variable.
    """
    if Deprecated is not None and Deprecated.is_tagged_on(value):
        value = Deprecated.untag(value)
        try:
            return templar.template(value, fail_on_undefined=False)
        except Exception:
            display.warning(
                "Failed to resolve variable '%s'. It references a deprecated "
                "top-level fact; use ansible_facts instead." % name)
            return value
    try:
        return templar.template(value, fail_on_undefined=False)
    except Exception:
        # Preserve variables that cannot be resolved, such as those that
        # reference omitted values. Casting to a plain string ensures that the
        # value is not templated again by the caller.
        return "%s" % value


@jinja2.pass_context
def kayobe_config_dump(context, hostvars, var_name=None):
    """Return the resolved Ansible variables for a host.

    This is used by the ``kayobe configuration dump`` command. It is not
    possible to simply serialize the result of ``hostvars[host]`` because in
    ansible-core >= 2.19 ``HostVarsVars`` templates variables in a context that
    does not include the ``hostvars`` variable, and fails on undefined
    variables. Instead, use the raw variables and template them in the current
    context.

    :param context: a Jinja2 Context object.
    :param hostvars: Ansible host variables for a host, typically
                     ``hostvars[inventory_hostname]``.
    :param var_name: optional name of a single variable to return. If not
                     specified, a dict of all variables is returned.
    :returns: a dict mapping variable names to resolved values, or a single
              resolved value if ``var_name`` is specified.
    :raises: ansible.errors.AnsibleFilterError
    """
    templar = Templar(loader=DataLoader(), variables=context.get_all())
    # HostVarsVars exposes its raw variables via _vars. There is no public API
    # for accessing them without templating.
    variables = getattr(hostvars, '_vars', hostvars)

    if var_name is not None:
        if var_name not in variables:
            inventory_hostname = context.get('inventory_hostname')
            raise errors.AnsibleFilterError(
                "Variable '%s' not found for host '%s'" %
                (var_name, inventory_hostname))
        return _make_serializable(
            _resolve(templar, var_name, variables[var_name]))

    return {
        name: _make_serializable(_resolve(templar, name, value))
        for name, value in variables.items()
    }


def get_filters():
    return {
        'kayobe_config_dump': kayobe_config_dump,
    }
