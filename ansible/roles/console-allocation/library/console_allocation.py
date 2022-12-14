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

# TODO(wszumski): If we have multiple conductors and they are on different machines
# we could make a pool per machine.

DOCUMENTATION = """
module: console_allocation
short_description: Allocate a serial console TCP port for an Ironic node from a pool
author: Mark Goddard (mark@stackhpc.com) and Will Szumski (will@stackhpc.com)
options:
  - option-name: nodes
    description: List of Names or UUIDs corresponding to Ironic Nodes
    required: True
    type: list
  - option-name: allocation_pool_start
    description: First address of the pool from which to allocate
    required: True
    type: int
  - option-name: allocation_pool_end
    description: Last address of the pool from which to allocate
    required: True
    type: int
  - option-name: allocation_file
    description: >
      Path to a file in which to store the allocations. Will be created if it
      does not exist.
    required: True
    type: string
requirements:
  - PyYAML
"""

EXAMPLES = """
- name: Ensure Ironic node has a TCP port assigned for it's serial console
  console_allocation:
    nodes: ['node-1', 'node-2']
    allocation_pool_start: 30000
    allocation_pool_end: 31000
    allocation_file: /path/to/allocation/file.yml
"""

RETURN = """
ports:
  description: >
    A dictionary mapping the node name to the allocated serial console TCP port
  returned: success
  type: dict
  sample: { 'node1' : 30000, 'node2':300001 }
"""

from ansible.module_utils.basic import *
import sys

# Store a list of import errors to report to the user.
IMPORT_ERRORS=[]
try:
    import yaml
except Exception as e:
    IMPORT_ERRORS.append(e)


def read_allocations(module):
    """Read TCP port allocations from the allocation file."""
    filename = module.params['allocation_file']
    try:
        with open(filename, 'r') as f:
            content = yaml.safe_load(f)
    except IOError as e:
        if e.errno == errno.ENOENT:
            # Ignore ENOENT - we will create the file.
            return {}
        module.fail_json(msg="Failed to open allocation file %s for reading" % filename)
    except yaml.YAMLError as e:
        module.fail_json(msg="Failed to parse allocation file %s as YAML" % filename)
    if content is None:
        # If the file is empty, yaml.safe_load() will return None.
        content = {}
    return content


def write_allocations(module, allocations):
    """Write TCP port allocations to the allocation file."""
    filename = module.params['allocation_file']
    try:
        with open(filename, 'w') as f:
            yaml.dump(allocations, f, default_flow_style=False)
    except IOError as e:
        module.fail_json(msg="Failed to open allocation file %s for writing" % filename)
    except yaml.YAMLError as e:
        module.fail_json(msg="Failed to dump allocation file %s as YAML" % filename)

def is_valid_port(port):
    try:
        int(port)
    except ValueError:
        return False
    if port < 0:
        return False
    if port > 65535:
        return False
    return True


def update_allocation(module, allocations):
    """Allocate a TCP port of an Ironic serial console.

    :param module: AnsibleModule instance
    :param allocations: Existing IP address allocations
    """
    nodes = module.params['nodes']

    allocation_pool_start = module.params['allocation_pool_start']
    allocation_pool_end = module.params['allocation_pool_end']
    result = {
        'changed': False,
        'ports': {}
    }
    object_name = "serial_console_allocations"
    console_allocations = allocations.setdefault(object_name, {})
    invalid_allocations = {node: port for node, port in console_allocations.items()
                           if not is_valid_port(port)}
    if invalid_allocations:
        module.fail_json(msg="Found invalid existing allocations in %s: %s" %
            (object_name,
             ", ".join("%s: %s" % (node, port)
                       for node, port in invalid_allocations.items())))

    allocated_consoles = { int(x) for x in  console_allocations.values() }
    allocation_pool = { x for x in range(allocation_pool_start, allocation_pool_end + 1) }
    free_ports = list(allocation_pool - allocated_consoles)
    free_ports.sort(reverse=True)

    for node in nodes:
        if node not in console_allocations:
            if len(free_ports) < 1:
                module.fail_json(msg="No unallocated TCP ports for %s in %s" % (node, object_name))
            result['changed'] = True
            free_port = free_ports.pop()
            console_allocations[node] = free_port
        result['ports'][node] = console_allocations[node]
    return result


def allocate(module):
    """Allocate a TCP port an ironic serial console, updating the allocation file."""
    allocations = read_allocations(module)
    result = update_allocation(module, allocations)
    if result['changed'] and not module.check_mode:
        write_allocations(module, allocations)
    return result


def main():
    module = AnsibleModule(
        argument_spec=dict(
            nodes=dict(required=True, type='list'),
            allocation_pool_start=dict(required=True, type='int'),
            allocation_pool_end=dict(required=True, type='int'),
            allocation_file=dict(required=True, type='str'),
        ),
        supports_check_mode=True,
    )

    # Fail if there were any exceptions when importing modules.
    if IMPORT_ERRORS:
        module.fail_json(msg="Import errors: %s" %
                         ", ".join([repr(e) for e in IMPORT_ERRORS]))

    try:
        results = allocate(module)
    except Exception as e:
        module.fail_json(msg="Failed to allocate TCP port: %s" % repr(e))
    else:
        module.exit_json(**results)


if __name__ == '__main__':
    main()
