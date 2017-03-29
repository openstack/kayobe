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

Kayobe configuration is by default located in ``/etc/kayobe`` on the Ansible
control host. This can be overridden to a different location to avoid touching
the system configuration directory by setting the environment variable
``KAYOBE_CONFIG_PATH``.  Similarly, kolla configuration on the Ansible control
host will by default be located in ``/etc/kolla`` and can be overridden via
``KOLLA_CONFIG_PATH``.

From a checkout of the Kayobe repository, the baseline Kayobe configuration
should be copied to the Kayobe configuration path::

    $ cp -r etc/ ${KAYOBE_CONFIG_PATH:-/etc/kayobe}

Once in place, each of the YAML and inventory files should be manually
inspected and configured as required.

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

Seed
====

The seed hypervisor should have CentOS and ``libvirt`` installed.  It should
have ``libvirt`` networks configured for all networks that the seed VM needs
access to and a ``libvirt`` storage pool available for the seed VM's volumes.
To provision the seed VM::

    (kayobe-venv) $ kayobe seed vm provision

When this command has completed the seed VM should be active and accessible via
SSH.  Kayobe will update the Ansible inventory with the IP address of the VM.

At this point the seed services need to be deployed on the seed VM.  These
services include Docker and the kolla ``bifrost-deploy`` container.  This
command will also build the Operating System image that will be used to deploy
the overcloud nodes using Disk Image Builder (DIB).

To configure the seed host OS::

    (kayobe-venv) $ kayobe seed host configure

.. note::

   If the seed host uses disks that have been in use in a previous
   installation, it may be necessary to wipe partition and LVM data from those
   disks.  To wipe all disks that are not mounted during host configuration::

       (kayobe-venv) $ kayobe seed host configure --wipe-disks

It is possible to use prebuilt container images from an image registry such as
Dockerhub.  In some cases it may be necessary to build images locally either to
apply local image customisation or to use a downstream version of kolla.  To
build images locally::

    (kayobe-venv) $ kayobe seed container image build

To deploy the seed services in containers::

    (kayobe-venv) $ kayobe seed service deploy

After this command has completed the seed services will be active.

Accessing the Seed via SSH
--------------------------

For SSH access to the seed VM, first determine the seed VM's IP address. We can
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

.. note::

   Automated discovery of the overcloud nodes is not currently documented.

Provisioning of the overcloud is performed by bifrost running in a container on
the seed.  A static inventory of servers may be configured using the
``kolla_bifrost_servers`` variable.  To provision the overcloud nodes::

    (kayobe-venv) $ kayobe overcloud provision

After this command has completed the overcloud nodes should have been
provisioned with an OS image.  To configure the overcloud hosts' OS::

    (kayobe-venv) $ kayobe overcloud host configure

.. note::

   If the controller hosts use disks that have been in use in a previous
   installation, it may be necessary to wipe partition and LVM data from those
   disks.  To wipe all disks that are not mounted during host configuration::

       (kayobe-venv) $ kayobe overcloud host configure --wipe-disks

It is possible to use prebuilt container images from an image registry such as
Dockerhub.  In some cases it may be necessary to build images locally either to
apply local image customisation or to use a downstream version of kolla.  To
build images locally::

    (kayobe-venv) $ kayobe overcloud container image build

To deploy the overcloud services in containers::

    (kayobe-venv) $ kayobe overcloud service deploy

Once this command has completed the overcloud nodes should have OpenStack
services running in Docker containers. Kolla-ansible writes out an environment
file that can be used to access the OpenStack services::

    $ source ${KOLLA_CONFIG_PATH:-/etc/kolla}/admin-openrc.sh

Other Useful Commands
=====================

To run an arbitrary Kayobe playbook::

    (kayobe-venv) $ kayobe playbook run <playbook> [<playbook>]

To execute a kolla-ansible command::

    (kayobe-venv) $ kayobe kolla ansible run <command>

To dump Kayobe configuration for one or more hosts::

    (kayobe-venv) $ kayobe configuration dump
