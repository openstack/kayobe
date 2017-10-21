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
typically provided via the `dev-kayobe-config
<https://github.com/stackhpc/dev-kayobe-config/>`_ repository, although it is
also possible to use your own kayobe configuration.  This allows us to build a
development environment that is as close to production as possible.

Environments
============

The following development environments are supported:

* Overcloud (single OpenStack controller)
* Seed hypervisor
* Seed VM

The seed VM environment may be used in an environment already deployed as a
seed hypervisor.

Overcloud
=========

Preparation
-----------

Clone the kayobe repository::

    git clone https://github.com/stackhpc/kayobe

Change the current directory to the kayobe repository::

    cd kayobe

Clone the ``dev-kayobe-config`` repository to ``config/src/kayobe-config``::

    mkdir -p config/src
    git clone https://github.com/stackhpc/dev-kayobe-config config/src/kayobe-config

Follow the steps in :ref:`development-vagrant` to prepare your environment for
use with Vagrant and bring up a Vagrant VM.

Inspect the kayobe configuration and make any changes necessary for your
environment.

Usage
-----

SSH into the Vagrant VM::

    vagrant ssh

Run the ``dev/overcloud-deploy.sh`` script to deploy the OpenStack control
plane::

    /vagrant/kayobe/dev/overcloud-deploy.sh

Upon successful completion of this script, the control plane will be active.

Seed Hypervisor
===============

The seed hypervisor development environment is supported for CentOS 7.  The
system must be either bare metal, or a VM on a system with nested
virtualisation enabled.

Preparation
-----------

The following commands should be executed on the seed hypervisor.

Clone the kayobe repository::

    git clone https://github.com/stackhpc/kayobe

Change the current directory to the kayobe repository::

    cd kayobe

Clone the ``add-seed-and-hv`` branch of the ``dev-kayobe-config`` repository to
``config/src/kayobe-config``::

    mkdir -p config/src
    git clone https://github.com/stackhpc/dev-kayobe-config -b add-seed-and-hv config/src/kayobe-config

Inspect the kayobe configuration and make any changes necessary for your
environment.

Usage
-----

Run the ``dev/seed-hypervisor-deploy.sh`` script to deploy the seed
hypervisor::

    ./dev/seed-hypervisor-deploy.sh

Upon successful completion of this script, the seed hypervisor will be active.

Seed VM
=======

The seed VM should be deployed on a system configured as a libvirt/KVM
hypervisor, using the kayobe seed hypervisor support or otherwise.

Preparation
-----------

The following commands should be executed on the seed hypervisor.

Change the current directory to the kayobe repository::

    git clone https://github.com/stackhpc/kayobe

Change to the ``kayobe`` directory::

    cd kayobe

Clone the ``add-seed-and-hv`` branch of the ``dev-kayobe-config`` repository to
``config/src/kayobe-config``::

    mkdir -p config/src
    git clone https://github.com/stackhpc/dev-kayobe-config -b add-seed-and-hv config/src/kayobe-config

Inspect the kayobe configuration and make any changes necessary for your
environment.

Usage
=====

Run the ``dev/seed-deploy.sh`` script to deploy the seed VM::

    ./dev/seed-deploy.sh

Upon successful completion of this script, the seed VM will be active.  The
seed VM may be accessed via SSH as the ``stack`` user::

    ssh stack@192.168.33.5
