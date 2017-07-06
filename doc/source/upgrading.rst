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

    (kayobe-venv) $ pip install -U .

Migrating Kayobe Configuration
------------------------------

Kayobe configuration options may be changed between releases of kayobe. Ensure
that all site local configuration is migrated to the target version format. If
using the `kayobe-config <https://github.com/stackhpc/kayobe-config>`_ git
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

    (kayobe-venv) $ kayobe configuration dump

The output of this command is a JSON object mapping hosts to their
configuration.  The output of the command may be restricted using the
``--host``, ``--hosts``, ``--var-name`` and ``--dump-facts`` options.

Upgrading the Control Host
==========================

Before starting the upgrade we must upgrade the Ansible control host.  Tasks
performed here include:

- Install updated Ansible role dependencies from Ansible Galaxy.
- Generate an SSH key if necessary and add it to the current user's authorised
  keys.

To upgrade the Ansible control host::

    (kayobe-venv) $ kayobe control host upgrade

Upgrading the Seed
==================

Currently, upgrading the seed services is not supported.

Upgrading the Overcloud
=======================

The overcloud services are upgraded in two steps.  First, new container images
should be obtained either by building them locally or pulling them from an
image registry.  Second, the overcloud services should be replaced with new
containers created from the new container images.

Upgrading the Ironic Deployment Images
--------------------------------------

Prior to upgrading the OpenStack control plane, the baremetal compute nodes
should be configured to use an updated deployment ramdisk. This procedure is
not currently automated by kayobe.

Building Container Images
-------------------------

.. note::

   It is possible to use prebuilt container images from an image registry such
   as Dockerhub.  In this case, this step can be skipped.

In some cases it may be necessary to build images locally either to apply local
image customisation or to use a downstream version of kolla.  To build images
locally::

    (kayobe-venv) $ kayobe overcloud container image build

It is possible to build a specific set of images by supplying one or more
image name regular expressions::

    (kayobe-venv) $ kayobe overcloud container image build ironic- nova-api

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

    (kayobe-venv) $ kayobe overcloud container image pull

Upgrading Containerised Services
--------------------------------

Containerised control plane services may be upgraded by replacing existing
containers with new containers using updated images which have been pulled from
a registry or built locally.

To upgrade the containerised control plane services::

    (kayobe-venv) $ kayobe overcloud service upgrade

It is possible to specify tags for Kayobe and/or kolla-ansible to restrict the
scope of the upgrade::

    (kayobe-venv) $ kayobe overcloud service upgrade --tags config --kolla-tags keystone
