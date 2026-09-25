#!/usr/bin/python
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

import importlib
import json

from ansible.module_utils.basic import AnsibleModule

DOCUMENTATION = """
---
module: nmstate_apply
version_added: "19.1"
author: "StackHPC"
short_description: Apply network state using nmstate
description:
    - "This module allows applying a network state using nmstate library.
       Provides idempotency by comparing desired and current states.
       Supports check and diff modes."
options:
  state:
    description:
      - Network state definition in nmstate format
    required: True
    type: dict
  debug:
    description:
      - Include previous and desired states in output for debugging
    required: False
    default: False
    type: bool
requirements:
    - libnmstate (nmstate 2.x)
"""

EXAMPLES = """
- name: Apply network state
  nmstate_apply:
    state:
      interfaces:
        - name: eth0
          type: ethernet
          state: up
          ipv4:
            address:
              - ip: 192.168.1.10
                prefix-length: 24
            dhcp: false
  debug: false
"""

RETURN = """
changed:
    description: Whether the network state was modified
    type: bool
    returned: always
state:
    description: Current network state after applying desired state
    type: dict
    returned: when not in check mode
differences:
    description: Computed differences between the current and desired states
    type: dict
    returned: when changed
diff:
    description: Prepared diff of the computed differences
    type: dict
    returned: when changed
previous_state:
    description: Network state before applying (when debug=true)
    type: dict
    returned: when debug=True
desired_state:
    description: Desired network state that was applied (when debug=true)
    type: dict
    returned: when debug=True
"""


def _is_empty(value):
    if isinstance(value, dict):
        return all(_is_empty(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return all(_is_empty(item) for item in value)
    return value is None


def run_module():
    argument_spec = dict(
        state=dict(required=True, type="dict"),
        debug=dict(default=False, type="bool"),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    try:
        libnmstate = importlib.import_module("libnmstate")
    except Exception as e:
        module.fail_json(
            msg=(
                "Failed to import libnmstate module. "
                "Ensure nmstate Python dependencies are installed "
                "(for example python3-libnmstate). "
                "Import errors: %s"
            ) % repr(e)
        )

    if not hasattr(libnmstate, "generate_differences"):
        module.fail_json(
            msg=(
                "The installed libnmstate does not provide "
                "generate_differences(). The nmstate_apply module requires "
                "nmstate 2.x (for example python3-libnmstate 2.x)."
            )
        )

    current_state = libnmstate.show()
    desired_state = module.params["state"]
    debug = module.params["debug"]

    differences = libnmstate.generate_differences(
        desired_state, current_state)
    changed = not _is_empty(differences)

    result = {"changed": changed}
    if changed:
        # "prepared" is a special Ansible diff key whose content is
        # printed as-is, keeping --diff output to the changed properties.
        if module._diff:
            result["diff"] = {
                "prepared": json.dumps(
                    differences, indent=1, sort_keys=True),
            }
        result["differences"] = differences

    if debug:
        result["previous_state"] = current_state
        result["desired_state"] = desired_state

    if module.check_mode:
        module.exit_json(**result)
        return

    # generate_differences() compares against the runtime state, not
    # the config persisted by NetworkManager, so apply unconditionally
    # to re-persist the config and prevent drift after a reboot.
    try:
        libnmstate.apply(desired_state)
    except Exception as e:
        # A failed apply must not claim changed: nmstate verifies the
        # applied state and rolls back on failure.
        module.fail_json(msg="Failed to apply nmstate state: %s" % repr(e),
                         differences=differences)

    result["state"] = libnmstate.show()

    module.exit_json(**result)


def main():
    run_module()


if __name__ == "__main__":
    main()
