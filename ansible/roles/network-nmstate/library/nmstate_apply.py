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

from ansible.module_utils.basic import AnsibleModule

DOCUMENTATION = """
---
module: nmstate_apply
version_added: "19.1"
author: "StackHPC"
short_description: Apply network state using nmstate
description:
    - "This module allows applying a network state using nmstate library.
       Provides idempotency by comparing desired and current states."
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
    - libnmstate
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
    returned: always
previous_state:
    description: Network state before applying (when debug=true)
    type: dict
    returned: when debug=True
desired_state:
    description: Desired network state that was applied (when debug=true)
    type: dict
    returned: when debug=True
"""


def run_module():
    argument_spec = dict(
        state=dict(required=True, type="dict"),
        debug=dict(default=False, type="bool"),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=False,
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

    previous_state = libnmstate.show()
    desired_state = module.params["state"]
    debug = module.params["debug"]

    result = {"changed": False}

    try:
        libnmstate.apply(desired_state)
    except Exception as e:
        module.fail_json(msg="Failed to apply nmstate state: %s" % repr(e))

    current_state = libnmstate.show()

    if current_state != previous_state:
        result["changed"] = True
        if debug:
            result["previous_state"] = previous_state
            result["desired_state"] = desired_state

    result["state"] = current_state

    module.exit_json(**result)


def main():
    run_module()


if __name__ == "__main__":
    main()
