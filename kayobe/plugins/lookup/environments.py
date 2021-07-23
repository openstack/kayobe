# Copyright (c) 2023 StackHPC Ltd.
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

from ansible.errors import AnsibleError
from ansible.plugins.loader import lookup_loader
from ansible.plugins.lookup import LookupBase

from kayobe.utils import EnvironmentFinder

__version__ = "1.0.0"

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display

    display = Display()


class LookupModule(LookupBase):
    def run(self, terms, variables=None, **kwargs):
        lookup = lookup_loader.get(
            'vars', loader=self._loader, templar=self._templar
        )
        # Values in variables are untemplated, e.g:
        # {{ lookup('env', 'KAYOBE_CONFIG_PATH') | default('/etc/kayobe', true) }}  # noqa
        environment = lookup.run(
            ["kayobe_environment"],
            variables=variables, default='')[0]
        kayobe_config_path = lookup.run(
            ["kayobe_config_path"],
            variables=variables, default='')[0]
        if not environment:
            return []
        if not kayobe_config_path:
            raise AnsibleError("kayobe_config_path is unset")
        environment_finder = EnvironmentFinder(kayobe_config_path, environment)
        return environment_finder.ordered_paths()
