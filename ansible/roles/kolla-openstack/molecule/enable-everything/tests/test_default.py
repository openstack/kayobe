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
import yaml


testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ['MOLECULE_INVENTORY_FILE']).get_hosts('all')

@pytest.mark.parametrize(
    'path',
    ['aodh.conf',
     'barbican.conf',
     'cinder.conf',
     'cloudkitty.conf',
     'designate.conf',
     'galera.cnf',
     'glance.conf',
     'grafana.ini',
     'heat.conf',
     'ironic.conf',
     'keystone.conf',
     'magnum.conf',
     'manila.conf',
     'masakari.conf',
     'multipath.conf',
     'neutron/ml2_conf.ini',
     'neutron.conf',
     'nova.conf',
     'octavia.conf',
     'placement.conf',
     'backup.my.cnf'])
def test_service_ini_file(host, path):
    # TODO(mgoddard): Check more of config file contents.
    # Tests config added with extra vars e.g kolla_extra_aodh. I.e the
    # the internal role templates.
    path = os.path.join('/etc/kolla/config', path)
    extra_section = 'extra-%s' % os.path.basename(path)
    expected = {extra_section: {'foo': 'bar'}}
    utils.test_ini_file(host, path, expected=expected)

@pytest.mark.parametrize(
    'path',
    ['aodh.conf',
     'barbican.conf',
     'cinder.conf',
     'cloudkitty.conf',
     'designate.conf',
     'galera.cnf',
     'glance.conf',
     'grafana.ini',
     'heat.conf',
     'ironic.conf',
     'keystone.conf',
     'magnum.conf',
     'manila.conf',
     'masakari.conf',
     'neutron/ml2_conf.ini',
     'neutron.conf',
     'nova.conf',
     'octavia.conf',
     'placement.conf',
     'backup.my.cnf'])
def test_service_ini_file_extra_confs(host, path):
    # Tests config added via extra config files
    path = os.path.join('/etc/kolla/config', path)
    extra_section = 'extra-file-%s' % os.path.basename(path)
    expected = {extra_section: {'bar': 'baz'}}
    utils.test_ini_file(host, path, expected=expected)

@pytest.mark.parametrize(
    'path',
    ['ironic/ironic-agent.initramfs',
     'ironic/ironic-agent.kernel',
     'nova/nova-libvirt/cacert.pem',
     'nova/nova-libvirt/clientcert.pem',
     'nova/nova-libvirt/clientkey.pem'])
def test_service_non_ini_file(host, path):
    # TODO(mgoddard): Check config file contents.
    path = os.path.join('/etc/kolla/config', path)
    utils.test_file(host, path)

@pytest.mark.parametrize(
    'path,regex',
    [('fluentd/input/01-test.conf', 'grepme')])
def test_service_non_ini_file_regex(host, path, regex):
    path = os.path.join('/etc/kolla/config', path)
    utils.test_regex_in_file(host, path, regex=regex)

@pytest.mark.parametrize(
    'relative_path',
    ['aodh/dummy.yml',
     'opensearch.yml',
     'prometheus/prometheus.yml.d/dummy.yml'])
def test_service_extra_yml_config(host, relative_path):
    path = os.path.join('/etc/kolla/config', relative_path)
    utils.test_file(host, path)
    content = yaml.safe_load(host.file(path).content_string)
    assert content["dummy_variable"] == 123

def test_service_extra_ini_config(host):
    relative_path = "aodh/dummy.ini"
    path = os.path.join('/etc/kolla/config', relative_path)
    utils.test_file(host, path)
    expected = {
        "dummy-section": {"dummy_variable": "123"}
    }
    utils.test_ini_file(host, path, expected=expected)
