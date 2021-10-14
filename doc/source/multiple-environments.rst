=====================
Multiple Environments
=====================

.. warning::

    Support for multiple Kayobe environments is considered experimental: its
    design may change in future versions without a deprecation period.

Sometimes it can be useful to support deployment of multiple environments from
a single Kayobe configuration. Most commonly this is to support a deployment
pipeline, such as the traditional development, test, staging and production
combination. Since the Wallaby release, it is possible to include multiple
environments within a single Kayobe configuration, each providing its own
Ansible inventory and variables. This section describes how to use multiple
environments with Kayobe.

Defining Kayobe Environments
============================

By default, a Kayobe configuration directory contains a single environment,
represented by the Ansible inventory located at
``$KAYOBE_CONFIG_PATH/inventory``, extra variables files
(``$KAYOBE_CONFIG_PATH/*.yml``), custom Ansible playbooks and hooks, and Kolla
configuration.

Supporting multiple environments is done through a
``$KAYOBE_CONFIG_PATH/environments`` directory, under which each directory
represents a different environment.  Each environment contains its own Ansible
inventory, extra variable files, and Kolla configuration. The following layout
shows two environments called ``staging`` and ``production`` within a single
Kayobe configuration.

.. code-block:: text

   $KAYOBE_CONFIG_PATH/
   └── environments/
       ├── production/
       │   ├── inventory/
       │   │   ├── groups
       │   │   ├── group_vars/
       │   │   ├── hosts
       │   │   ├── host_vars/
       │   │   └── overcloud
       │   ├── kolla/
       │   │   ├── config/
       │   │   ├── globals.yml
       │   │   └── passwords.yml
       │   ├── network-allocation.yml
       │   ├── networks.yml
       │   └── overcloud.yml
       └── staging/
           ├── inventory/
           │   ├── groups
           │   ├── group_vars/
           │   ├── hosts
           │   ├── host_vars/
           │   └── overcloud
           ├── kolla/
           │   ├── config/
           │   ├── globals.yml
           │   └── passwords.yml
           ├── network-allocation.yml
           ├── networks.yml
           └── overcloud.yml

Ansible Inventories
-------------------

Each environment can include its own inventory, which overrides any variable
declaration done in the shared inventory. Typically, a shared inventory may be
used to define groups and group variables, while hosts and host variables would
be set in environment inventories. The following layout (ignoring non-inventory
files) shows an example of multiple inventories.

.. code-block:: text

   $KAYOBE_CONFIG_PATH/
   ├── environments/
   │   ├── production/
   │   │   ├── inventory/
   │   │   │   ├── hosts
   │   │   │   ├── host_vars/
   │   │   │   └── overcloud
   │   └── staging/
   │       ├── inventory/
   │       │   ├── hosts
   │       │   ├── host_vars/
   │       │   └── overcloud
   └── inventory/
       ├── groups
       └── group_vars/

Shared Extra Variables Files
----------------------------

All of the extra variables files in the Kayobe configuration directory
(``$KAYOBE_CONFIG_PATH/*.yml``) are shared between all environments. Each
environment can override these extra variables through environment-specific
extra variables files
(``$KAYOBE_CONFIG_PATH/environments/<environment>/*.yml``).

This means that all configuration in shared extra variable files must apply to
all environments. Where configuration differs between environments, move the
configuration to extra variables files under each environment.

For example, to add environment-specific DNS configuration for variables in
``dns.yml``, set these variables in
``$KAYOBE_CONFIG_PATH/environments/<environment>/dns.yml``:

.. code-block:: text

   $KAYOBE_CONFIG_PATH/
   ├── dns.yml
   └── environments/
       ├── production/
       │   ├── dns.yml
       └── staging/
           └── dns.yml

Network Configuration
^^^^^^^^^^^^^^^^^^^^^

Networking is an area in which configuration is typically specific to an
environment. There are two main global configuration files that need to be
considered: ``networks.yml`` and ``network-allocation.yml``.

Move the environment-specific parts of this configuration to
environment-specific extra variables files:

* ``networks.yml`` -> ``$KAYOBE_CONFIG_PATH/environments/<environment>/networks.yml``
* ``network-allocation.yml`` -> ``$KAYOBE_CONFIG_PATH/environments/<environment>/network-allocation.yml``

Other network configuration that may differ between environments includes:

* DNS (``dns.yml``)
* network interface names, which may be set via group variables in environment
  inventories

Other Configuration
^^^^^^^^^^^^^^^^^^^

Typically it is necessary to customise ``overcloud_group_hosts_map`` in each
environment. This is done via the ``overcloud.yml`` file documented in
:ref:`control-plane-service-placement`.

When using baremetal compute nodes, allocation of TCP ports for serial console
functionality is typically specific to an environment
(``console-allocation.yml``). This file is automatically managed by Kayobe,
like the ``network-allocation.yml`` file.

Kolla Configuration
-------------------

In the Wallaby release, Kolla configuration was independent in each
environment.

As of the Xena release, the following files support combining the
environment-specific and shared configuration file content:

* ``kolla/config/bifrost/bifrost.yml``
* ``kolla/config/bifrost/dib.yml``
* ``kolla/config/bifrost/servers.yml``
* ``kolla/globals.yml``
* ``kolla/kolla-build.conf``

Options in the environment-specific files take precedence over those in the
shared files.

Managing Independent Environment Files
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For files that are independent in each environment, i.e. they do not support
combining the environment-specific and shared configuration file content, there
are some techniques that may be used to avoid duplication.

For example, symbolic links can be used to share common variable definitions.
It is advised to avoid sharing credentials between environments by making each
Kolla ``passwords.yml`` file unique.

Custom Ansible Playbooks and Hooks
----------------------------------

The following files and directories are currently shared across all
environments:

* Ansible playbooks, roles and requirements file under
  ``$KAYOBE_CONFIG_PATH/ansible``
* Ansible configuration at ``$KAYOBE_CONFIG_PATH/ansible.cfg`` and
  ``$KAYOBE_CONFIG_PATH/kolla/ansible.cfg``
* Hooks under ``$KAYOBE_CONFIG_PATH/hooks``

Dynamic Variable Definitions
----------------------------

It may be beneficial to define variables in a file shared by multiple
environments, but still set variables to different values based on the
environment. The Kayobe environment in use can be retrieved within Ansible via
the ``kayobe_environment`` variable. For example, some variables from
``$KAYOBE_CONFIG_PATH/networks.yml`` could be shared in the following way:

.. code-block:: yaml
   :caption: ``$KAYOBE_CONFIG_PATH/networks.yml``

   external_net_fqdn: "{{ kayobe_environment }}-api.example.com"

This would configure the external FQDN for the staging environment at
``staging-api.example.com``, while the production external FQDN would be at
``production-api.example.com``.

Final Considerations
--------------------

While it's clearly desirable to keep staging functionally as close to
production, this is not always possible due to resource constraints and other
factors. Test and development environments can deviate further, perhaps only
providing a subset of the functionality available in production, in a
substantially different environment. In these cases it will clearly be
necessary to use environment-specific configuration in a number of files. We
can't cover all the cases here, but hopefully we've provided a set of
techniques that can be used.

Using Kayobe Environments
=========================

Once environments are defined, Kayobe can be instructed to manage them with the
``$KAYOBE_ENVIRONMENT`` environment variable or the ``--environment``
command-line argument:

.. code-block:: console

   (kayobe) $ kayobe control host bootstrap --environment staging

.. code-block:: console

   (kayobe) $ export KAYOBE_ENVIRONMENT=staging
   (kayobe) $ kayobe control host bootstrap

The ``kayobe-env`` environment file in ``kayobe-config`` can also take an
``--environment`` argument, which exports the ``KAYOBE_ENVIRONMENT``
environment variable.

.. code-block:: console

   (kayobe) $ source kayobe-env --environment staging
   (kayobe) $ kayobe control host bootstrap

Finally, an environment name can be specified under
``$KAYOBE_CONFIG_ROOT/.environment``, which will be used by the ``kayobe-env``
script if no ``--environment`` argument is used. This is particularly useful
when using a separate branch for each environment.

.. code-block:: console

   (kayobe) $ echo "staging" > .environment
   (kayobe) $ source kayobe-env
   (kayobe) $ kayobe control host bootstrap

.. warning::

   The locations of the Kolla Ansible source code and Python virtual
   environment remain the same for all environments when using the
   ``kayobe-env`` file. When using the same control host to manage multiple
   environments with different versions of Kolla Ansible, clone the Kayobe
   configuration in different locations, so that Kolla Ansible source
   repositories and Python virtual environments will not conflict with each
   other. The generated Kolla Ansible configuration is also shared: Kayobe will
   store the name of the active environment under
   ``$KOLLA_CONFIG_PATH/.environment`` and produce a warning if a conflict is
   detected.

Migrating to Kayobe Environments
================================

Kayobe users already managing multiple environments will already have multiple
Kayobe configurations, whether in separate repositories or in different
branches of the same repository. Kayobe provides the ``kayobe environment
create`` command to help migrating to a common repository and branch with
multiple environments. For example, the following commands will create two new
environments for production and staging based on existing Kayobe
configurations.

.. code-block:: console

   (kayobe) $ kayobe environment create --source-config-path ~/kayobe-config-prod/etc/kayobe \
                  --environment production
   (kayobe) $ kayobe environment create --source-config-path ~/kayobe-config-staging/etc/kayobe \
                  --environment staging

This command recursively copies files and directories (except the
``environments`` directory if one exists) under the existing configuration to a
new environment. Merging shared configuration must be done manually.
