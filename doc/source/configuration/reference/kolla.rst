.. _configuration-kolla:

===================
Kolla Configuration
===================

Anyone using Kayobe to build images should familiarise themselves with the
:kolla-doc:`Kolla project's documentation <>`.

Container Image Build Host
==========================

Images are built on hosts in the ``container-image-builders`` group. The
default Kayobe Ansible inventory places the seed host in this group, although
it is possible to put a different host in the group, by modifying the
inventory.

For example, to build images on ``localhost``:

.. code-block:: console
   :caption: ``inventory/groups``

   [container-image-builders:children]

.. code-block:: console
   :caption: ``inventory/hosts``

   [container-image-builders]
   localhost

Kolla Installation
==================

Prior to building container images, Kolla and its dependencies will be
installed on the container image build host. The following variables affect the
installation of Kolla:

``kolla_ctl_install_type``
    Type of installation, either ``binary`` (PyPI) or ``source`` (git). Default
    is ``source``.
``kolla_source_path``
    Path to directory for Kolla source code checkout. Default is ``{{
    source_checkout_path ~ '/kolla' }}``.
``kolla_source_url``
    URL of Kolla source code repository if type is ``source``. Default is
    https://opendev.org/openstack/kolla.
``kolla_source_version``
    Version (branch, tag, etc.) of Kolla source code repository if type is
    ``source``. Default is ``{{ openstack_branch }}``, which is the same as the
    Kayobe upstream branch name.
``kolla_venv``
    Path to virtualenv in which to install Kolla on the container image build
    host. Default is ``{{ virtualenv_path ~ '/kolla' }}``.
``kolla_build_config_path``
    Path in which to generate kolla configuration. Default is ``{{ config_path
    ~ '/kolla' }}``.

For example, to install from a custom Git repository:

.. code-block:: yaml
   :caption: ``kolla.yml``

   kolla_source_url: https://git.example.com/kolla
   kolla_source_version: downstream

.. _configuration-kolla-global:

Global Configuration
====================

The following variables are global, affecting all container images. They are
used to generate the Kolla configuration file, ``kolla-build.conf``, and also
affect :ref:`Kolla Ansible configuration <configuration-kolla-ansible-global>`.

``kolla_base_arch``
    Kolla base container image architecture. Options are ``x86_64``,
    ``aarch64``. Default is ``{{ ansible_facts.architecture }}``.
``kolla_base_distro``
    Kolla base container image distribution. Options are ``centos``,
    ``debian``, ``rocky`` or ``ubuntu``. Default is ``{{ os_distribution }}``.
``kolla_base_distro_version``
    Kolla base container image distribution version. Default is dependent on
    ``kolla_base_distro``.
``kolla_docker_namespace``
    Docker namespace to use for Kolla images. Default is ``kolla``.
``kolla_docker_registry``
    URL of docker registry to use for Kolla images. Default is to use the value
    of ``docker_registry`` or ``podman_registry``, depending on the value of
    ``container_engine`` (see :ref:`configuration-hosts-container-engine`).
``kolla_docker_registry_username``
    Username to use to access a docker registry. Default is not set, in which
    case the registry will be used without authentication.
``kolla_docker_registry_password``
    Password to use to access a docker registry. Default is not set, in which
    case the registry will be used without authentication.
``kolla_openstack_release``
    Kolla OpenStack release version. This should be a Docker image tag. Default
    is the OpenStack release name (e.g. ``rocky``) on stable branches and
    tagged releases, or ``master`` on the Kayobe ``master`` branch.
``kolla_tag``
    Kolla container image tag. This is the tag that will be applied to built
    container images. Default is ``kolla_openstack_release``.

For example, to build the Kolla ``rocky`` images with a namespace
of ``example``, and a private Docker registry at ``registry.example.com:4000``,
using the ``zed`` release:

.. code-block:: yaml
   :caption: ``kolla.yml``

   kolla_base_distro: rocky
   kolla_docker_namespace: example
   kolla_docker_registry: registry.example.com:4000
   kolla_openstack_release: zed

The ``ironic-api`` image built with this configuration would be referenced as
follows:

.. code-block:: console

   registry.example.com:4000/example/ironic-api:zed-rocky-9

Further customisation of the Kolla configuration file can be performed by
writing a file at ``${KAYOBE_CONFIG_PATH/kolla/kolla-build.conf``. For example,
to enable debug logging:

.. code-block:: ini
   :caption: ``kolla/kolla-build.conf``

   [DEFAULT]
   debug = True

Seed Images
===========

The ``kayobe seed container image build`` command builds images for the seed
services. The only image required for the seed services is the
``bifrost-deploy`` image.

Overcloud Images
================

The ``kayobe overcloud container image build`` command builds images for the
control plane.  The default set of images built depends on which services and
features are enabled via the ``kolla_enable_<service>`` flags in
``$KAYOBE_CONFIG_PATH/kolla.yml``.

For example, the following configuration will enable the Magnum service and add
the ``magnum-api`` and ``magnum-conductor`` containers to the set of overcloud
images that will be built:

.. code-block:: yaml
   :caption: ``kolla.yml``

   kolla_enable_magnum: true

If a required image is not built when the corresponding flag is set, check the
image sets defined in ``overcloud_container_image_sets`` in
``ansible/inventory/group_vars/all/kolla``.

Image Customisation
===================

There are three main approaches to customising the Kolla container images:

#. Overriding Jinja2 blocks
#. Overriding Jinja2 variables
#. Source code locations

Overriding Jinja2 blocks
------------------------

Kolla's images are defined via Jinja2 templates that generate Dockerfiles.
Jinja2 blocks are frequently used to allow specific statements in one or more
Dockerfiles to be replaced with custom statements. See the :kolla-doc:`Kolla
documentation <admin/image-building.html#generic-customisation>` for details.

Blocks are configured via the ``kolla_build_blocks`` variable, which is a dict
mapping Jinja2 block names in to their contents.

For example, to override the block ``header`` to add a custom label to every
image:

.. code-block:: yaml
   :caption: ``kolla.yml``

   kolla_build_blocks:
     header: |
       LABEL foo="bar"

This will result in Kayobe generating a ``template-override.j2`` file with the
following content:

.. code-block:: console
   :caption: ``template-override.j2``

   {% extends parent_template %}

   {% block header %}
   LABEL foo="bar"
   {% endblock %}

Overriding Jinja2 variables
---------------------------

Jinja2 variables offer another way to customise images.  See the
:kolla-doc:`Kolla documentation
<admin/image-building.html#package-customisation>` for details of using
variable overrides to modify the list of packages to install in an image.

Variable overrides are configured via the ``kolla_build_customizations``
variable, which is a dict/map mapping names of variables to override to their
values.

For example, to add ``mod_auth_openidc`` to the list of packages installed in
the ``keystone-base`` image, we can set the variable
``keystone_base_packages_append`` to a list containing ``mod_auth_openidc``.

.. code-block:: yaml
   :caption: ``kolla.yml``

   kolla_build_customizations:
     keystone_base_packages_append:
       - mod_auth_openidc

This will result in Kayobe generating a ``template-override.j2`` file with the
following content:

.. code-block:: console
   :caption: ``template-override.j2``

   {% extends parent_template %}

   {% set keystone_base_packages_append = ["mod_auth_openidc"] %}

Note that the variable value will be JSON-encoded in ``template-override.j2``.

Source code locations
---------------------

For ``source`` image builds, configuration of source code locations for
packages installed in containers by Kolla is possible via the ``kolla_sources``
variable. The format is a dict/map mapping names of sources to their
definitions. See the :kolla-doc:`Kolla documentation
<admin/image-building.html#build-openstack-from-source>` for details. The
default is to specify the URL and version of Bifrost, as defined in
``${KAYOBE_CONFIG_PATH}/bifrost.yml``.

For example, to specify a custom source location for the ``ironic-base``
package:

.. code-block:: yaml
   :caption: ``kolla.yml``

   kolla_sources:
     bifrost-base:
       type: "git"
       location: "{{ kolla_bifrost_source_url }}"
       reference: "{{ kolla_bifrost_source_version }}"
     ironic-base:
       type: "git"
       location: https://git.example.com/ironic
       reference: downstream

This will result in Kayobe adding the following configuration to
``kolla-build.conf``:

.. code-block:: ini
   :caption: ``kolla-build.conf``

   [bifrost-base]
   type = git
   location = https://opendev.org/openstack/bifrost
   reference = stable/rocky

   [ironic-base]
   type = git
   location = https://git.example.com/ironic
   reference = downstream

Note that it is currently necessary to include the Bifrost source location if
using a seed.

Plugins & additions
-------------------

These features can also be used for installing :kolla-doc:`plugins
<admin/image-building.html#plugin-functionality>` and :kolla-doc:`additions
<admin/image-building.html#additions-functionality>` to ``source`` type images.

For example, to install a ``networking-ansible`` plugin in the
``neutron-server`` image:

.. code-block:: yaml
   :caption: ``kolla.yml``

   kolla_sources:
     bifrost-base:
       type: "git"
       location: "{{ kolla_bifrost_source_url }}"
       reference: "{{ kolla_bifrost_source_version }}"
     neutron-server-plugin-networking-ansible:
       type: "git"
       location: https://git.example.com/networking-ansible
       reference: downstream

The ``neutron-server`` image automatically installs any plugins provided to it.
For images that do not, a block such as the following may be required:

.. code-block:: yaml
   :caption: ``kolla.yml``

   kolla_build_blocks:
     neutron_server_footer: |
       ADD plugins-archive /
       pip --no-cache-dir install /plugins/*

A similar approach may be used for additions.
