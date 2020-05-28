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


def switch_interface_config_select_name(switch_interface_config, names):
    """Select and return all switch interfaces matching requested names.

    :param switch_interface_config: Switch interface configuration dict
    :param names: String or list of strings - interface names to match
    """
    if isinstance(names, str):
        names = [names]

    return {
        name: config
        for name, config in switch_interface_config.items()
        if name in names
    }


def switch_interface_config_select_description(switch_interface_config, descriptions):
    """Select and return all switch interfaces matching requested descriptions.

    :param switch_interface_config: Switch interface configuration dict
    :param descriptions: String or list of strings - descriptions to match
    """
    if isinstance(descriptions, str):
        descriptions = [descriptions]

    return {
        name: config
        for name, config in switch_interface_config.items()
        if (config.get('description') in descriptions and
            config.get('ngs_trunk_port', True))
    }


def switch_interface_config_select_trunk(switch_interface_config):
    """Select and return all switch interfaces which are trunk links.

    Interfaces are assumed to be trunked, unless they have a ngs_trunk_port
    item which is set to False.

    :param switch_interface_config: Switch interface configuration dict
    """
    return {
        name: config
        for name, config in switch_interface_config.items()
        if config.get('ngs_trunk_port', True)
    }


class FilterModule(object):
    """Switch filters."""

    def filters(self):
        return {
            'switch_interface_config_select_name': switch_interface_config_select_name,
            'switch_interface_config_select_description': switch_interface_config_select_description,
            'switch_interface_config_select_trunk': switch_interface_config_select_trunk,
        }
