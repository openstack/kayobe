.. _development-automated:

===============
Automated Setup
===============

This section provides information on the development tools provided by kayobe
to automate the deployment of various development environments.

For a manual procedure, see :ref:`development-manual`.

Overview
========

The kayobe development environment automation tooling is built using simple
shell scripts.  Some minimal configuration can be applied by setting the
environment variables in `dev/config.sh`.  Control plane configuration is
typically provided via the `kayobe-config-dev
<https://opendev.org/openstack/kayobe-config-dev>`_ repository,
although it is also possible to use your own kayobe configuration.  This allows
us to build a development environment that is as close to production as
possible.

Environments
============

The following development environments are supported:

* Overcloud (single OpenStack controller)
* Seed
* Seed hypervisor
* Seed VM

The seed VM environment may be used in an environment already deployed as a
seed hypervisor.

Overcloud
=========

Preparation
-----------

Clone the kayobe repository::

    git clone https://opendev.org/openstack/kayobe.git

Change the current directory to the kayobe repository::

    cd kayobe

Clone the ``kayobe-config-dev`` repository to ``config/src/kayobe-config``::

    mkdir -p config/src
    git clone https://opendev.org/openstack/kayobe-config-dev.git config/src/kayobe-config

Inspect the kayobe configuration and make any changes necessary for your
environment.

If using Vagrant, follow the steps in :ref:`development-vagrant` to prepare
your environment for use with Vagrant and bring up a Vagrant VM.

If not using Vagrant, the default development configuration expects the
presence of a bridge interface on the OpenStack controller host to carry
control plane traffic.  The bridge should be named ``breth1`` with a single
port ``eth1``, and an IP address of ``192.168.33.3/24``.  This can be modified
by editing
``config/src/kayobe-config/etc/kayobe/inventory/group_vars/controllers/network-interfaces``.
Alternatively, this can be added using the following commands::

    sudo ip l add breth1 type bridge
    sudo ip l set breth1 up
    sudo ip a add 192.168.33.3/24 dev breth1
    sudo ip l add eth1 type dummy
    sudo ip l set eth1 up
    sudo ip l set eth1 master breth1

Usage
-----

If using Vagrant, SSH into the Vagrant VM and change to the shared directory::

    vagrant ssh
    cd /vagrant

If not using Vagrant, run the ``dev/install-dev.sh`` script to install kayobe and
its dependencies in a virtual environment::

    ./dev/install-dev.sh

.. note::

   This will create an :ref:`editable install <installation-editable>`.
   It is also possible to install kayobe in a non-editable way, such that
   changes will not been seen until you reinstall the package. To do this you
   can run ``./dev/install.sh``.

Run the ``dev/overcloud-deploy.sh`` script to deploy the OpenStack control
plane::

    ./dev/overcloud-deploy.sh

Upon successful completion of this script, the control plane will be active.

Testing
-------

Scripts are provided for testing the creation of virtual and bare metal
instances.

Virtual Machines
^^^^^^^^^^^^^^^^

The control plane can be tested by running the ``dev/overcloud-test-vm.sh``
script. This will run the ``init-runonce`` setup script provided by Kolla
Ansible that registers images, networks, flavors etc. It will then deploy a
virtual server instance, and delete it once it becomes active::

    ./dev/overcloud-test-vm.sh

Bare Metal Compute
^^^^^^^^^^^^^^^^^^

For a control plane with Ironic enabled, a "bare metal" instance can be
deployed. We can use the `Tenks <https://tenks.readthedocs.io/en/latest/>`__
project to create fake bare metal nodes.

Clone the tenks repository::

    git clone https://opendev.org/openstack/tenks.git

Optionally, edit the Tenks configuration file,
``dev/tenks-deploy-config-compute.yml``.

Run the ``dev/tenks-deploy-compute.sh`` script to deploy Tenks::

    ./dev/tenks-deploy-compute.sh ./tenks

Check that Tenks has created VMs called ``tk0`` and ``tk1``::

    sudo virsh -c qemu+unix:///system?socket=/var/run/libvirt-tenks/libvirt-sock list --all

Verify that VirtualBMC is running::

    ~/tenks-venv/bin/vbmc list

Configure the firewall to allow the baremetal nodes to access OpenStack
services::

    ./dev/configure-firewall.sh

We are now ready to run the ``dev/overcloud-test-baremetal.sh`` script. This
will run the ``init-runonce`` setup script provided by Kolla Ansible that
registers images, networks, flavors etc. It will then deploy a bare metal
server instance, and delete it once it becomes active::

    ./dev/overcloud-test-baremetal.sh

The machines and networking created by Tenks can be cleaned up via
``dev/tenks-teardown-compute.sh``::

    ./dev/tenks-teardown-compute.sh ./tenks

Upgrading
---------

It is possible to test an upgrade from a previous release by running the
``dev/overcloud-upgrade.sh`` script::

    ./dev/overcloud-upgrade.sh

.. _development-automated-seed:

Seed
====

These instructions cover deploying the seed services directly rather than in a
VM. See :ref:`development-automated-seed-vm` for instructions covering
deployment of the seed services in a VM.

Preparation
-----------

Clone the kayobe repository::

    git clone https://opendev.org/openstack/kayobe.git

Change to the ``kayobe`` directory::

    cd kayobe

Clone the ``kayobe-config-dev`` repository to ``config/src/kayobe-config``::

    mkdir -p config/src
    git clone https://opendev.org/openstack/kayobe-config-dev.git config/src/kayobe-config

Inspect the kayobe configuration and make any changes necessary for your
environment.

The default development configuration expects the presence of a bridge
interface on the seed host to carry provisioning traffic.  The bridge should be
named ``breth1`` with a single port ``eth1``, and an IP address of
``192.168.33.5/24``.  This can be modified by editing
``config/src/kayobe-config/etc/kayobe/inventory/group_vars/seed/network-interfaces``.
Alternatively, this can be added using the following commands::

    sudo ip l add breth1 type bridge
    sudo ip l set breth1 up
    sudo ip a add 192.168.33.5/24 dev breth1
    sudo ip l add eth1 type dummy
    sudo ip l set eth1 up
    sudo ip l set eth1 master breth1

Usage
-----

Run the ``dev/install.sh`` script to install kayobe and its dependencies in a
virtual environment::

    ./dev/install.sh

Run the ``dev/seed-deploy.sh`` script to deploy the seed services::

    ./dev/seed-deploy.sh

Upon successful completion of this script, the seed will be active.

Testing
-------

The seed services may be tested using the `Tenks
<https://tenks.readthedocs.io/en/latest/>`__ project to create fake bare metal
nodes.

Clone the tenks repository::

    git clone https://opendev.org/openstack/tenks.git

Optionally, edit the Tenks configuration file,
``dev/tenks-deploy-config-overcloud.yml``.

Run the ``dev/tenks-deploy-overcloud.sh`` script to deploy Tenks::

    ./dev/tenks-deploy-overcloud.sh ./tenks

Check that Tenks has created a VM called ``controller0``::

    sudo virsh list --all

Verify that VirtualBMC is running::

    ~/tenks-venv/bin/vbmc list

The machines and networking created by Tenks can be cleaned up via
``dev/tenks-teardown-overcloud.sh``::

    ./dev/tenks-teardown-overcloud.sh ./tenks

.. _development-automated-seed-hypervisor:

Seed Hypervisor
===============

The seed hypervisor development environment is supported for CentOS 7.  The
system must be either bare metal, or a VM on a system with nested
virtualisation enabled.

Preparation
-----------

The following commands should be executed on the seed hypervisor.

Clone the kayobe repository::

    git clone https://opendev.org/openstack/kayobe.git

Change the current directory to the kayobe repository::

    cd kayobe

Clone the ``add-seed-and-hv`` branch of the ``kayobe-config-dev`` repository to
``config/src/kayobe-config``::

    mkdir -p config/src
    git clone https://github.com/markgoddard/dev-kayobe-config -b add-seed-and-hv config/src/kayobe-config

Inspect the kayobe configuration and make any changes necessary for your
environment.

Usage
-----

Run the ``dev/install-dev.sh`` script to install kayobe and its dependencies in a
virtual environment::

    ./dev/install-dev.sh

.. note::

   This will create an :ref:`editable install <installation-editable>`.
   It is also possible to install kayobe in a non-editable way, such that
   changes will not been seen until you reinstall the package. To do this you
   can run ``./dev/install.sh``.

Run the ``dev/seed-hypervisor-deploy.sh`` script to deploy the seed
hypervisor::

    ./dev/seed-hypervisor-deploy.sh

Upon successful completion of this script, the seed hypervisor will be active.

.. _development-automated-seed-vm:

Seed VM
=======

The seed VM should be deployed on a system configured as a libvirt/KVM
hypervisor, using :ref:`development-automated-seed-hypervisor` or otherwise.

Preparation
-----------

The following commands should be executed on the seed hypervisor.

Clone the kayobe repository::

    git clone https://opendev.org/openstack/kayobe.git

Change to the ``kayobe`` directory::

    cd kayobe

Clone the ``add-seed-and-hv`` branch of the ``kayobe-config-dev`` repository to
``config/src/kayobe-config``::

    mkdir -p config/src
    git clone https://github.com/markgoddard/dev-kayobe-config -b add-seed-and-hv config/src/kayobe-config

Inspect the kayobe configuration and make any changes necessary for your
environment.

Usage
-----

Run the ``dev/install-dev.sh`` script to install kayobe and its dependencies in a
virtual environment::

    ./dev/install-dev.sh

.. note::

   This will create an :ref:`editable install <installation-editable>`.
   It is also possible to install kayobe in a non-editable way, such that
   changes will not been seen until you reinstall the package. To do this you
   can run ``./dev/install.sh``.

Run the ``dev/seed-deploy.sh`` script to deploy the seed VM::

    ./dev/seed-deploy.sh

Upon successful completion of this script, the seed VM will be active.  The
seed VM may be accessed via SSH as the ``stack`` user::

    ssh stack@192.168.33.5

It is possible to test an upgrade by running the ``dev/seed-upgrade.sh``
script::

    ./dev/seed-upgrade.sh
