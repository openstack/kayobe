DOCUMENTATION = '''
---
module: blockdevice_info
short_description: Returns information about block devices
version_added: "N/A"
description:
    - "Returns information about block devices"
author:
    - Will Szumski
'''

EXAMPLES = '''
- name: Retrieve information about block devices
  blockdevice_info:
  become: true
  register: result
'''

RETURN = '''
umounted:
    description: A list of all umounted block devices.
    type: list
    returned: always
'''

import json

from ansible.module_utils.basic import AnsibleModule

def _has_mounts(device):
    try:
        if device["mountpoint"]:
            return True
    # If unmounted, the JSON output contains "mountpoints": [null] so we handle
    # the KeyError here.
    except KeyError:
        if device["mountpoints"][0]:
            return True
    for child in device.get("children", []):
        if _has_mounts(child):
            return True
    return False

def unmounted(module, lsblk):
    result = []
    for device in lsblk.get("blockdevices", []):
        if not _has_mounts(device) and device["type"] == 'disk':
            result.append(device["name"])
    return result

def run_module():
    # The module takes no argumnets.
    module_args = dict()

    result = dict(
        changed=False,
        unmounted=[]
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    _rc, stdout, _stderr = module.run_command("lsblk -J")
    lsblk = json.loads(stdout)

    result['unmounted'] = unmounted(module, lsblk)

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
