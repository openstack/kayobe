# Kayobe

## Overiew

Kayobe is a tool for automating deployment of Scientific OpenStack onto bare
metal. Kayobe is composed of Ansible playbooks, a python module, and makes
heavy use of the OpenStack Kolla project.

## Prerequisites

Currently Kayobe supports the following Operating Systems:

- CentOS 7.3

To avoid conflicts with python packages installed by the system package manager
it is recommended to install Kayobe in a virtualenv. Ensure that the
`virtualenv` python module is available on the control host. For example, on
CentOS:

    $ yum install -y python-virtualenv

## Installation

This guide will describe how to install Kayobe from source in a virtualenv.
First, obtain the Kayobe source code. For example:

    $ git clone https://github.com/stackhpc/kayobe

To create a virtualenv for Kayobe:

    $ cd kayobe
    $ virtualenv kayobe-venv

Activate the virtualenv and update pip:

    $ source kayobe-venv/bin/activate
    (kayobe-venv) $ pip install -U pip

Install Kayobe and its dependencies using the source code checkout:

    (kayobe-venv) $ pip install .

At this point the `kayobe` Command Line Interface (CLI) should be available. To
see information on how to use the CLI:

    (kayobe-venv) $ kayobe help

Finally, deactivate the virtualenv:

    (kayobe-venv) $ deactivate

## Configuration

Kayobe configuration is by default located in `/etc/kayobe` on the Ansible
control host. This can be overridden to a different location to avoid touching
the system configuration directory by setting the environment variable
`KAYOBE_CONFIG_PATH`. Similarly, Kolla configuration on the Ansible control
host will by default be located in `/etc/kolla` and can be overridden via
`KOLLA_CONFIG_PATH`.

The baseline Kayobe configuration should be copied to the Kayobe configuration
path:

    $ cp -r etc/ ${KAYOBE_CONFIG_PATH:-/etc/kayobe}

Once in place, each of the YAML files should be inspected and configured as
required.

## Usage

This section describes usage of Kayobe to install an OpenStack cloud onto bare
metal. We assume access is available to a node which will act as the hypervisor
hosting the seed node in a VM. We also assume that this seed hypervisor has
access to the bare metal nodes that will form the OpenStack control plane.
Finally, we assume that the control plane nodes have access to the bare metal
nodes that will form the workload node pool.

NOTE: Where a prompt starts with `(kayobe-venv)` it is implied that the user
has activated the Kayobe virtualenv. This can be done as follows:

    $ source kayobe-venv/bin/activate

To deactivate the virtualenv:

    (kayobe-venv) $ deactivate

### Ansible Control Host

Before starting deployment we must bootstrap the Ansible control host. Tasks
here include:

- Install Ansible and role dependencies from Ansible Galaxy
- Generate an SSH key if necessary and add it to authorized\_keys
- Configure Kolla Ansible

To bootstrap the Ansible control host:

    (kayobe-venv) $ kayobe control host bootstrap

### Seed

The seed hypervisor should have CentOS and `libvirt` installed. It should have
`libvirt` networks configured for all networks that the seed VM needs access
to. To provision the seed VM:

    (kayobe-venv) $ kayobe seed vm provision

When this command has completed the seed VM should be active and accessible via
SSH. Kayobe will update the Ansible inventory with the dynamically assigned IP
address of the VM.

At this point the seed services need to be deployed on the seed VM. These
services include Docker and the Kolla `bifrost-deploy` container. This command
will also build the image to be used to deploy the overcloud nodes using Disk
Image Builder (DIB). To configure the seed host OS:

    (kayobe-venv) $ kayobe seed host configure

To deploy the seed services in containers:

    (kayobe-venv) $ kayobe seed service deploy

After this command has completed the seed services will be active. For SSH
access to the seed VM, first determine the seed VM's IP address:

    $ sudo virsh domifaddr <seed VM name>    

The `kayobe_user` variable determines which user account will be used by Kayobe
when accessing the machine via SSH. By default this is `stack`. Use this user
to access the seed:

    $ ssh stack@<seed VM IP>

To see the active Docker containers:

    $ docker ps

Leave the seed VM and return to the shell on the control host:

    $ exit

### Overcloud

Provisioning of the overcloud is performed by Bifrost running in a container on
the seed. An inventory of servers should be configured using the
`kolla_bifrost_servers` variable. To provision the overcloud nodes:

    (kayobe-venv) $ kayobe overcloud provision

After this command has completed the overcloud nodes should have been
provisioned with an OS image. To configure the overcloud hosts' OS:

    (kayobe-venv) $ kayobe overcloud host configure

To deploy the overcloud services in containers:

    (kayobe-venv) $ kayobe overcloud service deploy

Once this command has completed the overcloud nodes should have OpenStack
services running in Docker containers. Kolla writes out an environment file
that can be used to access the OpenStack services:

    $ source ${KOLLA_CONFIG_PATH:-/etc/kolla}/admin-openrc.sh

### Other Useful Commands

To run an arbitrary Kayobe playbook:

    (kayobe-venv) $ kayobe playbook run

To execute a Kolla Ansible command:

    (kayobe-venv) $ kayobe kolla ansible run

To dump Kayobe configuration for one or more hosts:

    (kayobe-venv) $ kayobe configuration dump
