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

import importlib.util
from pathlib import Path
import unittest
from unittest import mock


MODULE_PATH = (
    Path(__file__).resolve().parents[3] /
    "ansible/roles/network-nmstate/library/nmstate_apply.py"
)


class ModuleFailed(Exception):
    def __init__(self, payload):
        super().__init__(payload.get("msg", "module failed"))
        self.payload = payload


class ModuleExited(Exception):
    def __init__(self, payload):
        super().__init__("module exited")
        self.payload = payload


class FakeModule:
    def __init__(self, params):
        self.params = params

    def fail_json(self, **kwargs):
        raise ModuleFailed(kwargs)

    def exit_json(self, **kwargs):
        raise ModuleExited(kwargs)


class TestNMStateApply(unittest.TestCase):

    def _load_module(self):
        spec = importlib.util.spec_from_file_location(
            "kayobe_nmstate_apply_module",
            MODULE_PATH,
        )
        if spec is None or spec.loader is None:
            raise RuntimeError("Failed to load nmstate_apply module spec")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_import_failure(self):
        module = self._load_module()
        fake_module = FakeModule({"state": {}, "debug": False})

        with mock.patch.object(
            module, "AnsibleModule", return_value=fake_module
        ):
            with mock.patch.object(
                module.importlib,
                "import_module",
                side_effect=ImportError("No module named libnmstate"),
            ):
                with self.assertRaises(ModuleFailed) as context:
                    module.run_module()

        message = context.exception.payload["msg"]
        self.assertIn("Failed to import libnmstate module", message)
        self.assertIn("python3-libnmstate", message)

    def test_apply_failure(self):
        module = self._load_module()
        fake_module = FakeModule({"state": {"interfaces": []}, "debug": False})

        fake_libnmstate = mock.Mock()
        fake_libnmstate.show.return_value = {"interfaces": []}
        fake_libnmstate.apply.side_effect = RuntimeError("apply failed")

        with mock.patch.object(
            module, "AnsibleModule", return_value=fake_module
        ):
            with mock.patch.object(
                module.importlib,
                "import_module",
                return_value=fake_libnmstate,
            ):
                with self.assertRaises(ModuleFailed) as context:
                    module.run_module()

        self.assertIn(
            "Failed to apply nmstate state",
            context.exception.payload["msg"],
        )

    def test_apply_success_debug_output(self):
        module = self._load_module()
        desired_state = {"interfaces": [{"name": "eth0", "state": "up"}]}
        fake_module = FakeModule({"state": desired_state, "debug": True})

        previous_state = {"interfaces": [{"name": "eth0", "state": "down"}]}
        current_state = {"interfaces": [{"name": "eth0", "state": "up"}]}

        fake_libnmstate = mock.Mock()
        fake_libnmstate.show.side_effect = [previous_state, current_state]

        with mock.patch.object(
            module, "AnsibleModule", return_value=fake_module
        ):
            with mock.patch.object(
                module.importlib,
                "import_module",
                return_value=fake_libnmstate,
            ):
                with self.assertRaises(ModuleExited) as context:
                    module.run_module()

        payload = context.exception.payload
        self.assertTrue(payload["changed"])
        self.assertEqual(payload["state"], current_state)
        self.assertEqual(payload["previous_state"], previous_state)
        self.assertEqual(payload["desired_state"], desired_state)
        fake_libnmstate.apply.assert_called_once_with(desired_state)
