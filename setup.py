#!/usr/bin/env python

from setuptools import setup, find_packages


PROJECT = 'kayobe'
VERSION = '0.1'

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
    install_requires=['cliff'],

    namespace_packages=[],
    packages=find_packages(),
    include_package_data=True,

    entry_points={
        'console_scripts': [
            'kayobe = kayobe.cmd.kayobe:main'
        ],
        'kayobe.cli': [
            'control_host_bootstrap = kayobe.cli.commands:ControlHostBootstrap',
            'configuration_dump = kayobe.cli.commands:ConfigurationDump',
            'kolla_ansible_run = kayobe.cli.commands:KollaAnsibleRun',
            'overcloud_deploy = kayobe.cli.commands:OvercloudDeploy',
            'overcloud_provision = kayobe.cli.commands:OvercloudProvision',
            'playbook_run = kayobe.cli.commands:PlaybookRun',
            'seed_deploy = kayobe.cli.commands:SeedDeploy',
            'seed_vm_provision = kayobe.cli.commands:SeedVMProvision',
        ],
    },

    zip_safe=False,
)
