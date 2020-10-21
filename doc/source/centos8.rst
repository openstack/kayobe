========
CentOS 8
========

This section covers use of Kayobe on CentOS 8 in the Train release. From the
``7.1.0`` release, Kayobe supports both CentOS 7 and 8. However, CentOS 7 is
used by default, and some configuration changes are required to use CentOS 8.

Currently this documentation focuses on greenfield deployments. More
information about migrating from CentOS 7 to CentOS 8 will be provided soon.

See the :kolla-ansible-doc:`Kolla Ansible documentation <user/centos8>` for
information on using CentOS 8.

Container images
================

To support both CentOS 7 and 8, for the Train release only, Kolla publishes
images to Dockerhub with the following tags:

============== =============
CentOS version Tag
============== =============
7              train
8              train-centos8
============== =============

.. _centos8_building_container_images:

Building container images
-------------------------

For details on how to build container images based on CentOS 8, see the
:kolla-doc:`Kolla image building guide
<admin/image-building.html#building-kolla-images>`.  If building images
locally, the base image tag should be configured to use a CentOS 8 image.

.. code-block:: ini
   :caption: ``${KAYOBE_CONFIG_PATH}/kolla/kolla-build.conf``

   [DEFAULT]
   base_tag = 8

Also, the tag applied to the built images should be modified to match that
expected by Kolla Ansible.

.. code-block:: yaml
   :caption: ``${KAYOBE_CONFIG_PATH}/kolla.yml``

   kolla_tag: train-centos8

See :ref:`configuration-kolla-global` for further information.

Deploying container images
--------------------------

For the Train release only, Kolla Ansible applies a ``-centos8`` suffix
(configured via ``openstack_tag_suffix``) to image tags by default on CentOS 8
hosts. The default tag is therefore ``train-centos8``. If using a custom tag,
modify ``kolla_openstack_release``:

.. code-block:: yaml
   :caption: ``${KAYOBE_CONFIG_PATH}/kolla.yml``

   kolla_openstack_release: my-tag

This would result in Kolla Ansible using ``my-tag`` on CentOS 7 and
``my-tag-centos8`` on CentOS 8.

If you do not want the suffix to be applied, it may be set to an empty string:

.. code-block:: yaml
   :caption: ``${KAYOBE_CONFIG_PATH}/kolla/globals.yml``

   openstack_tag_suffix: ""

If you are using different tags for each service or image, and still want the
suffix to be applied (e.g. if migrating from CentOS 7 to 8), use a pattern like
the following:

.. code-block:: yaml
   :caption: ``${KAYOBE_CONFIG_PATH}/kolla/globals.yml``

   nova_tag: "my-nova-tag{% raw %}{{ openstack_tag_suffix }}{% endraw %}"

Seed VM
=======

By default, a CentOS 7 image is used to create the seed VM. This can be changed
via ``seed_vm_root_image``. For example, to use the upstream CentOS 8.2 cloud
image:

.. code-block:: yaml
   :caption: ``${KAYOBE_CONFIG_PATH}/seed-vm.yml``

   seed_vm_root_image: https://cloud.centos.org/centos/8/x86_64/images/CentOS-8-GenericCloud-8.2.2004-20200611.2.x86_64.qcow2

Migrating a Seed VM to CentOS 8
-------------------------------

By default, a seed VM is provisioned with separate root and data libvirt
volumes. If Docker volumes are stored on the data libvirt volume, a CentOS 7
seed VM can be easily migrated to CentOS 8 using the following instructions.

.. note::

   Backing up the seed VM is strongly recommended before attempting the
   migration. All data stored in the root libvirt volume will be lost.

On the seed hypervisor, shut down the seed VM and delete its root libvirt
volume, assuming that the seed VM is named ``seed`` and the libvirt storage
pool for the seed VM is named ``default``.

.. code-block:: console

   $ sudo virsh shutdown seed
   $ sudo virsh vol-delete seed-root --pool default

Update ``seed_vm_root_image`` in ``${KAYOBE_CONFIG_PATH}/seed-vm.yml`` to point
to a CentOS 8 image, as described earlier.

Reprovision the seed VM and configure its host OS:

.. code-block:: console

   (kayobe) $ kayobe seed vm provision
   (kayobe) $ kayobe seed host configure

Update the Kayobe configuration to build container images based on CentOS 8, as
described in :ref:`centos8_building_container_images`, and rebuild the bifrost
image:

.. code-block:: console

   (kayobe) $ kayobe seed container image build bifrost-deploy

Finally, redeploy Bifrost:

.. code-block:: console

   (kayobe) $ kayobe seed service deploy

Ironic Python Agent (IPA)
=========================

If building IPA images locally, by default a CentOS 7 based ramdisk will be
built. This can be changed via the following configuration:

.. code-block:: yaml
   :caption: ``${KAYOBE_CONFIG_PATH}/ipa.yml``

   ipa_build_dib_elements_default:
     - centos
     - enable-serial-console
     - ironic-python-agent-ramdisk

   ipa_build_dib_env_extra:
     DIB_RELEASE: 8

   ipa_build_dib_git_elements_default:
     - repo: "https://opendev.org/openstack/ironic-python-agent-builder"
       local: "{{ source_checkout_path }}/ironic-python-agent-builder"
       version: "master"
       elements_path: "dib"

   os_images_upper_constraints_file: https://releases.openstack.org/constraints/upper/ussuri

Alternatively, if you are downloading IPA images, you should apply the
following configuration to use CentOS 8:

.. code-block:: yaml
   :caption: ``${KAYOBE_CONFIG_PATH}/ipa.yml``

   ipa_kernel_upstream_url: "https://tarballs.openstack.org/ironic-python-agent/dib/files/ipa-centos8{{ ipa_images_upstream_url_suffix }}.kernel"
   ipa_ramdisk_upstream_url: "https://tarballs.openstack.org/ironic-python-agent/dib/files/ipa-centos8{{ ipa_images_upstream_url_suffix }}.initramfs"

After the images are built or downloaded, you will need to rename the kernel
from ``ipa.kernel`` to ``ipa.vmzlinuz``.

See :doc:`configuration/ironic-python-agent` for further information.

Overcloud root disk
===================

The overcloud root disk is based on CentOS 7 by default. This can be changed
via the following configuration:

.. code-block:: yaml
   :caption: ``${KAYOBE_CONFIG_PATH}/bifrost.yml``

   kolla_bifrost_dib_os_element: centos
   kolla_bifrost_dib_os_release: 8

Note that the version of ``diskimage-builder`` in the ``bifrost_deploy``
container on the seed must be at least ``2.35`` for CentOS 8 support.

See :doc:`configuration/bifrost` for further information.
