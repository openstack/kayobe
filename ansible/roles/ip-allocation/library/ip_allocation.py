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

DOCUMENTATION = """
module: ip_allocation
short_description: Allocate an IP address for a host from a pool
author: Mark Goddard (mark@stackhpc.com)
options:
  - option-name: net_name
    description: Name of the network
    required: True
    type: string
  - option-name: hostname
    description: Name of the host
    required: True
    type: string
  - option-name: cidr
    description: IP Network in CIDR format
    required: True
    type: string
  - option-name: allocation_pool_start
    description: First address of the pool from which to allocate
    required: False
    type: string
  - option-name: allocation_pool_end
    description: Last address of the pool from which to allocate
    required: False
    type: string
  - option-name: allocation_file
    description: >
      Path to a file in which to store the allocations. Will be created if it
      does not exist.
    required: True
    type: string
requirements:
  - netaddr
  - PyYAML
"""

EXAMPLES = """
- name: Ensure host has an IP address
  ip_allocation:
    net_name: my-network
    hostname: my-host
    cidr: 10.0.0.0/24
    allocation_pool_start: 10.0.0.1
    allocation_pool_end: 10.0.0.254
    allocation_file: /path/to/allocation/file.yml
"""

RETURN = """
ip:
  description: The allocated IP address
  returned: success
  type: string
  sample: 10.0.0.1
"""

from ansible.module_utils.basic import *
import sys

# Store a list of import errors to report to the user.
IMPORT_ERRORS=[]
try:
    import netaddr
except Exception as e:
    IMPORT_ERRORS.append(e)
try:
    import yaml
except Exception as e:
    IMPORT_ERRORS.append(e)


def read_allocations(module):
    """Read IP address allocations from the allocation file."""
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
    """Write IP address allocations to the allocation file."""
    filename = module.params['allocation_file']
    try:
        with open(filename, 'w') as f:
            yaml.dump(allocations, f, default_flow_style=False)
    except IOError as e:
        module.fail_json(msg="Failed to open allocation file %s for writing" % filename)
    except yaml.YAMLError as e:
        module.fail_json(msg="Failed to dump allocation file %s as YAML" % filename)


def update_allocation(module, allocations):
    """Allocate an IP address on a network for a host.

    :param module: AnsibleModule instance
    :param allocations: Existing IP address allocations
    """
    net_name = module.params['net_name']
    hostname = module.params['hostname']
    cidr = module.params['cidr']
    allocation_pool_start = module.params['allocation_pool_start']
    allocation_pool_end = module.params['allocation_pool_end']
    network = netaddr.IPNetwork(cidr)
    result = {
        'changed': False,
    }
    object_name = "%s_ips" % net_name
    net_allocations = allocations.setdefault(object_name, {})
    invalid_allocations = {hn: ip for hn, ip in net_allocations.items()
                           if netaddr.IPAddress(ip) not in network}
    if invalid_allocations:
        module.fail_json(msg="Found invalid existing allocations in network %s: %s" %
            (network,
             ", ".join("%s: %s" % (hn, ip)
                       for hn, ip in invalid_allocations.items())))
    if hostname not in net_allocations:
        result['changed'] = True
        allocated_ips = netaddr.IPSet(net_allocations.values())
        if allocation_pool_start and allocation_pool_end:
            allocation_pool = netaddr.IPRange(allocation_pool_start, allocation_pool_end)
            allocation_pool = netaddr.IPSet(allocation_pool)
        else:
            allocation_pool = netaddr.IPSet([network])
            if network.prefixlen != 32:
                reserved_ips = [network.network, network.broadcast]
                allocation_pool -= netaddr.IPSet(reserved_ips)
        free_ips = allocation_pool - allocated_ips
        for free_cidr in free_ips.iter_cidrs():
            ip = free_cidr[0]
            break
        else:
            module.fail_json(msg="No unallocated IP addresses for %s in %s" % (hostname, net_name))
        free_ips.remove(ip)
        net_allocations[hostname] = str(ip)
    result['ip'] = net_allocations[hostname]
    return result


def allocate(module):
    """Allocate an IP address for a host, updating the allocation file."""
    allocations = read_allocations(module)
    result = update_allocation(module, allocations)
    if result['changed'] and not module.check_mode:
        write_allocations(module, allocations)
    return result


def main():
    module = AnsibleModule(
        argument_spec=dict(
            net_name=dict(required=True, type='str'),
            hostname=dict(required=True, type='str'),
            cidr=dict(required=True, type='str'),
            allocation_pool_start=dict(required=False, type='str'),
            allocation_pool_end=dict(required=False, type='str'),
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
        module.fail_json(msg="Failed to allocate IP address: %s" % repr(e))
    else:
        module.exit_json(**results)


if __name__ == '__main__':
    main()
