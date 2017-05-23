=============
Configuration
=============

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
==================

From a checkout of the Kayobe repository, the baseline Kayobe configuration
should be copied to the Kayobe configuration path::

    $ cp -r etc/ ${KAYOBE_CONFIG_PATH:-/etc/kayobe}

Once in place, each of the YAML and inventory files should be manually
inspected and configured as required.

Inventory
----------

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
-----------------------------------

Site localisation and customisation is applied using Ansible extra-vars files
in ``${KAYOBE_CONFIG_PATH}/*.yml``.

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
