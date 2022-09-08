.. _configuration-kayobe:

====================
Kayobe Configuration
====================

This section covers configuration of Kayobe.  As an Ansible-based project,
Kayobe is for the most part configured using YAML files.

Configuration Location
======================

Kayobe configuration is by default located in ``/etc/kayobe`` on the Ansible
control host. This location can be overridden to a different location to avoid
touching the system configuration directory by setting the environment variable
``KAYOBE_CONFIG_PATH``.  Similarly, kolla configuration on the Ansible control
host will by default be located in ``/etc/kolla`` and can be overridden via
``KOLLA_CONFIG_PATH``.

Configuration Directory Layout
==============================

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
======================

Ansible's variable precedence rules are `fairly well documented
<http://docs.ansible.com/ansible/playbooks_variables.html#variable-precedence-where-should-i-put-a-variable>`_
and provide a mechanism we can use for providing site localisation and
customisation of OpenStack in combination with some reasonable default values.
For global configuration options, Kayobe typically uses the following patterns:

- Inventory group variables for the *all* group in
  ``<kayobe repo>/ansible/inventory/group_vars/all/*`` set **global defaults**.
  These files should not be modified.
- Inventory group variables for other groups in
  ``<kayobe repo>/ansible/inventory/group_vars/<group>/*`` set **defaults for
  some subsets of hosts**.  These files should not be modified.
- Extra-vars files in ``${KAYOBE_CONFIG_PATH}/*.yml`` set **custom values
  for global variables** and should be used to apply global site localisation
  and customisation.  By default these variables are commented out.

Additionally, variables can be set on a per-group or per-host basis using
inventory group or host variables files in
``${KAYOBE_CONFIG_PATH}/inventory/group_vars/*`` or
``${KAYOBE_CONFIG_PATH}/inventory/host_vars/*`` respectively.  It should be
noted that variables set in extra-vars files take precedence over per-host
variables.

.. _configuring-kayobe:

Configuring Kayobe
==================

The `kayobe-config <https://opendev.org/openstack/kayobe-config>`_ git
repository contains a Kayobe configuration directory structure and unmodified
configuration files.  This repository can be used as a mechanism for version
controlling Kayobe configuration.  As Kayobe is updated, the configuration
should be merged to incorporate any upstream changes with local modifications.

Alternatively, the baseline Kayobe configuration may be copied from a checkout
of the Kayobe repository to the Kayobe configuration path::

    $ mkdir -p ${KAYOBE_CONFIG_PATH:-/etc/kayobe/}
    $ cp -r etc/kayobe/* ${KAYOBE_CONFIG_PATH:-/etc/kayobe/}

Once in place, each of the YAML and inventory files should be manually
inspected and configured as required.

Inventory
----------

The inventory should contain the following hosts:

Ansible Control host
    This should be localhost.
Seed hypervisor
    If provisioning a seed VM, a host should exist for the hypervisor that
    will run the VM, and should be a member of the ``seed-hypervisor`` group.
Seed
    The seed host, whether provisioned as a VM by Kayobe or externally managed,
    should exist in the ``seed`` group.

Cloud hosts and bare metal compute hosts are not required to exist in the
inventory if discovery of the control plane hardware is planned, although
entries for groups may still be required.

Use of advanced control planes with multiple server roles and customised
service placement across those servers is covered in
:ref:`control-plane-service-placement`.

Site Localisation and Customisation
-----------------------------------

Site localisation and customisation is applied using Ansible extra-vars files
in ``${KAYOBE_CONFIG_PATH}/*.yml``.

.. _configuration-kayobe-ansible:

Configuration of Ansible
------------------------

Ansible configuration is described in detail in the `Ansible documentation
<https://docs.ansible.com/ansible/latest/reference_appendices/config.html>`__.
In addition to the standard locations, Kayobe supports using an Ansible
configuration file located in the Kayobe configuration at
``${KAYOBE_CONFIG_PATH}/ansible.cfg``. Note that if the ``ANSIBLE_CONFIG``
environment variable is specified it takes precedence over this file.

Encryption of Secrets
---------------------

Kayobe supports the use of `Ansible vault
<http://docs.ansible.com/ansible/playbooks_vault.html>`_ to encrypt sensitive
information in its configuration.  The ``ansible-vault`` tool should be used to
manage individual files for which encryption is required.  Any of the
configuration files may be encrypted.  Since encryption can make working with
Kayobe difficult, it is recommended to follow `best practice
<http://docs.ansible.com/ansible/playbooks_best_practices.html#best-practices-for-variables-and-vaults>`_,
adding a layer of indirection and using encryption only where necessary.

Location of data files
----------------------

Kayobe needs to know where to find any files not contained within its python package;
this includes its Ansible playbooks and any other files it needs for runtime operation.
These files are known collectively as 'data files'.

Kayobe will attempt to detect the location of its data files automatically. However, if
you have installed kayobe to a non-standard location this auto-detection may fail.
It is possible to manually override the path using the environment variable:
``KAYOBE_DATA_FILES_PATH``. This should be set to a path with the following structure::

    requirements.yml
    ansible/
        roles/
            ...
        ...

Where ``ansible`` is the ``ansible`` directory from the source checkout and ``...``
is an elided representation of any files and subdirectories contained within
that directory.
