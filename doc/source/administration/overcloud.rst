========================
Overcloud Administration
========================

Updating Packages
=================

It is possible to update packages on the overcloud hosts. To update one or more
packages::

    (kayobe) $ kayobe overcloud host package update --packages <package1>,<package2>

To update all eligible packages, use ``*``, escaping if necessary::

    (kayobe) $ kayobe overcloud host package update --packages *

To only install updates that have been marked security related::

    (kayobe) $ kayobe overcloud host package update --packages <packages> --security

Note that these commands do not affect packages installed in containers, only
those installed on the host.

Running Commands
================

It is possible to run a command on the overcloud hosts::

    (kayobe) $ kayobe overcloud host command run --command "<command>"

For example::

    (kayobe) $ kayobe overcloud host command run --command "service docker restart"

To execute the command with root privileges, add the ``--become`` argument.
Adding the ``--verbose`` argument allows the output of the command to be seen.

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
followed by ``kayobe ovecloud service configuration save`` to gather the
generated configuration to the Ansible control host.
