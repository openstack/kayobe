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

import copy

from ansible.module_utils.basic import *
from ansible_collections.openstack.cloud.plugins.module_utils.openstack import *

# Store a list of import errors to report to the user.
IMPORT_ERRORS = []
try:
    import openstack
except Exception as e:
    IMPORT_ERRORS.append(e)


DOCUMENTATION = """
module: os_ironic_inspector_rule
short_description: Create or destroy an Ironic Inspector rule.
author: "Mark Goddard <mark@stackhpc.com>"
extends_documentation_fragment: openstack
description:
  - Create or destroy an Ironic inspector rule.
options:
  state:
    description:
      - State of the rule
    choices: ["present", "absent"]
  uuid:
    description:
      - Globally unique identifier for the rule.
    required: false
  description:
    description:
      - Description for the rule.
    required: false
  conditions:
    description:
      - List of conditions that must be met in order to apply the rule.
    required: true
  actions:
    description:
      - List of actions to be taken when the conditions are met.
    required: true
  sensitive:
    description:
      - Whether to mark the rule as sensitive in Ironic
    required: false
"""

EXAMPLES = """
# Ensure that an inspector rule exists.
os_ironic_inspector_rule:
  cloud: "openstack"
  state: present
  uuid: "d44666e1-35b3-4f6b-acb0-88ab7052da69"
  description: Set IPMI username in driver_info if not set
  conditions:
    - field: "node://driver_info.ipmi_username"
      op: "is-empty"
  actions:
    - action: "set-attribute"
      path: "driver_info/ipmi_username"
      value: "root"
"""


def _get_client(module, cloud):
    """Return an Ironic inspector client."""
    return cloud.baremetal


def _ensure_rule_present(module, client):
    """Ensure that an inspector rule is present."""
    if module.params['uuid']:
        response = client.get('/inspection_rules/{}'.format(module.params['uuid']), headers={'X-OpenStack-Ironic-API-Version': '1.96'})
        if not response.ok:
            if response.status_code != 404:
                module.fail_json(msg="Failed retrieving Inspector rule %s: %s"
                                 % (module.params['uuid'], repr(e)))
        else:
            rule = response.json()
            # Check whether the rule differs from the request.
            keys = ('conditions', 'actions', 'description', 'sensitive')
            for key in keys:
                expected = module.params[key]
                if key == 'conditions':
                    # Rules returned from the API include default values in the
                    # conditions that may not be in the requested rule. Apply
                    # defaults to allow the comparison to succeed.
                    expected = copy.deepcopy(expected)
                if key == 'actions':
                    expected = copy.deepcopy(expected)
                    for condition in expected:
                        condition.setdefault('loop', [])
                if rule[key] != expected:
                    break
            else:
                # Nothing to do - rule exists and is as requested.
                return False
            # Rule differs - delete it before recreating.
            _ensure_rule_absent(module, client)

    rule = {
        "conditions": module.params['conditions'],
        "actions": module.params['actions'],
        "description": module.params['description'],
        "sensitive": module.params['sensitive'],
        "uuid": module.params['uuid'],
    }
    response = client.post("/inspection_rules", json=rule, headers={'X-OpenStack-Ironic-API-Version': '1.96'})
    if not response.ok:
        module.fail_json(msg="Failed creating Inspector rule %s: %s"
                         % (module.params['uuid'], response.text))
    return True


def _ensure_rule_absent(module, client):
    """Ensure that an inspector rule is absent."""
    if not module.params['uuid']:
        module.fail_json(msg="UUID is required to ensure rules are absent")
    response = client.delete("/inspection_rules/{}".format(module.params['uuid']), headers={'X-OpenStack-Ironic-API-Version': '1.96'})
    if not response.ok:
        # If the rule does not exist, no problem and no change.
        if response.status_code == 404:
            return False
        module.fail_json(msg="Failed retrieving Inspector rule %s: %s"
                         % (module.params['uuid'], response.text))
    return True


def main():
    argument_spec = openstack_full_argument_spec(
        conditions=dict(type='list', required=True),
        actions=dict(type='list', required=True),
        description=dict(required=False),
        uuid=dict(required=False),
        sensitive=dict(type='bool', required=False, default=False),
        state=dict(required=False, default='present',
                   choices=['present', 'absent']),
    )
    module_kwargs = openstack_module_kwargs()
    module = AnsibleModule(argument_spec, **module_kwargs)

    # Fail if there were any exceptions when importing modules.
    if IMPORT_ERRORS:
        module.fail_json(msg="Import errors: %s" %
                         ", ".join([repr(e) for e in IMPORT_ERRORS]))

    sdk, cloud = openstack_cloud_from_module(module)
    try:
        client = _get_client(module, cloud)
        if module.params["state"] == "present":
            changed = _ensure_rule_present(module, client)
        else:
            changed = _ensure_rule_absent(module, client)
    except Exception as e:
        module.fail_json(msg="Failed to configure Ironic Inspector rule: %s" %
                         repr(e))
    else:
        module.exit_json(changed=changed)


if __name__ == '__main__':
    main()
