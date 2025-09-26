===================
Seed Administration
===================

Deprovisioning The Seed VM
==========================

.. note::

   This step will destroy the seed VM and its data volumes.

To deprovision the seed VM::

    (kayobe) $ kayobe seed vm deprovision

Destroying all services on the seed
===================================

.. warning::

   This step will destroy all containers, container images, and volumes that were deployed by
   Kayobe and Kolla. To destroy volumes and images associated with
   :ref:`custom containers <configuration-seed-custom-containers>`, you must configure the
   ``post_destroy`` and ``pre_destroy`` hooks to do the clean up manually as Kayobe will not
   automatically clean these up. It is generally only advised to run this command when
   you have no important data on the system.

To destroy the seed services::

    (kayobe) $ kayobe seed service destroy --yes-i-really-really-mean-it

This can optionally be used with a tag::

    (kayobe) $ kayobe seed service destroy --yes-i-really-really-mean-it -kt none -t docker-registry

Care must be taken to set both kayobe and kolla tags to avoid accidentally
destroying other services.

Updating Packages
=================

It is possible to update packages on the seed host.

Package Repositories
--------------------

If using custom DNF package repositories on CentOS or Rocky, it may be
necessary to update these prior to running a package update. To do this, update
the configuration in ``${KAYOBE_CONFIG_PATH}/dnf.yml`` and run the following
command::

    (kayobe) $ kayobe seed host configure --tags dnf --kolla-tags none

Package Update
--------------

To update one or more packages::

    (kayobe) $ kayobe seed host package update --packages <package1>,<package2>

To update all eligible packages, use ``*``, escaping if necessary::

    (kayobe) $ kayobe seed host package update --packages "*"

To only install updates that have been marked security related::

    (kayobe) $ kayobe seed host package update --packages "*" --security

Note that these commands do not affect packages installed in containers, only
those installed on the host.

Packages can also be updated on the seed hypervisor host, if one is in use::

    (kayobe) $ kayobe seed hypervisor package update --packages <package1>,<package2>

Kernel Updates
--------------

If the kernel has been updated, you will probably want to reboot the seed host
to boot into the new kernel. This can be done using a command such as the
following::

    (kayobe) $ kayobe seed host command run --command "shutdown -r" --become

Examining the Bifrost Container
===============================

The seed host runs various services required for a standalone Ironic
deployment. These all run in a single ``bifrost_deploy`` container.

It can often be helpful to execute a shell in the bifrost container for
diagnosing operational issues:

.. note::

   Examples show the commands when using Docker as the container engine. If
   using Podman, simply change ``docker`` for ``sudo podman`` in the command.

.. code-block:: console

   $ docker exec -it bifrost_deploy bash

Services are run via Systemd::

    (bifrost_deploy) systemctl

Logs are stored in ``/var/log/kolla/``, which is mounted to the ``kolla_logs``
Docker volume.

Accessing the Seed Services
===========================

The Ironic and Ironic inspector APIs can be accessed via the ``baremetal``
command line interface::

    (bifrost_deploy) $ export OS_CLOUD=bifrost
    (bifrost_deploy) $ baremetal node list
    (bifrost_deploy) $ baremetal introspection list

Backup & Restore
================

There are two main approaches to backing up and restoring data on the seed.  A
backup may be taken of the Ironic databases. Alternatively, a Virtual Machine
backup may be used if running the seed services in a VM.  The former will
consume less storage. Virtual Machine backups are not yet covered here, neither
is scheduling of backups. Any backup and restore procedure should be tested in
advance.

Database Backup & Restore
-------------------------

A backup may be taken of the database, using one of the many tools that exist
for backing up MariaDB databases.

A simple approach that should work for the typically modestly sized seed
database is ``mysqldump``.  The following commands should all be executed on
the seed.

Backup
^^^^^^

.. note::

    Examples show the commands when using Docker as the container engine. If using
    Podman, simply change ``docker`` for ``sudo podman`` in the command.

It should be safe to keep services running during the backup, but for maximum
safety they may optionally be stopped::

    docker exec -it bifrost_deploy systemctl stop ironic ironic-inspector

Then, to perform the backup::

    docker exec -it bifrost_deploy \
    mysqldump --all-databases --single-transaction --routines --triggers > seed-backup.sql

If the services were stopped prior to the backup, start them again::

    docker exec -it bifrost_deploy systemctl start ironic ironic-inspector

Restore
^^^^^^^

.. note::

   Examples show the commands when using Docker as the container engine. If using
   Podman, simply change ``docker`` for ``sudo podman`` in the command.

Prior to restoring the database, the Ironic and Ironic Inspector services
should be stopped::

    docker exec -it bifrost_deploy systemctl stop ironic ironic-inspector

The database may then safely be restored::

    docker exec -i bifrost_deploy \
    mysql < seed-backup.sql

Finally, start the Ironic and Ironic Inspector services again::

    docker exec -it bifrost_deploy systemctl start ironic ironic-inspector

Running Commands
================

It is possible to run a command on the seed host::

    (kayobe) $ kayobe seed host command run --command "<command>"

For example::

    (kayobe) $ kayobe seed host command run --command "service docker restart"

Commands can also be run on the seed hypervisor host, if one is in use::

    (kayobe) $ kayobe seed hypervisor host command run --command "<command>"

To execute the command with root privileges, add the ``--become`` argument.
Adding the ``--verbose`` argument allows the output of the command to be seen.
