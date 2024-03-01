.. _multiple-environments:

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
inventory, extra variable files, hooks, and Kolla configuration. The following
layout shows two environments called ``staging`` and ``production`` within a
single Kayobe configuration.

.. code-block:: text

   $KAYOBE_CONFIG_PATH/
   └── environments/
       ├── production/
       │   ├── hooks/
       │   │   └── overcloud-service-deploy/
       │   │       └── pre.d/
       │   │           └── 1-prep-stuff.yml
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

Naming
------

The environment name ``kayobe`` is reserved for internal use. The name should
be a valid directory name, otherwise there are no other restrictions.

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

Custom Kolla Ansible inventories
--------------------------------

Kayobe has a :ref:`feature <custom_kolla_inventory>` to pass through
additional inventories to Kolla Ansible. When using multiple environments,
these are passed though as additional inventories to Ansible. The ordering is
such that the inventory in the base layer of kayobe config overrides the
internal kayobe inventory, and inventory in the environment overrides inventory
in the base layer:

.. code-block:: bash

   ansible-playbook -i <internal kayobe inventory> -i <inventory from base layer> -i <inventory from environment>

See :ref:`custom_kolla_inventory` for more details.

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
environment. The Xena release supported combining environment-specific
and shared configuration file content for the following subset of the files:

* ``kolla/config/bifrost/bifrost.yml``
* ``kolla/config/bifrost/dib.yml``
* ``kolla/config/bifrost/servers.yml``
* ``kolla/globals.yml``
* ``kolla/kolla-build.conf``
* ``kolla/repos.yml`` or ``kolla/repos.yaml``

The Antelope release expands upon this list to add support for combining Kolla
Ansible custom service configuration. This behaviour is configured using two
variables:

* ``kolla_openstack_custom_config_include_globs``: Specifies which files are
  considered when templating the Kolla configuration. The Kayobe defaults
  are set using ``kolla_openstack_custom_config_include_globs_default``.
  An optional list of additional globs can be set using:
  ``kolla_openstack_custom_config_include_globs_extra``. These are
  combined with ``kolla_openstack_custom_config_include_globs_default``
  to produce ``kolla_openstack_custom_config_include_globs``.
  Each list entry is a dictionary with the following keys:

   * ``enabled``: Boolean which determines if this rule is used. Set to
     ``false`` to disable the rule.
   * ``glob``: String glob matching a relative path in the ``kolla/config``
     directory

   An example of such a rule:

   .. code-block:: yaml

      enabled: '{{ kolla_enable_aodh | bool }}'
      glob: aodh/**

* ``kolla_openstack_custom_config_rules``: List of rules that specify the
  strategy to use when generating a particular file. The Kayobe defaults
  are set using ``kolla_openstack_custom_config_rules_default``.
  An optional list of additional rules can be set using:
  ``kolla_openstack_custom_config_rules_extra``. These are
  combined with ``kolla_openstack_custom_config_rules_default``
  to produce ``kolla_openstack_custom_config_rules``.
  Each list entry is a dictionary with the format:

   * ``glob``: A glob matching files for this rule to match on (relative to the
     search path)
   * ``priority``: The rules are processed in increasing priority order with the
     first rule matching taking effect
   * ``strategy``: How to process the matched file. One of ``copy``,
     ``concat``, ``template``, ``merge_configs``, ``merge_yaml``
   * ``params``: Optional list of additional params to pass to module enacting
     the strategy

   An example of such a rule:

   .. code-block:: yaml

      glob: a/path/test.yml
      strategy: merge_yaml
      priority: 1000
      params:
        extend_lists: true

The Kayobe defaults fallback to using the ``template`` strategy, with a
priority of 65535. To override this behaviour configure a rule with a lower
priority e.g:

   .. code-block:: yaml

      glob: horizon/themes/**
      strategy: copy
      priority: 1000

The default INI merging strategy can be configured using:
``kolla_openstack_custom_config_ini_merge_strategy_default``. It defaults to ``concat``
for backwards compatibility. An alternative strategy is ``merge_configs`` which will
merge the two INI files so that values set in the environment take precedence over values
set in the shared files. The caveat with the ``merge_configs`` strategy is that files
must template to valid INI. This is mostly an issue when you use raw Jinja
tags, for example:

   .. code-block:: ini

      [defaults]
      {% raw %}
      {% if inventory_hostname in 'compute' %}
      foo=bar
      {% else %}
      foo=baz
      {% endif %}
      {% endraw %}

After the first round of templating by Kayobe the raw tags are stripped. This leaves:

   .. code-block:: ini

      [defaults]
      {% if inventory_hostname in 'compute' %}
      foo=bar
      {% else %}
      foo=baz
      {% endif %}

Which isn't valid INI (due to the Jinja if blocks) and cannot be merged. In most cases
the templating can be refactored:

   .. code-block:: ini

      [defaults]
      {% raw %}
      foo={{ 'bar' if inventory_hostname in 'compute' else 'baz' }}
      {% endraw %}

Alternatively, you can use Kolla host or group variables.

Disabling the default rules
^^^^^^^^^^^^^^^^^^^^^^^^^^^

There are some convenience variables to disable a subset of the
rules in ``kolla_openstack_custom_config_rules_default``:

* ``kolla_openstack_custom_config_rules_default_remove``: Allows you remove
  a rule by matching on the glob:

   .. code-block:: yaml

      kolla_openstack_custom_config_rules_default_remove:
         - "**/*.ini"

* ``kolla_openstack_custom_config_merge_configs_enabled``: Enables rules for
  matching INI files. Default is ``true``.

* ``kolla_openstack_custom_config_merge_yaml_enabled``: Enables rules for
  matching YAML files. Default is ``true``.

These allow you to more easily keep in sync with the upstream defaults. If
you had an override on ``kolla_openstack_custom_config_rules``, that
replicated most of ``kolla_openstack_custom_config_rules_default`` you'd have
to keep this in sync with the upstream kayobe defaults.

Search paths
^^^^^^^^^^^^

When merging config files the following locations are "searched" to find
files with an identical relative path:

- ``<environment-path>/kolla/config``
- ``<shared-files-path>/kolla/config``
- ``<kolla-openstack-role-path>/templates/kolla/config``

Not all strategies use all of the files when generating the kolla config.
For instance, the copy strategy will use the first file found when searching
each of the paths.

There is a feature flag: ``kolla_openstack_custom_config_environment_merging_enabled``,
that may be set to ``false`` to prevent Kayobe searching the shared files path
when merging configs. This is to replicate the legacy behaviour where the
environment Kolla custom service configuration was not merged with the base
layer. We still merge the files with Kayobe's defaults in the
``kolla-openstack`` role's internal templates.

Managing Independent Environment Files
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For files that are independent in each environment, i.e. they do not support
combining the environment-specific and shared configuration file content, there
are some techniques that may be used to avoid duplication.

For example, symbolic links can be used to share common variable definitions.
It is advised to avoid sharing credentials between environments by making each
Kolla ``passwords.yml`` file unique.

Custom Ansible Playbooks
------------------------

:doc:`Custom Ansible playbooks <custom-ansible-playbooks>`, roles and
requirements file under ``$KAYOBE_CONFIG_PATH/ansible`` are currently shared
across all environments.

Hooks
-----

Prior to the Caracal 16.0.0 release, :ref:`hooks <custom-playbooks-hooks>` were
shared across all environments.  Since Caracal it is possible to define hooks
on a per-environment basis. Hooks are collected from all environments and the
base configuration. Where multiple hooks exist with the same name, the
environment's hook takes precedence and *replaces* the other hooks. Execution
order follows the normal rules, regardless of where each hook is defined.

For example, the base configuration defines the following hooks:

* ``$KAYOBE_CONFIG_PATH/hooks/overcloud-service-deploy/pre.d/1-base.yml``
* ``$KAYOBE_CONFIG_PATH/hooks/overcloud-service-deploy/pre.d/2-both.yml``

The environment defines the following hooks:

* ``$KAYOBE_CONFIG_PATH/environments/env/hooks/overcloud-service-deploy/pre.d/2-both.yml``
* ``$KAYOBE_CONFIG_PATH/environments/env/hooks/overcloud-service-deploy/pre.d/3-env.yml``

The following hooks will execute in the order shown:

* ``$KAYOBE_CONFIG_PATH/hooks/overcloud-service-deploy/pre.d/1-base.yml``
* ``$KAYOBE_CONFIG_PATH/environments/env/hooks/overcloud-service-deploy/pre.d/2-both.yml``
* ``$KAYOBE_CONFIG_PATH/environments/env/hooks/overcloud-service-deploy/pre.d/3-env.yml``

Ansible Configuration
---------------------

Ansible configuration at ``$KAYOBE_CONFIG_PATH/ansible.cfg`` or
``$KAYOBE_CONFIG_PATH/kolla/ansible.cfg`` is currently shared across all
environments.

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

Environment Dependencies
------------------------

.. warning::

   This is an experimental feature and is still subject to change whilst
   the design is finalised.

Since the Antelope 14.0.0 release, multiple environments can be layered on top
of each of each other by declaring dependencies in a ``.kayobe-environment``
file located in the environment subdirectory. For example:

.. code-block:: yaml
   :caption: ``$KAYOBE_CONFIG_PATH/environments/environment-C/.kayobe-environment``

   dependencies:
     - environment-B

.. code-block:: yaml
   :caption: ``$KAYOBE_CONFIG_PATH/environments/environment-B/.kayobe-environment``

   dependencies:
     - environment-A

Kayobe uses a dependency resolver to order these environments into a linear
chain. Any dependency cycles in will result in an error. Using the example
above the chain would be resolved to:

.. code-block:: text

   C -> B -> A

Where C is the environment with highest precedence. Kayobe will make sure to
include the inventory and extra-vars in an order matching this chain when
running any playbooks.

Mixin environments
^^^^^^^^^^^^^^^^^^

Environment dependencies can be used to design fragments of re-useable
configuration that can be shared across multiple environments. For example:

.. code-block:: yaml
   :caption: ``$KAYOBE_CONFIG_PATH/environments/environment-A/.kayobe-environment``

   dependencies:
     - environment-mixin-1
     - environment-mixin-2
     - environment-mixin-3

In this case, each environment dependency could provide the configuration
necessary for one or more features. The mixin environments do not necessarily
need to define any dependencies between them, however Kayobe will perform a
topological sort to determine a suitable precedence. Care should be taken to
make sure that environments without an explicit ordering do not modify the same
variables.

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
