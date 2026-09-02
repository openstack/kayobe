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
import json
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
    def __init__(self, params, check_mode=False, diff_mode=True):
        self.params = params
        self.check_mode = check_mode
        self._diff = diff_mode

    def fail_json(self, **kwargs):
        raise ModuleFailed(kwargs)

    def exit_json(self, **kwargs):
        raise ModuleExited(kwargs)


def make_fake_libnmstate(differences=None, states=None):
    fake_libnmstate = mock.Mock()
    if differences is not None:
        fake_libnmstate.generate_differences.return_value = differences
    if states is not None:
        fake_libnmstate.show.side_effect = states
    return fake_libnmstate


class TestNMStateApply(unittest.TestCase):

    maxDiff = None

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

    def _run_module(self, module, fake_module, fake_libnmstate):
        with mock.patch.object(
            module, "AnsibleModule", return_value=fake_module
        ):
            with mock.patch.object(
                module.importlib,
                "import_module",
                return_value=fake_libnmstate,
            ):
                module.run_module()

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

    def test_missing_differences_api(self):
        module = self._load_module()
        fake_module = FakeModule({"state": {}, "debug": False})

        # Simulate a libnmstate without generate_differences (for
        # example nmstate 1.x).
        fake_libnmstate = mock.Mock(spec=["show"])

        with self.assertRaises(ModuleFailed) as context:
            self._run_module(module, fake_module, fake_libnmstate)

        message = context.exception.payload["msg"]
        self.assertIn("generate_differences", message)
        self.assertIn("nmstate 2.x", message)
        fake_libnmstate.show.assert_not_called()

    def test_apply_failure(self):
        module = self._load_module()
        desired_state = {"interfaces": [{"name": "eth0", "state": "up"}]}
        fake_module = FakeModule({"state": desired_state, "debug": False})

        current_state = {"interfaces": [{"name": "eth0", "state": "down"}]}
        differences = {"interfaces": [{"name": "eth0", "state": "up"}]}
        fake_libnmstate = make_fake_libnmstate(
            differences=differences,
            states=[current_state],
        )
        fake_libnmstate.apply.side_effect = RuntimeError("apply failed")

        with self.assertRaises(ModuleFailed) as context:
            self._run_module(module, fake_module, fake_libnmstate)

        payload = context.exception.payload
        self.assertIn("Failed to apply nmstate state", payload["msg"])
        # A failed apply must not claim changed (nmstate rolls back).
        self.assertEqual(payload["differences"], differences)
        self.assertNotIn("diff", payload)
        self.assertNotIn("changed", payload)

    def test_changed_without_diff_mode(self):
        module = self._load_module()
        desired_state = {"interfaces": [{"name": "eth0", "state": "up"}]}
        fake_module = FakeModule(
            {"state": desired_state, "debug": False},
            check_mode=True, diff_mode=False)

        current_state = {"interfaces": [{"name": "eth0", "state": "down"}]}
        differences = {"interfaces": [{"name": "eth0", "state": "up"}]}
        fake_libnmstate = make_fake_libnmstate(
            differences=differences,
            states=[current_state],
        )

        with self.assertRaises(ModuleExited) as context:
            self._run_module(module, fake_module, fake_libnmstate)

        payload = context.exception.payload
        self.assertTrue(payload["changed"])
        self.assertEqual(payload["differences"], differences)
        self.assertNotIn("diff", payload)
        fake_libnmstate.apply.assert_not_called()

    def test_apply_no_changes(self):
        module = self._load_module()
        desired_state = {"interfaces": [{"name": "eth0", "state": "up"}]}
        fake_module = FakeModule({"state": desired_state, "debug": False})

        current_state = {"interfaces": [{"name": "eth0", "state": "up"}]}
        # Real shape returned by the library when nothing differs.
        fake_libnmstate = make_fake_libnmstate(
            differences={"interfaces": []},
            states=[current_state, current_state],
        )

        with self.assertRaises(ModuleExited) as context:
            self._run_module(module, fake_module, fake_libnmstate)

        payload = context.exception.payload
        self.assertFalse(payload["changed"])
        self.assertNotIn("diff", payload)
        self.assertNotIn("differences", payload)
        self.assertEqual(payload["state"], current_state)
        # Apply is intentional even without changes (re-persists config).
        fake_libnmstate.apply.assert_called_once_with(desired_state)

    def test_apply_changed_with_diff_and_debug(self):
        module = self._load_module()
        desired_state = {"interfaces": [{"name": "eth0", "state": "up"}]}
        fake_module = FakeModule({"state": desired_state, "debug": True})

        previous_state = {"interfaces": [{"name": "eth0", "state": "down"}]}
        current_state = {"interfaces": [{"name": "eth0", "state": "up"}]}
        differences = {"interfaces": [{"name": "eth0", "state": "up"}]}

        fake_libnmstate = make_fake_libnmstate(
            differences=differences,
            states=[previous_state, current_state],
        )

        with self.assertRaises(ModuleExited) as context:
            self._run_module(module, fake_module, fake_libnmstate)

        payload = context.exception.payload
        self.assertTrue(payload["changed"])
        self.assertEqual(payload["state"], current_state)
        self.assertEqual(payload["previous_state"], previous_state)
        self.assertEqual(payload["desired_state"], desired_state)
        self.assertEqual(payload["differences"], differences)
        self.assertEqual(
            payload["diff"],
            {
                "prepared": json.dumps(
                    differences, indent=1, sort_keys=True),
            },
        )
        fake_libnmstate.apply.assert_called_once_with(desired_state)

    def test_check_mode_with_changes(self):
        module = self._load_module()
        desired_state = {"interfaces": [{"name": "eth0", "state": "up"}]}
        fake_module = FakeModule(
            {"state": desired_state, "debug": True}, check_mode=True)

        current_state = {"interfaces": [{"name": "eth0", "state": "down"}]}
        differences = {"interfaces": [{"name": "eth0", "state": "up"}]}
        fake_libnmstate = make_fake_libnmstate(
            differences=differences,
            states=[current_state],
        )

        with self.assertRaises(ModuleExited) as context:
            self._run_module(module, fake_module, fake_libnmstate)

        payload = context.exception.payload
        self.assertTrue(payload["changed"])
        self.assertEqual(payload["differences"], differences)
        self.assertEqual(
            payload["diff"],
            {
                "prepared": json.dumps(
                    differences, indent=1, sort_keys=True),
            },
        )
        # Debug output is available in check mode as well.
        self.assertEqual(payload["previous_state"], current_state)
        self.assertEqual(payload["desired_state"], desired_state)
        self.assertNotIn("state", payload)
        fake_libnmstate.apply.assert_not_called()

    def test_check_mode_no_changes(self):
        module = self._load_module()
        desired_state = {"interfaces": [{"name": "eth0", "state": "up"}]}
        fake_module = FakeModule(
            {"state": desired_state, "debug": False}, check_mode=True)

        current_state = {"interfaces": [{"name": "eth0", "state": "up"}]}
        fake_libnmstate = make_fake_libnmstate(
            differences={"interfaces": []},
            states=[current_state],
        )

        with self.assertRaises(ModuleExited) as context:
            self._run_module(module, fake_module, fake_libnmstate)

        payload = context.exception.payload
        self.assertFalse(payload["changed"])
        self.assertNotIn("diff", payload)
        self.assertNotIn("differences", payload)
        fake_libnmstate.apply.assert_not_called()

    def test_is_empty(self):
        module = self._load_module()

        # Empty or fully elided differences mean no changes.
        self.assertTrue(module._is_empty({}))
        self.assertTrue(module._is_empty({"interfaces": []}))
        self.assertTrue(module._is_empty({"routes": {"config": []}}))
        self.assertTrue(module._is_empty(
            {"dns-resolver": {"config": {}}}))
        self.assertTrue(module._is_empty(None))

        # Any populated structure or scalar means changes.
        self.assertFalse(module._is_empty(
            {"interfaces": [{"name": "eth0"}]}))
        self.assertFalse(module._is_empty(
            {"routes": {"config": [{"destination": "0.0.0.0/0"}]}}))
        self.assertFalse(module._is_empty({"hostname": "host01"}))
        self.assertFalse(module._is_empty(False))
        self.assertFalse(module._is_empty(0))
