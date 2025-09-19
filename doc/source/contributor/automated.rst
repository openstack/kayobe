.. _contributor-automated:

===============
Automated Setup
===============

This section provides information on the development tools provided by Kayobe
to automate the deployment of various development environments.

For a manual procedure, see :ref:`contributor-manual`.

Overview
========

The Kayobe development environment automation tooling is built using simple
shell scripts.  Some minimal configuration can be applied by setting the
environment variables in ``dev/config.sh``.  Control plane configuration is
typically provided via the `kayobe-config-dev
<https://opendev.org/openstack/kayobe-config-dev>`_ repository,
although it is also possible to use your own Kayobe configuration.  This allows
us to build a development environment that is as close to production as
possible.

Environments
============

The following development environments are supported:

* Overcloud (single OpenStack controller)
* Seed

The `Universe from Nothing
<https://github.com/stackhpc/a-universe-from-nothing/>`_ workshop may be of use
for more advanced testing scenarios involving a seed hypervisor, seed VM, and
separate control and compute nodes.

.. _contributor-automated-overcloud:

Overcloud
=========

Preparation
-----------

Clone the Kayobe repository:

.. parsed-literal::

   git clone \https://opendev.org/openstack/kayobe.git -b |current_release_git_branch_name|

Change the current directory to the Kayobe repository::

    cd kayobe

Clone the ``kayobe-config-dev`` repository to ``config/src/kayobe-config``

.. parsed-literal::

   mkdir -p config/src
   git clone \https://opendev.org/openstack/kayobe-config-dev.git config/src/kayobe-config -b |current_release_git_branch_name|

Inspect the Kayobe configuration and make any changes necessary for your
environment.

If you want to test bare metal compute nodes as described in
:ref:`testing_bare_metal_compute`, enable Ironic by adding the following to
``config/src/kayobe-config/etc/kayobe/kolla.yml``:

.. code-block:: yaml

   kolla_enable_ironic: True

If using Vagrant, follow the steps in :ref:`contributor-vagrant` to prepare
your environment for use with Vagrant and bring up a Vagrant VM.

If not using Vagrant, the default development configuration expects the
presence of a bridge interface on the OpenStack controller host to carry
control plane traffic.  The bridge should be named ``breth1`` with a single
port ``dummy1``, and an IP address of ``192.168.33.3/24``.  This can be
modified by editing
``config/src/kayobe-config/etc/kayobe/inventory/group_vars/controllers/network-interfaces``.

This can be added using the following commands::

    sudo ip l add breth1 type bridge
    sudo ip l set breth1 up
    sudo ip a add 192.168.33.3/24 dev breth1
    sudo ip l add dummy1 type dummy
    sudo ip l set dummy1 up
    sudo ip l set dummy1 master breth1

Configuration
-------------

Enable TLS
^^^^^^^^^^

Apply the following configuration if you wish to enable TLS for the OpenStack
API:

Set the following option in ``config/src/kayobe-config/etc/kayobe/kolla.yml``:

.. code-block:: yaml

   kolla_enable_tls_internal: "yes"

Set the following options in
``config/src/kayobe-config/etc/kayobe/kolla/globals.yml``:

.. code-block:: yaml

   kolla_copy_ca_into_containers: "yes"
   openstack_cacert: "{% if os_distribution == 'ubuntu' %}/etc/ssl/certs/ca-certificates.crt{% else %}/etc/pki/tls/certs/ca-bundle.crt{% endif %}"
   kolla_admin_openrc_cacert: "{% if os_distribution == 'ubuntu' %}/etc/ssl/certs/ca-certificates.crt{% else %}/etc/pki/tls/certs/ca-bundle.crt{% endif %}"

Usage
-----

If using Vagrant, SSH into the Vagrant VM and change to the shared directory::

    vagrant ssh
    cd /vagrant

If not using Vagrant, run the ``dev/install-dev.sh`` script to install Kayobe and
its dependencies in a Python virtual environment::

    ./dev/install-dev.sh

.. note::

   This will create an :ref:`editable install <installation-editable>`.
   It is also possible to install Kayobe in a non-editable way, such that
   changes will not been seen until you reinstall the package. To do this you
   can run ``./dev/install.sh``.

If you are using TLS and wish to generate self-signed certificates::

    export KAYOBE_OVERCLOUD_GENERATE_CERTIFICATES=1

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

.. _testing_bare_metal_compute:

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

    sudo virsh list --all

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

.. _contributor-automated-seed:

Seed
====

These instructions cover deploying the seed services directly rather than in a
VM.

Preparation
-----------

Clone the Kayobe repository:

.. parsed-literal::

   git clone \https://opendev.org/openstack/kayobe.git -b |current_release_git_branch_name|

Change to the ``kayobe`` directory::

    cd kayobe

Clone the ``kayobe-config-dev`` repository to ``config/src/kayobe-config``:

.. parsed-literal::

   mkdir -p config/src
   git clone \https://opendev.org/openstack/kayobe-config-dev.git config/src/kayobe-config -b |current_release_git_branch_name|

Inspect the Kayobe configuration and make any changes necessary for your
environment.

The default development configuration expects the presence of a bridge
interface on the seed host to carry provisioning traffic.  The bridge should be
named ``breth1`` with a single port ``eth1``, and an IP address of
``192.168.33.5/24``.  This can be modified by editing
``config/src/kayobe-config/etc/kayobe/inventory/group_vars/seed/network-interfaces``.
Alternatively, this can be added using the following commands::

    sudo ip l add breth1 type bridge
    sudo ip l set breth1 up
    sudo ip a add 192.168.33.5/24 brd 192.168.33.255 dev breth1
    sudo ip l add dummy1 type dummy
    sudo ip l set dummy1 up
    sudo ip l set dummy1 master breth1

Usage
-----

Run the ``dev/install.sh`` script to install Kayobe and its dependencies in a
Python virtual environment::

    ./dev/install.sh

Run the ``dev/seed-deploy.sh`` script to deploy the seed services::

    export KAYOBE_SEED_VM_PROVISION=0
    ./dev/seed-deploy.sh

Upon successful completion of this script, the seed will be active.

Testing
-------

The seed services may be tested using the `Tenks
<https://tenks.readthedocs.io/en/latest/>`__ project to create fake bare metal
nodes.

If your seed has a non-standard MTU, you should set it via ``aio_mtu`` in
``etc/kayobe/networks.yml``.

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

It is now possible to discover, inspect and provision the controller VM::

    source dev/environment-setup.sh
    kayobe overcloud inventory discover
    kayobe overcloud hardware inspect
    kayobe overcloud provision

The controller VM is now accessible via SSH as the bootstrap user
(``cloud-user``, ``rocky`` or ``ubuntu``) at ``192.168.33.3``.

The machines and networking created by Tenks can be cleaned up via
``dev/tenks-teardown-overcloud.sh``::

    ./dev/tenks-teardown-overcloud.sh ./tenks

Upgrading
---------

It is possible to test an upgrade by running the ``dev/seed-upgrade.sh``
script::

    ./dev/seed-upgrade.sh
