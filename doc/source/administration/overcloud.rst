========================
Overcloud Administration
========================

Updating Packages
=================

It is possible to update packages on the overcloud hosts.

Package Repositories
--------------------

If using custom DNF package repositories on CentOS or Rocky, it may be
necessary to update these prior to running a package update. To do this, update
the configuration in ``${KAYOBE_CONFIG_PATH}/dnf.yml`` and run the following
command::

    (kayobe) $ kayobe overcloud host configure --tags dnf --kolla-tags none

Package Update
--------------

To update one or more packages::

    (kayobe) $ kayobe overcloud host package update --packages <package1>,<package2>

To update all eligible packages, use ``*``, escaping if necessary::

    (kayobe) $ kayobe overcloud host package update --packages "*"

To only install updates that have been marked security related::

    (kayobe) $ kayobe overcloud host package update --packages "*" --security

Note that these commands do not affect packages installed in containers, only
those installed on the host.

Kernel Updates
--------------

If the kernel has been updated, you will probably want to reboot the hosts to
boot into the new kernel. This can be done using a command such as the
following::

    (kayobe) $ kayobe overcloud host command run --command "shutdown -r" --become

It is normally best to apply this to control plane hosts in batches to avoid
clustered services from losing quorum. This can be achieved using the
``--limit`` argument, and ensuring services are fully up after rebooting before
proceeding with the next batch.

Running Commands
================

It is possible to run a command on the overcloud hosts::

    (kayobe) $ kayobe overcloud host command run --command "<command>"

For example::

    (kayobe) $ kayobe overcloud host command run --command "service docker restart"

To execute the command with root privileges, add the ``--become`` argument.
Adding the ``--verbose`` argument allows the output of the command to be seen.

Provisioning Hosts Without Kolla Services
==========================================

Sometimes it may be necessary to provision hosts that are not included in the
Kolla Ansible inventory - for example, external storage nodes such as Lustre
fileservers, or other infrastructure nodes that require network configuration
and system setup but should not run OpenStack services.

By default, hosts in groups mapped by ``kolla_overcloud_inventory_top_level_group_map``
are automatically included in the Kolla Ansible inventory. To exclude a group of
hosts from the Kolla Ansible inventory, do not map that group in
``kolla_overcloud_inventory_top_level_group_map``.

When a group is excluded from the Kolla Ansible inventory, the following
variables are not required for hosts in that group:

- ``kolla_internal_vip_address``
- ``kolla_internal_fqdn``
- ``kolla_network_interface``
- ``kolla_api_interface``

The hosts can still be provisioned and configured via Kayobe playbooks, allowing
you to use Kayobe for complete infrastructure provisioning while selectively
excluding certain hosts from Kolla Ansible deployments.

Example: Provision an external storage group
----------------------------------------------

If you are using bifrost, follow the regular process to enroll the servers.
Configure ``overcloud_group_hosts_map`` to map the hosts into an appropriate
group:

.. code-block:: yaml
   :caption: ``$KAYOBE_CONFIG_PATH/overcloud.yml``

   overcloud_group_hosts_map:
     lustre-servers:
       - lustre-server-01
       - lustre-server-02

These hosts must also be configured to be members of the ``overcloud`` group:

.. code-block:: ini
   :caption: ``$KAYOBE_CONFIG_PATH/inventory/groups``

   # Empty group declaration. kayobe overcloud inventory discover will
   # populate this group from bifrost inventory.
   [lustre-servers]

   # The hosts must be members of the overcloud group
   [overcloud:children]
   lustre-servers

You can then run  ``kayobe overcloud inventory discover`` to automatically
populate the ``lustre-servers`` group.

Alternatively, you can provision these hosts by some other means: either
manually or by using an alternative provisioning tool. You would then manually
add these to your inventory.

.. code-block:: ini
   :caption: ``$KAYOBE_CONFIG_PATH/inventory/groups``

   # This example demonstrates how you can add hosts that are not provisioned
   # by bifrost e.g deployed by some external provisioning tool.

   [lustre-servers]
   lustre-server-01
   lustre-server-02

   # The hosts must be members of the overcloud group
   [overcloud:children]
   lustre-servers

Ensuring that the IPs used to access these servers are correctly set in
``network-allocations.yml``.

Ensure the hosts are not mapped through to the kolla inventory:

  .. code-block:: yaml
   :caption: ``$KAYOBE_CONFIG_PATH/kolla.yml``

   # Define the Kolla group mapping without including lustre-servers
   kolla_overcloud_inventory_top_level_group_map:
     control:
       groups:
         - controllers
     network:
       groups:
         - network
     compute:
       groups:
         - compute
     compute-vgpu:
       groups:
         - compute-vgpu
     monitoring:
       groups:
         - monitoring
     storage:
       groups:
         - storage
     # lustre-servers group is intentionally not mapped

The hosts can then be configured using::

    (kayobe) $ kayobe overcloud host configure --limit lustre-servers

This will apply host configuration and network setup. ``kayobe overcloud service
deploy`` will be a no-op for these hosts as they will not be mapped to the
Kolla Ansible inventory.

.. _overcloud-administration-reconfigure:

Reconfiguring Containerised Services
====================================

When configuration is changed, it is necessary to apply these changes across
the system in an automated manner.  To reconfigure the overcloud, first make
any changes required to the configuration on the Ansible control host.  Next,
run the following command::

    (kayobe) $ kayobe overcloud service reconfigure

In case not all services' configuration have been modified, performance can be
improved by specifying Ansible tags to limit the tasks run in kayobe and/or
kolla-ansible's playbooks.  This may require knowledge of the inner workings of
these tools but in general, kolla-ansible tags the play used to configure each
service by the name of that service.  For example: ``nova``, ``neutron`` or
``ironic``.  Use ``-t`` or ``--tags`` to specify kayobe tags and ``-kt`` or
``--kolla-tags`` to specify kolla-ansible tags.  For example::

    (kayobe) $ kayobe overcloud service reconfigure --tags config --kolla-tags nova,ironic

Deploying Updated Container Images
==================================

A common task is to deploy updated container images, without configuration
changes. This might be to roll out an updated container OS or to pick up some
package updates. This should be faster than a full deployment or
reconfiguration.

To deploy updated container images::

    (kayobe) $ kayobe overcloud service deploy containers

Note that if there are configuration changes, these will not be applied using
this command so if in doubt, use a normal ``kayobe overcloud service deploy``.

In case not all services' containers have been modified, performance can be
improved by specifying Ansible tags to limit the tasks run in kayobe and/or
kolla-ansible's playbooks.  This may require knowledge of the inner workings of
these tools but in general, kolla-ansible tags the play used to configure each
service by the name of that service.  For example: ``nova``, ``neutron`` or
``ironic``.  Use ``-t`` or ``--tags`` to specify kayobe tags and ``-kt`` or
``--kolla-tags`` to specify kolla-ansible tags.  For example::

    (kayobe) $ kayobe overcloud service deploy containers --kolla-tags nova,ironic

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

Running Prechecks
=================

Sometimes it may be useful to run prechecks without deploying services::

    (kayobe) $ kayobe overcloud service prechecks

As for other similar commands, it is possible to specify tags for Kayobe and/or
kolla-ansible::

    (kayobe) $ kayobe overcloud service upgrade --tags config --kolla-tags keystone

Stopping the Overcloud Services
===============================

.. note::

   This step will stop all containers on the overcloud hosts.

To stop the overcloud services::

    (kayobe) $ kayobe overcloud service stop --yes-i-really-really-mean-it

It should be noted that this state is persistent - containers will remain
stopped after a reboot of the host on which they are running.

It is possible to limit the operation to particular hosts via
``--kolla-limit``, or to particular services via ``--kolla-tags``.  It is also
possible to avoid stopping the common containers via ``--kolla-skip-tags
common``. For example:

    (kayobe) $ kayobe overcloud service stop --kolla-tags glance,nova --kolla-skip-tags common

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
   instance state from the seed's ironic service. This command will print a
   list of hosts which will be deprovisioned, you must type ``yes`` to confirm.
   To automatically confirm, pass the arguments ``-e confirm_deprovision=yes``.

To deprovision the overcloud::

    (kayobe) $ kayobe overcloud deprovision

Saving Overcloud Service Configuration
======================================

It is often useful to be able to save the configuration of the control
plane services for inspection or comparison with another configuration set
prior to a reconfiguration or upgrade. This command will gather and save the
control plane configuration for all hosts to the Ansible control host::

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
followed by ``kayobe overcloud service configuration save`` to gather the
generated configuration to the Ansible control host.

Validating Overcloud Service Configuration
==========================================

Issues can arise in Kolla Ansible deployments when incorrect options are used
in configuration files. This is because OpenStack services will ignore unknown
options. It is also important to keep on top of deprecated options that may be
removed in the future. The ``oslo-config-validator`` can be used to check both
of these. This command will run it on the OpenStack control plane services::

    (kayobe) $ kayobe overcloud service configuration validate --output-dir /path/to/save/results

Performing Database Backups
===========================

Database backups can be performed using the underlying support in Kolla
Ansible.

In order to enable backups, enable Mariabackup in
``${KAYOBE_CONFIG_PATH}/kolla.yml``:

.. code-block:: console

   kolla_enable_mariabackup: true

To apply this change, use the :ref:`kayobe overcloud service reconfigure
<overcloud-administration-reconfigure>` command.

To perform a full backup, run the following command:

.. code-block:: console

   kayobe overcloud database backup

Or to perform an incremental backup, run the following command:

.. code-block:: console

   kayobe overcloud database backup --incremental

Further information on backing up and restoring the database is available in
the :kolla-ansible-doc:`Kolla Ansible documentation
<admin/mariadb-backup-and-restore.html>`.

Performing Database Recovery
============================

Recover a completely stopped MariaDB cluster using the underlying support in
Kolla Ansible.

To perform recovery run the following command:

.. code-block:: console

   kayobe overcloud database recover

Or to perform recovery on specified host, run the following command:

.. code-block:: console

   kayobe overcloud database recover --force-recovery-host <host>

By default the underlying kolla-ansible will automatically determine which
host to use, and this option should not be used.

Gathering Facts
===============

The following command may be used to gather facts for all overcloud hosts, for
both Kayobe and Kolla Ansible:

.. code-block:: console

   kayobe overcloud facts gather

This may be useful to populate a fact cache in advance of other operations.
