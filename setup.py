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

#!/usr/bin/env python

from setuptools import setup, find_packages


PROJECT = 'kayobe'
VERSION = '2.0.0'

try:
    long_description = open('README.md', 'rt').read()
except IOError:
    long_description = ''

setup(
    name=PROJECT,
    version=VERSION,

    description='OpenStack deployment for scientific computing',
    long_description=long_description,

    author='StackHPC',
    author_email='mark@stackhpc.com',

    url='https://github.com/stackhpc/kayobe',
    download_url='https://github.com/stackhpc/kayobe/tarball/master',

    provides=[],
    install_requires=open('requirements.txt', 'rt').read().splitlines(),

    namespace_packages=[],
    packages=find_packages(),
    include_package_data=True,

    entry_points={
        'console_scripts': [
            'kayobe = kayobe.cmd.kayobe:main',
            'kayobe-vault-password-helper = kayobe.cmd.kayobe_vault_password_helper:main',
        ],
        'kayobe.cli': [
            'control_host_bootstrap = kayobe.cli.commands:ControlHostBootstrap',
            'control_host_upgrade = kayobe.cli.commands:ControlHostUpgrade',
            'configuration_dump = kayobe.cli.commands:ConfigurationDump',
            'kolla_ansible_run = kayobe.cli.commands:KollaAnsibleRun',
            'overcloud_bios_raid_configure = kayobe.cli.commands:OvercloudBIOSRAIDConfigure',
            'overcloud_container_image_build = kayobe.cli.commands:OvercloudContainerImageBuild',
            'overcloud_container_image_pull = kayobe.cli.commands:OvercloudContainerImagePull',
            'overcloud_deployment_image_build = kayobe.cli.commands:OvercloudDeploymentImageBuild',
            'overcloud_deprovision = kayobe.cli.commands:OvercloudDeprovision',
            'overcloud_hardware_inspect = kayobe.cli.commands:OvercloudHardwareInspect',
            'overcloud_host_configure = kayobe.cli.commands:OvercloudHostConfigure',
            'overcloud_host_upgrade = kayobe.cli.commands:OvercloudHostUpgrade',
            'overcloud_introspection_data_save = kayobe.cli.commands:OvercloudIntrospectionDataSave',
            'overcloud_inventory_discover = kayobe.cli.commands:OvercloudInventoryDiscover',
            'overcloud_post_configure = kayobe.cli.commands:OvercloudPostConfigure',
            'overcloud_provision = kayobe.cli.commands:OvercloudProvision',
            'overcloud_service_deploy = kayobe.cli.commands:OvercloudServiceDeploy',
            'overcloud_service_destroy = kayobe.cli.commands:OvercloudServiceDestroy',
            'overcloud_service_reconfigure = kayobe.cli.commands:OvercloudServiceReconfigure',
            'overcloud_service_upgrade = kayobe.cli.commands:OvercloudServiceUpgrade',
            'physical_network_configure = kayobe.cli.commands:PhysicalNetworkConfigure',
            'playbook_run = kayobe.cli.commands:PlaybookRun',
            'seed_container_image_build = kayobe.cli.commands:SeedContainerImageBuild',
            'seed_deployment_image_build = kayobe.cli.commands:SeedDeploymentImageBuild',
            'seed_host_configure = kayobe.cli.commands:SeedHostConfigure',
            'seed_hypervisor_host_configure = kayobe.cli.commands:SeedHypervisorHostConfigure',
            'seed_service_deploy = kayobe.cli.commands:SeedServiceDeploy',
            'seed_vm_deprovision = kayobe.cli.commands:SeedVMDeprovision',
            'seed_vm_provision = kayobe.cli.commands:SeedVMProvision',
        ],
    },

    zip_safe=False,
)
