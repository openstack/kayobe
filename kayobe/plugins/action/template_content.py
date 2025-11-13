# Copyright (c) 2025 StackHPC Ltd.
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
import tempfile

from ansible.module_utils.common.text.converters import to_bytes
from ansible.plugins.action.template import ActionModule as TemplateBase

from ansible import errors as ansible_errors


class ActionModule(TemplateBase):
    """Decorates template action to support using content parameter"""

    def run(self, *args, **kwargs):
        module_args = self._task.args
        if "src" in module_args and "content" in module_args:
            raise ansible_errors.AnsibleActionFail(
                "Invalid argument: content and src are mutually exclusive."
            )
        if "content" not in module_args and "src" not in module_args:
            raise ansible_errors.AnsibleActionFail(
                "Invalid argument: You must speicfy either content or src"
            )

        if "src" in module_args:
            return super().run(*args, **kwargs)

        with tempfile.NamedTemporaryFile() as fp:
            content = module_args.pop("content", "")
            fp.write(to_bytes(content))
            fp.flush()
            tempfile_path = os.path.join(tempfile.gettempdir(), str(fp.name))
            module_args["src"] = tempfile_path
            return super().run(*args, **kwargs)
