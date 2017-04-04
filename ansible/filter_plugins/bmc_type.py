def bmc_type_from_system_vendor(system_vendor):
    if not system_vendor:
        return None
    if system_vendor.get('manufacturer') == 'Dell Inc.':
        return 'idrac'
    return None


class FilterModule(object):
    """BMC type filters."""

    def filters(self):
        return {
            'bmc_type_from_system_vendor': bmc_type_from_system_vendor,
        }
