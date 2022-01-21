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

from ansible import errors


def _get_namespace(context, inventory_hostname=None):
    if inventory_hostname is None:
        return context
    if inventory_hostname not in context['hostvars']:
        raise errors.AnsibleFilterError(
            "Inventory hostname '%s' not in hostvars" % inventory_hostname)
    return context["hostvars"][inventory_hostname]


def get_hostvar(context, var_name, inventory_hostname=None):
    return _get_namespace(context, inventory_hostname).get(var_name)


def hostvar_defined(context, var_name, inventory_hostname=None):
    return var_name in _get_namespace(context, inventory_hostname)


def call_bool_filter(context, value):
    """Pass a value through the 'bool' filter.

    :param context: Jinja2 Context object.
    :param value: Value to pass through bool filter.
    :returns: A boolean.
    """
    return context.environment.call_filter("bool", value, context=context)
