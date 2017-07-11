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

    (kayobe-venv) $ kayobe overcloud service reconfigure

In case not all services' configuration have been modified, performance can be
improved by specifying Ansible tags to limit the tasks run in kayobe and/or
kolla-ansible's playbooks.  This may require knowledge of the inner workings of
these tools but in general, kolla-ansible tags the play used to configure each
service by the name of that service.  For example: ``nova``, ``neutron`` or
``ironic``.  Use ``-t`` or ``--tags`` to specify kayobe tags and ``-kt`` or
``--kolla-tags`` to specify kolla-ansible tags.  For example::

    (kayobe-venv) $ kayobe overcloud service reconfigure --tags config --kolla-tags nova,ironic

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

    (kayobe-venv) $ kayobe overcloud service upgrade

As for the reconfiguration command, it is possible to specify tags for Kayobe
and/or kolla-ansible::

    (kayobe-venv) $ kayobe overcloud service upgrade --tags config --kolla-tags keystone

Destroying the Overcloud Services
=================================

.. note::

   This step will destroy all containers, container images, volumes and data on
   the overcloud hosts.

To destroy the overcloud services::

    (kayobe-venv) $ kayobe overcloud service destroy --yes-i-really-really-mean-it

Deprovisioning The Cloud
========================

.. note::

   This step will power down the overcloud hosts and delete their nodes'
   instance state from the seed's ironic service.

To deprovision the overcloud::

    (kayobe-venv) $ kayobe overcloud deprovision

Running Kayobe Playbooks on Demand
==================================

In some situations it may be necessary to run an individual Kayobe playbook.
Playbooks are stored in ``<kayobe repo>/ansible/*.yml``.  To run an arbitrary
Kayobe playbook::

    (kayobe-venv) $ kayobe playbook run <playbook> [<playbook>]

Running Kolla-ansible Commands
==============================

To execute a kolla-ansible command::

    (kayobe-venv) $ kayobe kolla ansible run <command>

Dumping Kayobe Configuration
============================

The Ansible configuration space is quite large, and it can be hard to determine
the final values of Ansible variables.  We can use Kayobe's
``configuration dump`` command to view individual variables or the variables
for one or more hosts.  To dump Kayobe configuration for one or more hosts::

    (kayobe-venv) $ kayobe configuration dump

The output is a JSON-formatted object mapping hosts to their hostvars.

We can use the ``--var-name`` argument to inspect a particular variable or the
``--host`` or ``--hosts`` arguments to view a variable or variables for a
specific host or set of hosts.
