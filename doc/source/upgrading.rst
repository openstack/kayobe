.. _upgrading:

=========
Upgrading
=========

This section describes how to upgrade from one OpenStack release to another.

Preparation
===========

Before you start, be sure to back up any local changes, configuration, and
data.

Migrating Kayobe Configuration
------------------------------

Kayobe configuration options may be changed between releases of kayobe. Ensure
that all site local configuration is migrated to the target version format. If
using the `kayobe-config <https://opendev.org/openstack/kayobe-config>`_ git
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
* ``kolla_tag``
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

The `Kayobe release notes <https://docs.openstack.org/releasenotes/kayobe/>`__
provide information on each new release. In particular, the *Upgrade Notes* and
*Deprecation Notes* sections provide information that might affect the
configuration migration.

All changes made to the configuration should be committed and pushed to the
hosting git repository.

.. _upgrading-kayobe-configuration:

Updating Kayobe Configuration
=============================

Ensure that the Kayobe configuration is checked out at the required commit.

First, ensure that there are no uncommitted local changes to the repository::

    $ cd <base_path>/src/kayobe-config/
    $ git status

Pull down changes from the hosting repository. For example, to fetch changes
from the ``master`` branch of the ``origin`` remote::

    $ git checkout master
    $ git pull --ff-only origin master

Adjust this procedure to suit your environment.

.. _upgrading-kayobe:

Upgrading Kayobe
================

If a new, suitable version of kayobe is available, it should be installed.
As described in :ref:`installation`, Kayobe can be installed via the released
Python packages on PyPI, or from source. Installation from a Python package is
supported from Kayobe 5.0.0 onwards.

Kayobe supports skip-level (SLURP) upgrades, see the `Kolla Ansible docs
<https://docs.openstack.org/kolla-ansible/latest/user/operating-kolla.html#preparation-the-real-deal>`__
for details.

Upgrading from PyPI
-------------------

This section describes how to upgrade Kayobe from a Python package in a
virtualenv. This is supported from Kayobe 5.0.0 onwards.

Ensure that the virtualenv is activated::

    $ source <base_path>/venvs/kayobe/bin/activate

Update the pip package::

    (kayobe) $ pip install -U pip

.. note::

   When updating Ansible above version 2.9.x, first uninstall it with ``pip
   uninstall ansible``. A newer version will be installed with the next
   command, as a Kayobe dependency. If Ansible 2.10.x was installed and you
   want to use a newer version, also uninstall the ``ansible-base`` package
   with ``pip uninstall ansible-base``.

If upgrading to the latest version of Kayobe::

    (kayobe) $ pip install -U kayobe

Alternatively, to upgrade to a specific release of Kayobe::

    (kayobe) $ pip install kayobe==5.0.0

Upgrading from source
---------------------

This section describes how to install Kayobe from source in a virtualenv.

First, check out the required version of the Kayobe source code.  This may be
done by pulling down the new version from ``opendev.org``.  Make sure
that any local changes to kayobe are committed and merged with the new upstream
code as necessary.  For example, to pull version 5.0.0 from the ``origin``
remote::

    $ cd <base_path>/src/kayobe
    $ git pull origin 5.0.0

Ensure that the virtualenv is activated::

    $ source <base_path>/venvs/kayobe/bin/activate

Update the pip package::

    (kayobe) $ pip install -U pip

If using a non-editable install of Kayobe::

    (kayobe) $ cd <base_path>/src/kayobe
    (kayobe) $ pip install -U .

Alternatively, if using an editable install of Kayobe (version 5.0.0 onwards,
see :ref:`installation-editable` for details)::

    (kayobe) $ cd <base_path>/src/kayobe
    (kayobe) $ pip install -U -e .

.. _upgrading-control-host:

Upgrading the Ansible Control Host
==================================

Before starting the upgrade we must upgrade the Ansible control host.  Tasks
performed here include:

- Install updated Ansible role dependencies from Ansible Galaxy.
- Generate an SSH key if necessary and add it to the current user's authorised
  keys.
- Upgrade Kolla Ansible locally to the configured version.

To upgrade the Ansible control host::

    (kayobe) $ kayobe control host upgrade

Upgrading the Seed Hypervisor
=============================

Currently, upgrading the seed hypervisor services is not supported.  It may
however be necessary to upgrade host packages and some host services.

Upgrading Host Packages
-----------------------

Prior to upgrading the seed hypervisor, it may be desirable to upgrade system
packages on the seed hypervisor host.

To update all eligible packages, use ``*``, escaping if necessary::

    (kayobe) $ kayobe seed hypervisor host package update --packages "*"

To only install updates that have been marked security related::

    (kayobe) $ kayobe seed hypervisor host package update --packages "*" --security

Upgrading Host Services
-----------------------

It may be necessary to upgrade some host services::

    (kayobe) $ kayobe seed hypervisor host upgrade

Note that this will not perform full configuration of the host, and will
instead perform a targeted upgrade of specific services where necessary.

Upgrading the Seed
==================

The seed services are upgraded in two steps.  First, new container images
should be obtained either by building them locally or pulling them from an
image registry.  Second, the seed services should be replaced with new
containers created from the new container images.

Upgrading Host Packages
-----------------------

Prior to upgrading the seed, it may be desirable to upgrade system packages on
the seed host.

To update all eligible packages, use ``*``, escaping if necessary::

    (kayobe) $ kayobe seed host package update --packages "*"

To only install updates that have been marked security related::

    (kayobe) $ kayobe seed host package update --packages "*" --security

Note that these commands do not affect packages installed in containers, only
those installed on the host.

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

    (kayobe) $ kayobe seed deployment image build

To overwrite existing images, add the ``--force-rebuild`` argument.

Upgrading Host Services
-----------------------

It may be necessary to upgrade some host services::

    (kayobe) $ kayobe seed host upgrade

Note that this will not perform full configuration of the host, and will
instead perform a targeted upgrade of specific services where necessary.

Building Container Images
-------------------------

.. note::

   It is possible to use prebuilt container images from an image registry such
   as Quay.io.  In this case, this step can be skipped.

In some cases it may be necessary to build images locally either to apply local
image customisation or to use a downstream version of kolla.  To build images
locally::

    (kayobe) $ kayobe seed container image build

In order to push images to a registry after they are built, add the ``--push``
argument.

Upgrading Containerised Services
--------------------------------

Containerised seed services may be upgraded by replacing existing containers
with new containers using updated images which have been pulled from
a registry or built locally.

To upgrade the containerised seed services::

    (kayobe) $ kayobe seed service upgrade

Upgrading the Overcloud
=======================

The overcloud services are upgraded in two steps.  First, new container images
should be obtained either by building them locally or pulling them from an
image registry.  Second, the overcloud services should be replaced with new
containers created from the new container images.

Upgrading Host Packages
-----------------------

Prior to upgrading the OpenStack control plane, it may be desirable to upgrade
system packages on the overcloud hosts.

To update all eligible packages, use ``*``, escaping if necessary::

    (kayobe) $ kayobe overcloud host package update --packages "*"

To only install updates that have been marked security related::

    (kayobe) $ kayobe overcloud host package update --packages "*" --security

Note that these commands do not affect packages installed in containers, only
those installed on the host.

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

To overwrite existing images, add the ``--force-rebuild`` argument.

Upgrading Ironic Deployment Images
----------------------------------

Prior to upgrading the OpenStack control plane you should upgrade
the deployment images. If you are using prebuilt images, update
the following variables in ``etc/kayobe/ipa.yml`` accordingly:

* ``ipa_kernel_upstream_url``
* ``ipa_kernel_checksum_url``
* ``ipa_kernel_checksum_algorithm``
* ``ipa_ramdisk_upstream_url``
* ``ipa_ramdisk_checksum_url``
* ``ipa_ramdisk_checksum_algorithm``

Alternatively, you can update the files that the URLs point to. If building the
images locally, follow the process outlined in
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
   as Quay.io.  In this case, this step can be skipped.

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
   image registry such as Quay.io.  In this case, this step can be skipped.

In most cases suitable prebuilt kolla images will be available on Quay.io. The
`openstack.kolla organisation <https://quay.io/organization/openstack.kolla>`_
provides image repositories suitable for use with kayobe and will be used by
default. To pull images from the configured image registry::

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
followed by ``kayobe overcloud service configuration save`` to gather the
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
