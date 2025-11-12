.. _overcloud-dib:

===============================
Overcloud host disk image build
===============================

This section covers configuration for building overcloud host disk images with
Diskimage builder (DIB), which is available from the Yoga 12.0.0 release. This
configuration is applied in ``${KAYOBE_CONFIG_PATH}/overcloud-dib.yml``.

Enabling host disk image build
==============================

From the Yoga release, disk images for overcloud hosts can be built directly
using Diskimage builder rather than through Bifrost. This is enabled with the
following option:

``overcloud_dib_build_host_images``
    Whether to build host disk images with DIB directly instead of through
    Bifrost. Setting it to true disables Bifrost image build and allows images
    to be built with the ``kayobe overcloud host image build`` command. Default
    value is true since the Zed release.

With this option enabled, Bifrost will be configured to stop building a root
disk image. This will become the default behaviour in a future release.

Overcloud root disk image configuration
=======================================

Kayobe uses Diskimage builder (DIB) to build root disk images that are deployed
to overcloud hosts when they are provisioned. The following options configure
how these images are built. Consult the
:diskimage-builder-doc:`Diskimage-builder documentation <>` for further
information on building disk images.

The default configuration builds a whole disk (partitioned) image using the
selected :ref:`OS distribution <os-distribution>` (Rocky Linux 10 by default)
with serial console enabled, and SELinux disabled if CentOS Stream or Rocky
Linux is used.
`Cloud-init <https://cloudinit.readthedocs.io/en/latest/>`__ is used to process
the configuration drive built by Bifrost during provisioning.

``overcloud_dib_host_packages_extra``
    List of additional host packages to install. Default is an empty list.
``overcloud_dib_host_images``
    List of overcloud host disk images to build. Each element is a dict
    defining an image in a format accepted by the `stackhpc.openstack.os_images
    <https://galaxy.ansible.com/ui/repo/published/stackhpc/openstack/content/role/os_images/>`__
    role. Default is to build an image named ``deployment_image`` configured
    with the ``overcloud_dib_*`` variables defined below: ``{"name":
    "deployment_image", "elements": "{{ overcloud_dib_elements }}", "env": "{{
    overcloud_dib_env_vars }}", "packages": "{{ overcloud_dib_packages }}"}``.
``overcloud_dib_os_element``
    DIB base OS element. Default is ``{{ 'rocky-container' if os_distribution == 'rocky' else os_distribution }}``.
``overcloud_dib_os_release``
    DIB image OS release. Default is ``{{ os_release }}``.
``overcloud_dib_elements_default``
    List of default DIB elements. Default is ``["{{ overcloud_dib_os_element
    }}", "cloud-init-datasources", "enable-serial-console", "vm"]``. The ``vm``
    element is poorly named, and causes DIB to build a whole disk image rather
    than a single partition.
``overcloud_dib_elements_extra``
    List of additional DIB elements. Default is none.
``overcloud_dib_elements``
    List of DIB elements. Default is a combination of ``overcloud_dib_elements_default``
    and ``overcloud_dib_elements_extra``.
``overcloud_dib_env_vars_default``
    DIB default environment variables. Default is
    ``{"DIB_BOOTLOADER_DEFAULT_CMDLINE": "nofb nomodeset gfxpayload=text
    net.ifnames=1", "DIB_CLOUD_INIT_DATASOURCES": "ConfigDrive",
    "DIB_CONTAINERFILE_RUNTIME": "docker", "DIB_CONTAINERFILE_NETWORK_DRIVER":
    "host", DIB_RELEASE": "{{ overcloud_dib_os_release }}"}``.
``overcloud_dib_env_vars_extra``
    DIB additional environment variables. Default is none.
``overcloud_dib_env_vars``
    DIB environment variables. Default is combination of
    ``overcloud_dib_env_vars_default`` and
    ``overcloud_dib_env_vars_extra``.
``overcloud_dib_packages``
    List of DIB packages to install. Default is to install no extra packages.
``overcloud_dib_git_elements_default``
    List of default git repositories containing Diskimage Builder (DIB)
    elements. See stackhpc.openstack.os_images role for usage.
    Default is empty.
``overcloud_dib_git_elements_extra``
    List of additional git repositories containing Diskimage Builder (DIB)
    elements. See stackhpc.openstack.os_imagesimages role for usage.
    Default is empty.
``overcloud_dib_git_elements``
    List of git repositories containing Diskimage Builder (DIB) elements. See
    stackhpc.openstack.os_images role for usage. Default is a combination of
    ``overcloud_dib_git_elements_default`` and
    ``overcloud_dib_git_elements_extra``.
``overcloud_dib_upper_constraints_file``
    Upper constraints file for installing packages in the virtual environment
    used for building overcloud host disk images. Default is ``{{
    pip_upper_constraints_file }}``.
``overcloud_dib_dib_upper_constraints_file``
    Upper constraints file for installation of DIB to build overcloud
    host disk images. Default is empty string.

Disk images are built with the following command:

.. code-block:: console

   (kayobe) $ kayobe overcloud host image build

It is worth noting that images will not be rebuilt if they already exist. To
force rebuilding images, it is necessary to use the ``--force-rebuild``
argument.

.. code-block:: console

   (kayobe) $ kayobe overcloud host image build --force-rebuild

Example: Adding an element
--------------------------

In the following, we extend the list of DIB elements to add the ``growpart``
element:

.. code-block:: yaml
   :caption: ``dib.yml``

   overcloud_dib_elements_extra:
     - "growpart"

Example: Building an XFS root filesystem image
----------------------------------------------

By default, DIB will format the image as ``ext4``. In some cases it might be
useful to use XFS, for example when using the ``overlay`` Docker storage driver
which can reach the maximum number of hardlinks allowed by ``ext4``.

In DIB, we achieve this by setting the ``FS_TYPE`` environment variable to
``xfs``.

.. code-block:: yaml
   :caption: ``dib.yml``

   overcloud_dib_env_vars_extra:
     FS_TYPE: "xfs"

Example: Configuring a development user account
-----------------------------------------------

.. warning::

   A development user account should not be used in production.

When debugging a failed deployment, it can sometimes be necessary to allow
access to the image via a preconfigured user account with a known password.
This can be achieved via the :diskimage-builder-doc:`devuser
<elements/devuser/README>` element.

This example shows how to add the ``devuser`` element, and configure a username
and password for an account that has passwordless sudo:

.. code-block:: yaml
   :caption: ``dib.yml``

   overcloud_dib_elements_extra:
     - "devuser"

   overcloud_dib_env_vars_extra:
     DIB_DEV_USER_USERNAME: "devuser"
     DIB_DEV_USER_PASSWORD: "correct horse battery staple"
     DIB_DEV_USER_PWDLESS_SUDO: "yes"

Alternatively, the :diskimage-builder-doc:`dynamic-login element
<elements/dynamic-login/README>` can be used to authorize SSH keys by appending
them to the kernel arguments.

Example: Configuring custom DIB elements
----------------------------------------

Sometimes it is useful to use custom DIB elements that are not shipped with DIB
itself. This can be done by sharing them in a git repository.

.. code-block:: yaml
   :caption: ``overcloud-dib.yml``

   overcloud_dib_elements_extra:
     - "my-element"

   overcloud_dib_git_elements:
     - repo: "https://git.example.com/custom-dib-elements"
       local: "{{ source_checkout_path }}/custom-dib-elements"
       version: "master"
       elements_path: "elements"

In this example the ``master`` branch of
https://git.example.com/custom-dib-elements would have a top level ``elements``
directory, containing a ``my-element`` directory for the element.

Example: Installing a package
-----------------------------

It can be necessary to install additional packages in the root disk image.
Rather than needing to write a custom DIB element, we can use the
``overcloud_dib_packages`` variable. For example, to install the
``biosdevname`` package:

.. code-block:: yaml
   :caption: ``dib.yml``

   overcloud_dib_packages:
     - "biosdevname"

Example: Building multiple images
---------------------------------

It can be necessary to build multiple images to support the various types of
hardware present in a deployment or the different functions performed by
overcloud hosts. This can be configured with the ``overcloud_dib_host_images``
variable, using a format accepted by the `stackhpc.openstack.os_images
<https://galaxy.ansible.com/ui/repo/published/stackhpc/openstack/content/role/os_images/>`__
role. Note that image names should not include the file extension. For example,
to build a second image with a development user account and the ``biosdevname``
package:

.. code-block:: yaml
   :caption: ``dib.yml``

   overcloud_dib_host_images:
     - name: "deployment_image"
       elements: "{{ overcloud_dib_elements }}"
       env: "{{ overcloud_dib_env_vars }}"
       packages: "{{ overcloud_dib_packages }}"
     - name: "debug_deployment_image"
       elements: "{{ overcloud_dib_elements + ['devuser'] }}"
       env: "{{ overcloud_dib_env_vars | combine(devuser_env_vars) }}"
       packages: "{{ overcloud_dib_packages + ['biosdevname'] }}"

   devuser_env_vars:
     DIB_DEV_USER_USERNAME: "devuser"
     DIB_DEV_USER_PASSWORD: "correct horse battery staple"
     DIB_DEV_USER_PWDLESS_SUDO: "yes"

Running the ``kayobe overcloud host image build`` command with this
configuration will create two images: ``deployment_image.qcow2`` and
``debug_deployment_image.qcow2``.

Disk image deployment configuration
===================================

See :ref:`disk image deployment configuration in
Bifrost<configuration-bifrost-image-deployment-config>` for how to configure
the root disk image to be used to provision each host.
