# Copyright (c) 2018 StackHPC Ltd.
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

import os
import os.path

from kayobe.tests.molecule import utils

import pytest
import testinfra.utils.ansible_runner


testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ['MOLECULE_INVENTORY_FILE']).get_hosts('all')


@pytest.mark.parametrize(
    'path',
    ['aodh',
     'cinder',
     'cloudkitty',
     'designate',
     'fluentd/filter',
     'fluentd/input',
     'fluentd/output',
     'glance',
     'grafana',
     'heat',
     'horizon',
     'ironic',
     'keystone',
     'magnum',
     'manila',
     'mariadb',
     'masakari',
     'murano',
     'neutron',
     'nova',
     'prometheus',
     'sahara',
     'swift'])
def test_service_config_directory_absent(host, path):
    path = os.path.join('/etc/kolla/config', path)
    utils.test_path_absent(host, path)
