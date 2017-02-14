#!/usr/bin/python

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


DOCUMENTATION = """ 
WM
"""

EXAMPLES = """ 
WM
"""


def read_allocations(module):
    """Read IP address allocations from the allocation file."""
    filename = module.params['allocation_file']
    try:
        with open(filename, 'r') as f:
            return yaml.load(f)
    except IOError as e:
        module.fail_json(msg="Failed to open allocation file %s for reading" % filename)
    except yaml.YAMLError as e:
        module.fail_json(msg="Failed to parse allocation file %s as YAML" % filename)


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
    network = netaddr.IPNetwork(cidr)
    result = {
        'changed': False,
    }
    object_name = "%s_ips" % net_name
    net_allocations = allocations.setdefault(object_name, {})
    invalid_allocations = {hn: ip for hn, ip in net_allocations.items()
                           if ip not in network}
    if invalid_allocations:
        module.fail_json(msg="Found invalid existing allocations in network %s: %s" %
            (network, ", ".join("%s: %s" % (hn, ip) for hn, ip in invalid_allocations.items())))
    if hostname not in net_allocations:
        result['changed'] = True
        ips = netaddr.IPSet(net_allocations.values())
        free_ips = netaddr.IPSet([network]) - ips
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
