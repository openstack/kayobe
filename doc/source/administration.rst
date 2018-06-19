==============
Administration
==============

This section describes how to use kayobe to simplify post-deployment
administrative tasks.

Reconfiguring Containerised Services
====================================

When configuration is changed, it is necessary to apply these changes across
the system in an automated manner.  To reconfigure the overcloud, first make
any changes required to the configuration on the control host.  Next, run the
following command::

    (kayobe) $ kayobe overcloud service reconfigure

In case not all services' configuration have been modified, performance can be
improved by specifying Ansible tags to limit the tasks run in kayobe and/or
kolla-ansible's playbooks.  This may require knowledge of the inner workings of
these tools but in general, kolla-ansible tags the play used to configure each
service by the name of that service.  For example: ``nova``, ``neutron`` or
``ironic``.  Use ``-t`` or ``--tags`` to specify kayobe tags and ``-kt`` or
``--kolla-tags`` to specify kolla-ansible tags.  For example::

    (kayobe) $ kayobe overcloud service reconfigure --tags config --kolla-tags nova,ironic

Upgrading Containerised Services
================================

Containerised control plane services may be upgraded by replacing existing
containers with new containers using updated images which have been pulled from
a registry or built locally.  If using an updated version of Kayobe or
upgrading from one release of OpenStack to another, be sure to follow the
:ref:`kayobe upgrade guide <upgrading>`.  It may be necessary to upgrade one
or more services within a release, for example to apply a patch or minor
release.

To upgrade the containerised control plane services::

    (kayobe) $ kayobe overcloud service upgrade

As for the reconfiguration command, it is possible to specify tags for Kayobe
and/or kolla-ansible::

    (kayobe) $ kayobe overcloud service upgrade --tags config --kolla-tags keystone

Destroying the Overcloud Services
=================================

.. note::

   This step will destroy all containers, container images, volumes and data on
   the overcloud hosts.

To destroy the overcloud services::

    (kayobe) $ kayobe overcloud service destroy --yes-i-really-really-mean-it

Deprovisioning The Cloud
========================

.. note::

   This step will power down the overcloud hosts and delete their nodes'
   instance state from the seed's ironic service.

To deprovision the overcloud::

    (kayobe) $ kayobe overcloud deprovision

Deprovisioning The Seed VM
==========================

.. note::

   This step will destroy the seed VM and its data volumes.

To deprovision the seed VM::

    (kayobe) $ kayobe seed vm deprovision

Saving Overcloud Service Configuration
======================================

It is often useful to be able to save the configuration of the control
plane services for inspection or comparison with another configuration set
prior to a reconfiguration or upgrade. This command will gather and save the
control plane configuration for all hosts to the ansible control host::

    (kayobe) $ kayobe overcloud service configuration save

The default location for the saved configuration is ``$PWD/overcloud-config``,
but this can be changed via the ``output-dir`` argument. To gather
configuration from a directory other than the default ``/etc/kolla``, use the
``node-config-dir`` argument.

Generating Overcloud Service Configuration
==========================================

Prior to deploying, reconfiguring, or upgrading a control plane, it may be
useful to generate the configuration that will be applied, without actually
applying it to the running containers. The configuration should typically be
generated in a directory other than the default configuration directory of
``/etc/kolla``, to avoid overwriting the active configuration::

    (kayobe) $ kayobe overcloud service configuration generate --node-config-dir /path/to/generated/config

The configuration will be generated remotely on the overcloud hosts in the
specified directory, with one subdirectory per container. This command may be
followed by ``kayobe ovecloud service configuration save`` to gather the
generated configuration to the ansible control host.

Checking Network Connectivity
=============================

In complex networking environments it can be useful to be able to automatically
check network connectivity and diagnose networking issues.  To perform some
simple connectivity checks::

    (kayobe) $ kayobe network connectivity check

Note that this will run on the seed, seed hypervisor, and overcloud hosts. If
any of these hosts are not expected to be active (e.g. prior to overcloud
deployment), the set of target hosts may be limited using the ``--limit``
argument.

Baremetal Compute Node Management
=================================

When enrolling new hardware or performing maintenance, it can be useful to be
able to manage many bare metal compute nodes simulteneously.

In all cases, commands are delegated to one of the controller hosts, and
executed concurrently. Note that ansible's ``forks`` configuration option,
which defaults to 5, may limit the number of nodes configured concurrently.

By default these commands wait for the state transition to complete for each
node. This behavior can be changed by overriding the variable
``baremetal_compute_wait`` via ``-e baremetal_compute_wait=False``

Manage
------

A node may need to be set to the ``manageable`` provision state in order to
perform certain management operations, or when an enrolled node is
transitioned into service. In order to manage a node, it must be in one of
these states: ``enroll``, ``available``, ``cleaning``, ``clean failed``,
``adopt failed`` or ``inspect failed``. To move the baremetal compute nodes
to the ``manageable`` provision state::

    (kayobe) $ kayobe baremetal compute manage

Provide
-------

In order for nodes to be scheduled by nova, they must be ``available``. To
move the baremetal compute nodes from the ``manageable`` state to the
``available`` provision state::

    (kayobe) $ kayobe baremetal compute provide

Inspect
-------

Nodes must be in one of the following states: ``manageable``, ``inspect
failed``, or ``available``. To trigger hardware inspection on the baremetal
compute nodes::

    (kayobe) $ kayobe baremetal compute inspect

Rename
------

Once nodes have been discovered, it is helpful to associate them with a name
to make them easier to work with. If you would like the nodes to be named
according to their inventory host names, you can run the following command:

    (kayobe) $ kayobe baremetal compute rename

This command will use the ``ipmi_address`` host variable from the inventory
to map the inventory host name to the correct node.

Running Kayobe Playbooks on Demand
==================================

In some situations it may be necessary to run an individual Kayobe playbook.
Playbooks are stored in ``<kayobe repo>/ansible/*.yml``.  To run an arbitrary
Kayobe playbook::

    (kayobe) $ kayobe playbook run <playbook> [<playbook>]

Running Kolla-ansible Commands
==============================

To execute a kolla-ansible command::

    (kayobe) $ kayobe kolla ansible run <command>

Dumping Kayobe Configuration
============================

The Ansible configuration space is quite large, and it can be hard to determine
the final values of Ansible variables.  We can use Kayobe's
``configuration dump`` command to view individual variables or the variables
for one or more hosts.  To dump Kayobe configuration for one or more hosts::

    (kayobe) $ kayobe configuration dump

The output is a JSON-formatted object mapping hosts to their hostvars.

We can use the ``--var-name`` argument to inspect a particular variable or the
``--host`` or ``--hosts`` arguments to view a variable or variables for a
specific host or set of hosts.
