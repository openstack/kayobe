======================
General Administration
======================

Updating the Control Host
=========================

There are several pieces of software and configuration that must be installed
and synchronised on the Ansible Control host:

* Kayobe configuration
* Kayobe Python package
* Ansible Galaxy roles
* Kolla Ansible Python package

A change to the configuration may require updating the Kolla Ansible Python
package. Updating the Kayobe Python package may require updating the Ansible
Galaxy roles. It's not always easy to know which of these are required, so the
simplest option is to apply all of the following steps when any of the above
are changed.

#. :ref:`Update Kayobe configuration <upgrading-kayobe-configuration>` to the
   required commit
#. :ref:`Upgrade the Kayobe Python package <upgrading-kayobe>` to the required
   version
#. :ref:`Upgrade the Ansible control host <upgrading-control-host>` to
   synchronise the Ansible Galaxy roles and Kolla Ansible Python package.

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

These checks will attempt to ping the external IP address ``8.8.8.8`` and
external hostname ``google.com``. They can be configured with the
``nc_external_ip`` and ``nc_external_hostname`` variables in
``$KAYOBE_CONFIG_PATH/networks.yml``.
