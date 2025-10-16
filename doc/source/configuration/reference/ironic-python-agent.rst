=========================
Ironic Python Agent (IPA)
=========================

This section covers configuration of Ironic Python Agent (IPA) which is used by
Ironic and Ironic Inspector to deploy and inspect bare metal nodes. This is
used by the Bifrost services that run on the seed host, and also by Ironic and
Ironic Inspector services running in the overcloud for bare metal compute, if
enabled (``kolla_enable_ironic`` is ``true``). IPA configuration is typically
applied in ``${KAYOBE_CONFIG_PATH}/ipa.yml``. Consult the
:ironic-python-agent-doc:`IPA documentation <>` for full details of IPA usage
and configuration.

.. _configuration-ipa-build:

Ironic Python Agent (IPA) image build configuration
===================================================

.. note::

   This section may be skipped if not building IPA images locally
   (``ipa_build_images`` is ``false``).

The following options cover building of IPA images via Diskimage-builder (DIB).
Consult the :diskimage-builder-doc:`Diskimage-builder documentation <>` for
full details.

The default configuration builds a CentOS Stream 9 ramdisk image which includes
the upstream IPA source code, and has a serial console enabled.

The images are built for Bifrost via ``kayobe seed deployment image build``,
and for Ironic in the overcloud (if enabled) via ``kayobe overcloud deployment
image build``.

``ipa_build_images``
    Whether to build IPA images from source. Default is ``False``.
``ipa_build_source_url``
    URL of IPA source repository. Default is
    https://opendev.org/openstack/ironic-python-agent
``ipa_build_source_version``
    Version of IPA source repository. Default is ``{{ openstack_branch }}``.
``ipa_builder_source_url``
    URL of IPA builder source repository. Default is
    https://opendev.org/openstack/ironic-python-agent-builder
``ipa_builder_source_version``
    Version of IPA builder source repository. Default is ``master``.
``ipa_build_dib_host_packages_extra``
    List of additional build host packages to install. Default is ``[ 'zstd' ]``.
``ipa_build_dib_elements_default``
    List of default Diskimage Builder (DIB) elements to use when building IPA
    images. Default is ``["centos", "dynamic-login", "enable-serial-console",
    "ironic-python-agent-ramdisk"]`` when ``os_distribution`` is ``"rocky"``, and
    ``["ubuntu", "dynamic-login", "enable-serial-console",
    "ironic-python-agent-ramdisk"]`` otherwise.
``ipa_build_dib_elements_extra``
    List of additional Diskimage Builder (DIB) elements to use when building IPA
    images. Default is empty.
``ipa_build_dib_elements``
    List of Diskimage Builder (DIB) elements to use when building IPA images.
    Default is combination of ``ipa_build_dib_elements_default`` and
    ``ipa_build_dib_elements_extra``.
``ipa_build_dib_env_default``
    Dictionary of default environment variables to provide to Diskimage Builder
    (DIB) during IPA image build. Default is ``{"DIB_RELEASE": "9-stream",
    "DIB_REPOLOCATION_ironic_python_agent": "{{ ipa_build_source_url }}",
    "DIB_REPOREF_ironic_python_agent": "{{ ipa_build_source_version }}",
    "DIB_REPOREF_requirements": "{{ ipa_build_source_version }}"}`` if
    ``os_distribution`` is ``"rocky"`` else ``{"DIB_RELEASE": "{{ os_release
    }}", "DIB_REPOLOCATION_ironic_python_agent": "{{ ipa_build_source_url }}",
    "DIB_REPOREF_ironic_python_agent": "{{ ipa_build_source_version }}",
    "DIB_REPOREF_requirements": "{{ ipa_build_source_version }}"}``.
``ipa_build_dib_env_extra``
    Dictionary of additional environment variables to provide to Diskimage
    Builder (DIB) during IPA image build. Default is empty.
``ipa_build_dib_env``
    Dictionary of environment variables to provide to Diskimage Builder (DIB)
    during IPA image build. Default is a combination of
    ``ipa_build_dib_env_default`` and ``ipa_build_dib_env_extra``.
``ipa_build_dib_git_elements_default``
    List of default git repositories containing Diskimage Builder (DIB)
    elements. See `stackhpc.openstack.os_images
    <https://galaxy.ansible.com/ui/repo/published/stackhpc/openstack/content/role/os_images/>`__
    role for usage. Default is one item for IPA builder.
``ipa_build_dib_git_elements_extra``
    List of additional git repositories containing Diskimage Builder (DIB)
    elements. See `stackhpc.openstack.os_images
    <https://galaxy.ansible.com/ui/repo/published/stackhpc/openstack/content/role/os_images/>`__
    role for usage. Default is none.
``ipa_build_dib_git_elements``
    List of git repositories containing Diskimage Builder (DIB) elements. See
    `stackhpc.openstack.os_images <https://galaxy.ansible.com/ui/repo/published/stackhpc/openstack/content/role/os_images/>`__
    role for usage. Default is combination of ``ipa_build_dib_git_elements_default``
    and ``ipa_build_dib_git_elements_extra``.
``ipa_build_dib_packages``
    List of DIB packages to install. Default is none.
``ipa_build_upper_constraints_file``
    Upper constraints file for installing packages in the virtual environment
    used for building IPA images. Default is ``{{ pip_upper_constraints_file
    }}``.

Example: Building IPA images locally
------------------------------------

To build IPA images locally:

.. code-block:: yaml
   :caption: ``ipa.yml``

   ipa_build_images: true

Example: Installing IPA from a custom git repository
----------------------------------------------------

To install IPA from a custom git repository:

.. code-block:: yaml
   :caption: ``ipa.yml``

   ipa_source_url: https://git.example.com/ironic-python-agent
   ipa_source_version: downstream

Example: Adding an element
--------------------------

In the following example, we extend the list of DIB elements to add the
:diskimage-builder-doc:`mellanox element <elements/mellanox/README>`, which can
be useful for inspecting hardware with Mellanox InfiniBand NICs.

.. code-block:: yaml
   :caption: ``ipa.yml``

   ipa_build_dib_elements_extra:
     - "mellanox"

Example: Dynamically allowing access to the IPA environment
-----------------------------------------------------------

When debugging a failed deployment, it can sometimes be necessary to allow
access to the image dynamically.

The :diskimage-builder-doc:`dynamic-login element
<elements/dynamic-login/README>` can be used to authorize SSH keys by appending
them to the kernel arguments. This element is included by default in IPA images
since the Epoxy 18.0.0 release. On previous releases, it can be added with:

.. code-block:: yaml
   :caption: ``ipa.yml``

   ipa_build_dib_elements_extra:
     - "dynamic-login"

Bifrost can be configured to use ``dynamic-login`` with the
``kolla_bifrost_extra_kernel_options`` variable:

.. code-block:: yaml
   :caption: ``bifrost.yml``

   kolla_bifrost_extra_kernel_options:
     - sshkey="ssh-rsa BBA1..."

The updated configuration is applied with ``kayobe seed service deploy``.

Overcloud Ironic can be configured with the
``kolla_ironic_kernel_append_params_extra`` variable:

.. code-block:: yaml
   :caption: ``ironic.yml``

   kolla_ironic_kernel_append_params_extra:
     - sshkey="ssh-rsa BBA1..."

The updated configuration is applied with ``kayobe overcloud service deploy``.

Further information on troubleshooting IPA can be found
:ironic-python-agent-doc:`here <admin/troubleshooting>`.

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
   :caption: ``ipa.yml``

   ipa_build_dib_elements_extra:
     - "devuser"

   ipa_build_dib_env_extra:
     DIB_DEV_USER_USERNAME: "devuser"
     DIB_DEV_USER_PASSWORD: "correct horse battery staple"
     DIB_DEV_USER_PWDLESS_SUDO: "yes"

Further information on troubleshooting IPA can be found
:ironic-python-agent-doc:`here <admin/troubleshooting>`.

Example: Configuring custom DIB elements
----------------------------------------

Sometimes it is useful to use custom DIB elements that are not shipped with DIB
itself. This can be done by sharing them in a git repository.

.. code-block:: yaml
   :caption: ``ipa.yml``

   ipa_build_dib_elements_extra:
     - "my-element"

   ipa_build_dib_git_elements:
     - repo: "https://git.example.com/custom-dib-elements"
       local: "{{ source_checkout_path }}/custom-dib-elements"
       version: "master"
       elements_path: "elements"

In this example the ``master`` branch of
https://git.example.com/custom-dib-elements would have a top level ``elements``
directory, containing a ``my-element`` directory for the element.

Example: Installing a package
-----------------------------

It can be necessary to install additional packages in the IPA image. Rather
than needing to write a custom DIB element, we can use the
``ipa_build_dib_packages`` variable. For example, to install the
``biosdevname`` package:

.. code-block:: yaml
   :caption: ``ipa.yml``

   ipa_build_dib_packages:
     - "biosdevname"

Ironic Python Agent (IPA) images configuration
==============================================

.. note::

   If building IPA images locally (``ipa_build_images`` is ``true``) this
   section can be skipped.

The following options configure the source of Ironic Python Agent images for
inspection and deployment.  Consult the :ironic-python-agent-doc:`Ironic Python
Agent documentation <>` for full details.

``ipa_images_upstream_url_suffix``
    Suffix of upstream Ironic deployment image files. Default is based on
    ``{{ openstack_branch }}``.
``ipa_images_kernel_name``
    Name of Ironic deployment kernel image to register in Glance. Default is
    ``ipa.kernel``.
``ipa_kernel_upstream_url``
    URL of Ironic deployment kernel image to download. Default is
    ``https://tarballs.openstack.org/ironic-python-agent/dib/files/ipa-centos9{{
    ipa_images_upstream_url_suffix }}.kernel``.
``ipa_kernel_checksum_url``
    URL of checksum of Ironic deployment kernel image. Default is ``{{
    ipa_kernel_upstream_url }}.{{ ipa_kernel_checksum_algorithm }}``.
``ipa_kernel_checksum_algorithm``
    Algorithm of checksum of Ironic deployment kernel image. Default is
    ``sha256``.
``ipa_images_ramdisk_name``
    Name of Ironic deployment ramdisk image to register in Glance. Default is
    ``ipa.initramfs``.
``ipa_ramdisk_upstream_url``
    URL of Ironic deployment ramdisk image to download. Default is
    ``https://tarballs.openstack.org/ironic-python-agent/dib/files/ipa-centos9{{
    ipa_images_upstream_url_suffix }}.initramfs``.
``ipa_ramdisk_checksum_url``
    URL of checksum of Ironic deployment ramdisk image. Default is ``{{
    ipa_ramdisk_upstream_url }}.{{ ipa_ramdisk_checksum_algorithm }}``.
``ipa_ramdisk_checksum_algorithm``
    Algorithm of checksum of Ironic deployment ramdisk image. Default is
    ``sha256``.

Ironic Python Agent (IPA) deployment configuration
==================================================

The following options configure how IPA operates during deployment and
inspection.

``ipa_collect_lldp``
    Whether to enable collection of LLDP TLVs. Default is ``True``.
``ipa_collectors_default``
    .. note::

       ``extra-hardware`` is not currently included as it requires a ramdisk
       with the ``hardware`` python module installed.

    List of default inspection collectors to run. Default is ``["default",
    "logs", "pci-devices"]``.
``ipa_collectors_extra``
    List of additional inspection collectors to run. Default is none.
``ipa_collectors``
    List of inspection collectors to run. Default is a combination of
    ``ipa_collectors_default`` and ``ipa_collectors_extra``.
``ipa_benchmarks_default``
    List of default inspection benchmarks to run. Default is ``["cpu", "disk",
    "ram"]``.
``ipa_benchmarks_extra``
    List of extra inspection benchmarks to run. Default is none.
``ipa_benchmarks``
    .. note::

       The ``extra-hardware`` collector must be enabled in order to execute
       benchmarks during inspection.

    List of inspection benchmarks to run. Default is a combination of
    ``ipa_benchmarks_default`` and ``ipa_benchmarks_extra``.
``ipa_kernel_options_default``
    List of default kernel parameters for Ironic python agent. Default includes
    ``ipa-collect-lldp``, ``ipa-inspection-collectors`` and
    ``ipa-inspection-benchmarks``, with arguments taken from
    ``ipa_collect_lldp``, ``ipa_collectors`` and ``ipa_benchmarks``.
``ipa_kernel_options_extra``
    List of additional kernel parameters for Ironic python agent. Default is
    none.
``ipa_kernel_options``
    List of kernel parameters for Ironic python agent. Default is a combination
    of ``ipa_kernel_options_default`` and ``ipa_kernel_options_extra``.

Example: Adding the ``extra-hardware`` collector
------------------------------------------------

The ``extra-hardware`` collector may be used to collect additional information
about hardware during inspection. It is also a requirement for running
benchmarks. This collector depends on the Python `hardware package
<https://pypi.org/project/hardware/>`__, which is not installed in IPA images
by default.

The following example enables the ``extra-hardware`` collector:

.. code-block:: yaml
   :caption: ``ipa.yml``

   ipa_collectors_extra:
     - "extra-hardware"

The ``ironic-python-agent-builder`` repository provides an `extra-hardware
element
<https://docs.openstack.org/ironic-python-agent-builder/latest/admin/dib.html#ironic-python-agent-ipa-extra-hardware>`__
which may be used to install this package. It may be used as follows if
building an IPA image locally:

.. code-block:: yaml
   :caption: ``ipa.yml``

   ipa_build_dib_elements_extra:
     - "extra-hardware"

Example: Passing additional kernel arguments to IPA
---------------------------------------------------

The following example shows how to pass additional kernel arguments to IPA:

.. code-block:: yaml
   :caption: ``ipa.yml``

   ipa_kernel_options_extra:
     - "foo=bar"
