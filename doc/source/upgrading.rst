.. _upgrading:

=========
Upgrading
=========

This section describes how to upgrade from one OpenStack release to another.

Preparation
===========

Before you start, be sure to back up any local changes, configuration, and
data.

Upgrading Kayobe
================

If a new, suitable version of kayobe is available, it should be installed.
If using kayobe from a git checkout, this may be done by pulling down the new
version from Github.  Make sure that any local changes to kayobe are committed.
For example, to pull version 1.0.0 from the ``origin`` remote::

    $ git pull origin 1.0.0

If local changes were made to kayobe, these should now be reapplied.

The upgraded kayobe python module and dependencies should be installed::

    (kayobe) $ pip install -U .

Migrating Kayobe Configuration
------------------------------

Kayobe configuration options may be changed between releases of kayobe. Ensure
that all site local configuration is migrated to the target version format. If
using the `kayobe-config <https://github.com/openstack/kayobe-config>`_ git
repository to manage local configuration, this process can be managed via git.
For example, to fetch version 1.0.0 of the configuration from the ``origin``
remote and merge it into the current branch::

    $ git fetch origin 1.0.0
    $ git merge 1.0.0

The configuration should be manually inspected after the merge to ensure that
it is correct.  Any new configuration options may be set at this point.  In
particular, the following options may need to be changed if not using their
default values:

* ``kolla_openstack_release``
* ``kolla_sources``
* ``kolla_build_blocks``
* ``kolla_build_customizations``

Once the configuration has been migrated, it is possible to view the global
variables for all hosts::

    (kayobe) $ kayobe configuration dump

The output of this command is a JSON object mapping hosts to their
configuration.  The output of the command may be restricted using the
``--host``, ``--hosts``, ``--var-name`` and ``--dump-facts`` options.

If using the ``kayobe-env`` environment file in ``kayobe-config``, this should
also be inspected for changes and modified to suit the local ansible control
host environment if necessary. When ready, source the environment file::

    $ source kayobe-env

Upgrading the Ansible Control Host
==================================

Before starting the upgrade we must upgrade the Ansible control host.  Tasks
performed here include:

- Install updated Ansible role dependencies from Ansible Galaxy.
- Generate an SSH key if necessary and add it to the current user's authorised
  keys.

To upgrade the Ansible control host::

    (kayobe) $ kayobe control host upgrade

Upgrading the Seed Hypervisor
=============================

Currently, upgrading the seed hypervisor services is not supported.  It may
however be necessary to upgrade some host services::

    (kayobe) $ kayobe seed hypervisor host upgrade

Note that this will not perform full configuration of the host, and will
instead perform a targeted upgrade of specific services where necessary.

Upgrading the Seed
==================

Currently, upgrading the seed services is not supported.  It may however be
necessary to upgrade some host services::

    (kayobe) $ kayobe seed host upgrade

Note that this will not perform full configuration of the host, and will
instead perform a targeted upgrade of specific services where necessary.

Upgrading the Overcloud
=======================

The overcloud services are upgraded in two steps.  First, new container images
should be obtained either by building them locally or pulling them from an
image registry.  Second, the overcloud services should be replaced with new
containers created from the new container images.

Upgrading Host Services
-----------------------

Prior to upgrading the OpenStack control plane, the overcloud host services
should be upgraded::

    (kayobe) $ kayobe overcloud host upgrade

Note that this will not perform full configuration of the host, and will
instead perform a targeted upgrade of specific services where necessary.

.. _building_ironic_deployment_images:

Building Ironic Deployment Images
---------------------------------

.. note::

   It is possible to use prebuilt deployment images. In this case, this step
   can be skipped.

It is possible to use prebuilt deployment images from the `OpenStack hosted
tarballs <https://tarballs.openstack.org/ironic-python-agent>`_ or another
source.  In some cases it may be necessary to build images locally either to
apply local image customisation or to use a downstream version of Ironic Python
Agent (IPA).  In order to build IPA images, the ``ipa_build_images`` variable
should be set to ``True``.  To build images locally::

    (kayobe) $ kayobe overcloud deployment image build

Upgrading Ironic Deployment Images
----------------------------------

Prior to upgrading the OpenStack control plane you should upgrade
the deployment images. If you are using prebuilt images, update
``ipa_kernel_upstream_url`` and ``ipa_ramdisk_upstream_url`` in
``etc/kayobe/ipa.yml``, alternatively, you can update the files that the URLs
point to. If building the images locally, follow the process outlined in
:ref:`building_ironic_deployment_images`.

To get Ironic to use an updated set of overcloud deployment images, you can run::

    (kayobe) $ kayobe baremetal compute update deployment image

This will register the images in Glance and update the ``deploy_ramdisk``
and ``deploy_kernel`` properties of the Ironic nodes.

Before rolling out the update to all nodes, it can be useful to test the image
on a limited subset. To do this, you can use the ``baremetal-compute-limit``
option. See :ref:`update_deployment_image` for more details.

Building Container Images
-------------------------

.. note::

   It is possible to use prebuilt container images from an image registry such
   as Dockerhub.  In this case, this step can be skipped.

In some cases it may be necessary to build images locally either to apply local
image customisation or to use a downstream version of kolla.  To build images
locally::

    (kayobe) $ kayobe overcloud container image build

It is possible to build a specific set of images by supplying one or more
image name regular expressions::

    (kayobe) $ kayobe overcloud container image build ironic- nova-api

In order to push images to a registry after they are built, add the ``--push``
argument.

Pulling Container Images
------------------------

.. note::

   It is possible to build container images locally avoiding the need for an
   image registry such as Dockerhub.  In this case, this step can be skipped.

In most cases suitable prebuilt kolla images will be available on Dockerhub.
The `stackhpc account <https://hub.docker.com/r/stackhpc/>`_ provides image
repositories suitable for use with kayobe and will be used by default.  To
pull images from the configured image registry::

    (kayobe) $ kayobe overcloud container image pull

Saving Overcloud Service Configuration
--------------------------------------

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
------------------------------------------

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

Upgrading Containerised Services
--------------------------------

Containerised control plane services may be upgraded by replacing existing
containers with new containers using updated images which have been pulled from
a registry or built locally.

To upgrade the containerised control plane services::

    (kayobe) $ kayobe overcloud service upgrade

It is possible to specify tags for Kayobe and/or kolla-ansible to restrict the
scope of the upgrade::

    (kayobe) $ kayobe overcloud service upgrade --tags config --kolla-tags keystone
