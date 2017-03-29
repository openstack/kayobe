=====
Usage
=====

This section describes usage of Kayobe to install an OpenStack cloud onto a set
of bare metal servers.  We assume access is available to a node which will act
as the hypervisor hosting the seed node in a VM.  We also assume that this seed
hypervisor has access to the bare metal nodes that will form the OpenStack
control plane.  Finally, we assume that the control plane nodes have access to
the bare metal nodes that will form the workload node pool.

Configuration
=============

As an Ansible-based project, Kayobe is for the most part configured using YAML
files.

Configuration Location
----------------------

Kayobe configuration is by default located in ``/etc/kayobe`` on the Ansible
control host. This location can be overridden to a different location to avoid
touching the system configuration directory by setting the environment variable
``KAYOBE_CONFIG_PATH``.  Similarly, kolla configuration on the Ansible control
host will by default be located in ``/etc/kolla`` and can be overridden via
``KOLLA_CONFIG_PATH``.

Configuration Directory Layout
------------------------------

The Kayobe configuration directory contains Ansible ``extra-vars`` files and
the Ansible inventory.  An example of the directory structure is as follows::

    extra-vars1.yml
    extra-vars2.yml
    inventory/
        group_vars/
            group1-vars
            group2-vars
        groups
        host_vars/
            host1-vars
            host2-vars
        hosts

Configuration Patterns
----------------------

Ansible's variable precedence rules are `fairly well documented
<http://docs.ansible.com/ansible/playbooks_variables.html#variable-precedence-where-should-i-put-a-variable>`_
and provide a mechanism we can use for providing site localisation and
customisation of OpenStack in combination with some reasonable default values.
For global configuration options, Kayobe typically uses the following patterns:

- Playbook group variables for the *all* group in
  ``<kayobe repo>/ansible/group_vars/all/*`` set **global defaults**.  These
  files should not be modified.
- Playbook group variables for other groups in
  ``<kayobe repo>/ansible/group_vars/<group>/*`` set **defaults for some subsets
  of hosts**.  These files should not be modified.
- Extra-vars files in ``${KAYOBE_CONFIG_PATH}/*.yml`` set **custom values
  for global variables** and should be used to apply global site localisation
  and customisation.  By default these variables are commented out.

Additionally, variables can be set on a per-host basis using inventory host
variables files in ``${KAYOBE_CONFIG_PATH}/inventory/host_vars/*``.  It should
be noted that variables set in extra-vars files take precedence over per-host
variables.

Configuring Kayobe
------------------

From a checkout of the Kayobe repository, the baseline Kayobe configuration
should be copied to the Kayobe configuration path::

    $ cp -r etc/ ${KAYOBE_CONFIG_PATH:-/etc/kayobe}

Once in place, each of the YAML and inventory files should be manually
inspected and configured as required.

Inventory
^^^^^^^^^

The inventory should contain the following hosts:

Control host
    This should be localhost and should be a member of the ``config-mgmt``
    group.
Seed hypervisor
    If provisioning a seed VM, a host should exist for the hypervisor that
    will run the VM, and should be a member of the ``seed-hypervisor`` group.
Seed
    The seed host, whether provisioned as a VM by Kayobe or externally managed,
    should exist in the ``seed`` group.

Cloud hosts and bare metal compute hosts are not required to exist in the
inventory.

Site Localisation and Customisation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Site localisation and customisation is applied using Ansible extra-vars files
in ``${KAYOBE_CONFIG_PATH}/*.yml``.

Command Line Interface
======================

.. note::

   Where a prompt starts with ``(kayobe-venv)`` it is implied that the user has
   activated the Kayobe virtualenv. This can be done as follows::

       $ source kayobe-venv/bin/activate

   To deactivate the virtualenv::

       (kayobe-venv) $ deactivate

To see information on how to use the ``kayobe`` CLI and the commands it
provides::

    (kayobe-venv) $ kayobe help

As the ``kayobe`` CLI is based on the ``cliff`` package (as used by the
``openstack`` client), it supports tab auto-completion of subcommands.  This
can be activated by generating and then sourcing the bash completion script::

    (kayobe-venv) $ kayobe complete > kayobe-complete
    (kayobe-venv) $ source kayobe-complete

Ansible Control Host
====================

Before starting deployment we must bootstrap the Ansible control host.  Tasks
performed here include:

- Install Ansible and role dependencies from Ansible Galaxy.
- Generate an SSH key if necessary and add it to the current user's authorised
  keys.
- Configure kolla and kolla-ansible.

To bootstrap the Ansible control host::

    (kayobe-venv) $ kayobe control host bootstrap

Physical Network
================

The physical network can be managed by Kayobe, which uses Ansible's network
modules.  Currently Dell Network OS 6 and Dell Network OS 9 switches are
supported but this could easily be extended.  To provision the physical
network::

    (kayobe-venv) $ kayobe physical network configure --group <group>

The ``--group`` argument is used to specify an Ansible group containing
the switches to be configured.

Seed
====

VM Provisioning
---------------

.. note::

   It is not necesary to run the seed services in a VM.  To use an existing
   bare metal host or a VM provisioned outside of Kayobe, this step may be
   skipped.  Ensure that the Ansible inventory contains a host for the seed.

The seed hypervisor should have CentOS and ``libvirt`` installed.  It should
have ``libvirt`` networks configured for all networks that the seed VM needs
access to and a ``libvirt`` storage pool available for the seed VM's volumes.
To provision the seed VM::

    (kayobe-venv) $ kayobe seed vm provision

When this command has completed the seed VM should be active and accessible via
SSH.  Kayobe will update the Ansible inventory with the IP address of the VM.

Host Configuration
------------------

To configure the seed host OS::

    (kayobe-venv) $ kayobe seed host configure

.. note::

   If the seed host uses disks that have been in use in a previous
   installation, it may be necessary to wipe partition and LVM data from those
   disks.  To wipe all disks that are not mounted during host configuration::

       (kayobe-venv) $ kayobe seed host configure --wipe-disks

Building Container Images
-------------------------

.. note::

   It is possible to use prebuilt container images from an image registry such
   as Dockerhub.  In this case, this step can be skipped.

It is possible to use prebuilt container images from an image registry such as
Dockerhub.  In some cases it may be necessary to build images locally either to
apply local image customisation or to use a downstream version of kolla.  To
build images locally::

    (kayobe-venv) $ kayobe seed container image build

Deploying Containerised Services
--------------------------------

At this point the seed services need to be deployed on the seed VM.  These
services are deployed in the ``bifrost_deploy`` container.  This command will
also build the Operating System image that will be used to deploy the overcloud
nodes using Disk Image Builder (DIB).

To deploy the seed services in containers::

    (kayobe-venv) $ kayobe seed service deploy

After this command has completed the seed services will be active.

Accessing the Seed via SSH (Optional)
-------------------------------------

For SSH access to the seed, first determine the seed's IP address. We can
use the ``kayobe configuration dump`` command to inspect the seed's IP
address::

    (kayobe-venv) $ kayobe configuration dump --host seed --var-name ansible_host

The ``kayobe_ansible_user`` variable determines which user account will be used
by Kayobe when accessing the machine via SSH.  By default this is ``stack``.
Use this user to access the seed::

    $ ssh <kayobe ansible user>@<seed VM IP>

To see the active Docker containers::

    $ docker ps

Leave the seed VM and return to the shell on the control host::

    $ exit

Overcloud
=========

Discovery
---------

.. note::

   If discovery of the overcloud is not possible, a static inventory of servers
   using the bifrost ``servers.yml`` file format may be configured using the
   ``kolla_bifrost_servers`` variable in ``${KAYOBE_CONFIG_PATH}/bifrost.yml``.

Discovery of the overcloud is supported by the ironic inspector service running
in the ``bifrost_deploy`` container on the seed.  The service is configured to
PXE boot unrecognised MAC addresses with an IPA ramdisk for introspection.  If
an introspected node does not exist in the ironic inventory, ironic inspector
will create a new entry for it.

Discovery of the overcloud is triggered by causing the nodes to PXE boot using
a NIC attached to the overcloud provisioning network.  For many servers this
will be the factory default and can be performed by powering them on.

On completion of the discovery process, the overcloud nodes should be
registered with the ironic service running in the seed host's
``bifrost_deploy`` container.  The node inventory can be viewed by executing
the following on the seed::

    $ docker exec -it bifrost_deploy bash
    (bifrost_deploy) $ source env-vars
    (bifrost_deploy) $ ironic node-list

In order to interact with these nodes using Kayobe, run the following command
to add them to the Kayobe and bifrost Ansible inventories::

    (kayobe-venv) $ kayobe overcloud inventory discover

Provisioning
------------

Provisioning of the overcloud is performed by the ironic service running in the
bifrost container on the seed.  To provision the overcloud nodes::

    (kayobe-venv) $ kayobe overcloud provision

After this command has completed the overcloud nodes should have been
provisioned with an OS image.  The command will wait for the nodes to become
``active`` in ironic and accessible via SSH.

Host Configuration
------------------

To configure the overcloud hosts' OS::

    (kayobe-venv) $ kayobe overcloud host configure

.. note::

   If the controller hosts use disks that have been in use in a previous
   installation, it may be necessary to wipe partition and LVM data from those
   disks.  To wipe all disks that are not mounted during host configuration::

       (kayobe-venv) $ kayobe overcloud host configure --wipe-disks

Building Container Images
-------------------------

.. note::

   It is possible to use prebuilt container images from an image registry such
   as Dockerhub.  In this case, this step can be skipped.

In some cases it may be necessary to build images locally either to apply local
image customisation or to use a downstream version of kolla.  To build images
locally::

    (kayobe-venv) $ kayobe overcloud container image build

Deploying Containerised Services
--------------------------------

To deploy the overcloud services in containers::

    (kayobe-venv) $ kayobe overcloud service deploy

Once this command has completed the overcloud nodes should have OpenStack
services running in Docker containers. 

Interacting with the Control Plane
----------------------------------

Kolla-ansible writes out an environment file that can be used to access the
OpenStack services::

    $ source ${KOLLA_CONFIG_PATH:-/etc/kolla}/admin-openrc.sh

Other Useful Commands
=====================

Running Kayobe Playbooks on Demand
----------------------------------

In some situations it may be necessary to run an individual Kayobe playbook.
Playbooks are stored in ``<kayobe repo>/ansible/*.yml``.  To run an arbitrary
Kayobe playbook::

    (kayobe-venv) $ kayobe playbook run <playbook> [<playbook>]

Running Kolla-ansible Commands
------------------------------

To execute a kolla-ansible command::

    (kayobe-venv) $ kayobe kolla ansible run <command>

Dumping Kayobe Configuration
----------------------------

The Ansible configuration space is quite large, and it can be hard to determine
the final values of Ansible variables.  We can use Kayobe's
``configuration dump`` command to view individual variables or the variables
for one or more hosts.  To dump Kayobe configuration for one or more hosts::

    (kayobe-venv) $ kayobe configuration dump

The output is a JSON-formatted object mapping hosts to their hostvars.

We can use the ``--var-name`` argument to inspect a particular variable or the
``--host`` or ``--hosts`` arguments to view a variable or variables for a
specific host or set of hosts.
