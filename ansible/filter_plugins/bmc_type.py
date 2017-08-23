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

def bmc_type_from_system_vendor(system_vendor):
    if not system_vendor:
        return None
    if system_vendor.get('manufacturer') == 'Dell Inc.':
        return 'idrac'
    if system_vendor.get('manufacturer') == 'Intel Corporation':
        return 'intel'
    return None


class FilterModule(object):
    """BMC type filters."""

    def filters(self):
        return {
            'bmc_type_from_system_vendor': bmc_type_from_system_vendor,
        }
