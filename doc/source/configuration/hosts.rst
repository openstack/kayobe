==================
Host Configuration
==================

This section covers configuration of hosts. It does not cover configuration or
deployment of containers. Hosts that are configured by Kayobe include:

* Seed hypervisor (``kayobe seed hypervisor host configure``)
* Seed (``kayobe seed host configure``)
* Overcloud (``kayobe overcloud host configure``)

Unless otherwise stated, all host configuration described here is applied to
each of these types of host.

Configuration Location
======================

Some host configuration options are set via global variables, and others have a
variable for each type of host. The latter variables are included in the
following files under ``${KAYOBE_CONFIG_PATH}``:

* ``seed-hypervisor.yml``
* ``seed.yml``
* ``compute.yml``
* ``controller.yml``
* ``monitoring.yml``
* ``storage.yml``

Note that any variable may be set on a per-host or per-group basis, by using
inventory host or group variables - these delineations are for convenience.

Paths
=====

Several directories are used by Kayobe on the remote hosts. There is a
hierarchy of variables in ``${KAYOBE_CONFIG_PATH}/globals.yml`` that can be
used to control where these are located.

* ``base_path`` (default ``/opt/kayobe/``) sets the default base path for
  various directories.
* ``config_path`` (default ``{{ base_path }}/etc``) is a path in which to store
  configuration files.
* ``image_cache_path`` (default ``{{ base_path }}/images``) is a path in which
  to cache downloaded or built images.
* ``source_checkout_path`` (default ``{{ base_path }}/src``) is a path into
  which to store clones of source code repositories.
* ``virtualenv_path`` (default ``{{ base_path }}/venvs``) is a path in which to
  create Python virtual environments.

SSH Known Hosts
===============

While strictly this configuration is applied to the Ansible control host
(``localhost``), it is applied during the ``host configure`` commands.
The ``ansible_host`` of each host is added as an SSH known host. This is
typically the host's IP address on the admin network (``admin_oc_net_name``),
as defined in ``${KAYOBE_CONFIG_PATH}/network-allocation.yml`` (see
:ref:`configuration-network-ip-allocation`).

Kayobe User Bootstrapping
=========================

Kayobe uses a user account defined by the ``kayobe_ansible_user`` variable (in
``${KAYOBE_CONFIG_PATH}/globals.yml``) for remote SSH access. By default, this
is ``stack``.

Typically, the image used to provision these hosts will not include this user
account, so Kayobe performs a bootstrapping step to create it, as a different
user. In cloud images, there is often a user named after the OS distro, e.g.
``centos`` or ``ubuntu``. This user defaults to the name of the user running
Kayobe, but may be set via the following variables:

* ``seed_hypervisor_bootstrap_user``
* ``seed_bootstrap_user``
* ``compute_bootstrap_user``
* ``controller_bootstrap_user``
* ``monitoring_bootstrap_user``
* ``storage_bootstrap_user``

For example, to set the bootstrap user for controllers to ``centos``:

.. code-block:: yaml
   :caption: ``controllers.yml``

   controller_bootstrap_user: centos

PyPI Mirror
===========

Kayobe supports configuration of a PyPI mirror, via variables in
``${KAYOBE_CONFIG_PATH}/pip.yml``. This functionality is enabled by setting the
``pip_local_mirror`` variable to ``true``.

Kayobe will generate configuration for
``pip`` and ``easy_install`` to use the mirror, for the list of users defined
by ``pip_applicable_users`` (default ``kayobe_ansible_user`` and ``root``), in
addition to the user used for Kolla Ansible (``kolla_ansible_user``). The
mirror URL is configured via ``pip_index_url``, and ``pip_trusted_hosts`` is a
list of 'trusted' hosts, for which SSL verification will be disabled.

For example, to configure use of the test PyPI mirror at
https://test.pypi.org/simple/:

.. code-block:: yaml
   :caption: ``pip.yml``

   pip_local_mirror: true
   pip_index_url: https://test.pypi.org/simple/

Kayobe Remote Virtual Environment
=================================

By default, Ansible executes modules remotely using the system python
interpreter, even if the Ansible control process is executed from within a
virtual environment (unless the ``local`` connection plugin is used).
This is not ideal if there are python dependencies that must be installed
with isolation from the system python packages. Ansible can be configured to
use a virtualenv by setting the host variable ``ansible_python_interpreter``
to a path to a python interpreter in an existing virtual environment.

If kayobe detects that ``ansible_python_interpreter`` is set and references a
virtual environment, it will create the virtual environment if it does not
exist. Typically this variable should be set via a group variable in the
inventory for hosts in the ``seed``, ``seed-hypervisor``, and/or ``overcloud``
groups.

The default Kayobe configuration in the ``kayobe-config`` repository sets
``ansible_python_interpreter`` to ``{{ virtualenv_path }}/kayobe/bin/python``
for the ``seed``, ``seed-hypervisor``, and ``overcloud`` groups.

Disk Wiping
===========

Using hosts that may have stale data on their disks could affect the deployment
of the cloud. This is not a configuration option, since it should only be
performed once to avoid losing useful data. It is triggered by passing the
``--wipe-disks`` argument to the ``host configure`` commands.

Users and Groups
================

Linux user accounts and groups can be configured using the ``users_default``
variable in ``${KAYOBE_CONFIG_PATH}/users.yml``. The format of the list is
that used by the ``users`` variable of the `singleplatform-eng.users
<https://galaxy.ansible.com/singleplatform-eng/users>`__ role.  The following
variables can be used to set the users for specific types of hosts:

* ``seed_hypervisor_users``
* ``seed_users``
* ``compute_users``
* ``controller_users``
* ``monitoring_users``
* ``storage_users``

In the following example, a single user named ``bob`` is created. A password
hash has been generated via ``mkpasswd --method=sha-512``. The user is added to
the ``wheel`` group, and an SSH key is authorised. The SSH public key should be
added to the Kayobe configuration.

.. code-block:: yaml
   :caption: ``users.yml``

   users_default:
    - username: bob
      name: Bob
      password: "$6$wJt9MLWrHlWN8$oXJHbdaslm9guD5EC3Dry1mphuqF9NPeQ43OXk3cXZa2ze/F9FOTxm2KvvDkbdxBDs7ouwdiLTUJ1Ff40.cFU."
      groups:
        - wheel
      append: True
      ssh_key:
        - "{{ lookup('file', kayobe_config_path ~ '/ssh-keys/id_rsa_bob.pub') }}"

Package Repositories
====================

Kayobe supports configuration of package repositories via Yum, via variables in
``${KAYOBE_CONFIG_PATH}/yum.yml``.

Configuration of yum.conf
-------------------------

Global configuration of Yum is stored in ``/etc/yum.conf``, and options can be
set via the ``yum_config`` variable. Options are added to the ``[main]``
section of the file. For example, to configure Yum to use a proxy server:

.. code-block:: yaml
   :caption: ``yum.yml``

   yum_config:
     proxy: https://proxy.example.com

CentOS and EPEL Mirrors
-----------------------

CentOS and EPEL mirrors can be enabled by setting ``yum_use_local_mirror`` to
``true``.  CentOS repository mirrors are configured via the following
variables:

* ``yum_centos_mirror_host`` (default ``mirror.centos.org``) is the mirror
  hostname.
* ``yum_centos_mirror_directory`` (default ``centos``) is a directory on the
  mirror in which repositories may be accessed.

EPEL repository mirrors are configured via the following variables:

* ``yum_epel_mirror_host`` (default ``download.fedoraproject.org``) is the
  mirror hostname.
* ``yum_epel_mirror_directory`` (default ``pub/epel``) is a directory on the
  mirror in which repositories may be accessed.

For example, to configure CentOS and EPEL mirrors at mirror.example.com:

.. code-block:: yaml
   :caption: ``yum.yml``

   yum_use_local_mirror: true
   yum_centos_mirror_host: mirror.example.com
   yum_epel_mirror_host: mirror.example.com

Custom Yum Repositories
-----------------------

It is also possible to configure a list of custom Yum repositories via the
``yum_custom_repos`` variable. The format is a dict/map, with repository names
mapping to a dict/map of arguments to pass to the Ansible ``yum`` module.

For example, the following configuration defines a single Yum repository called
``widgets``.

.. code-block:: yaml
   :caption: ``yum.yml``

   yum_custom_repos:
     widgets:
       baseurl: http://example.com/repo
       file: widgets
       gpgkey: http://example.com/gpgkey
       gpgcheck: yes

Disabling EPEL
--------------

It is possible to disable the EPEL Yum repository by setting
``yum_install_epel`` to ``false``.

SELinux
=======

SELinux is not supported by Kolla Ansible currently, so it is disabled by
Kayobe. If necessary, Kayobe will reboot systems in order to apply a change to
the SELinux configuration. The timeout for waiting for systems to reboot is
``disable_selinux_reboot_timeout``. Alternatively, the reboot may be avoided by
setting ``disable_selinux_do_reboot`` to ``false``.

Network Configuration
=====================

Configuration of host networking is covered in depth in
:ref:`configuration-network`.

Sysctls
=======

Arbitrary ``sysctl`` configuration can be applied to hosts. The variable format
is a dict/map, mapping parameter names to their required values. The following
variables can be used to set ``sysctl`` configuration specific types of hosts:

* ``seed_hypervisor_sysctl_parameters``
* ``seed_sysctl_parameters``
* ``compute_sysctl_parameters``
* ``controller_sysctl_parameters``
* ``monitoring_sysctl_parameters``
* ``storage_sysctl_parameters``

For example, to set the ``net.ipv4.ip_forward`` parameter to ``1`` on controllers:

.. code-block:: yaml
   :caption: ``controllers.yml``

   controller_sysctl_parameters:
     net.ipv4.ip_forward: 1

Disable cloud-init
==================

cloud-init is a popular service for performing system bootstrapping. If you are
not using cloud-init, this section can be skipped.

If using the seed's Bifrost service to provision the control plane hosts, the
use of cloud-init may be configured via the ``kolla_bifrost_dib_init_element``
variable.

cloud-init searches for network configuration in order of increasing
precedence; each item overriding the previous.  In some cases, on subsequent
boots cloud-init can automatically reconfigure network interfaces and cause
some issues in network configuration. To disable cloud-init from running after
the initial server bootstrapping, set ``disable_cloud_init`` to ``true`` in
``${KAYOBE_CONFIG_PATH}/overcloud.yml``.

Disable Glean
=============

The ``glean`` service can be used to perform system bootstrapping, serving a
similar role to ``cloud-init``. If you are not using ``glean``, this section
can be skipped.

If using the seed's Bifrost service to provision the control plane hosts, the
use of ``glean`` may be configured via the ``kolla_bifrost_dib_init_element``
variable.

After the initial server bootstrapping, the glean service can cause problems as
it attempts to enable all network interfaces, which can lead to timeouts while
booting. To avoid this, the ``glean`` service is disabled. Additionally, any
network interface configuration files generated by ``glean`` and not
overwritten by Kayobe are removed.

Timezone
========

The timezone can be configured via the ``timezone`` variable in
``${KAYOBE_CONFIG_PATH}/ntp.yml``. The value must be a valid Linux
timezone. For example:

.. code-block:: yaml
   :caption: ``ntp.yml``

   timezone: Europe/London

NTP
===

Network Time Protocol (NTP) may be configured via variables in
``${KAYOBE_CONFIG_PATH}/ntp.yml``. The list of NTP servers is
configured via ``ntp_config_server``, and by default the ``pool.ntp.org``
servers are used. A list of restrictions may be added via
``ntp_config_restrict``, and a list of interfaces to listen on via
``ntp_config_listen``. Other options and their default values may be found in
the `resmo.ntp <https://galaxy.ansible.com/resmo/ntp>`__ Ansible role.

.. code-block:: yaml
   :caption: ``ntp.yml``

   ntp_config_server:
     - 1.ubuntu.pool.ntp.org
     - 2.ubuntu.pool.ntp.org

   ntp_config_restrict:
     - '-4 default kod notrap nomodify nopeer noquery'

   ntp_config_listen:
     - eth0

The NTP service may be disabled as follows:

.. code-block:: yaml
   :caption: ``ntp.yml``

   ntp_service_enabled: false

Chrony
------

Kolla Ansible can deploy a chrony container. This is disabled by default in
Kayobe to avoid conflicting with the NTP daemon on the host.

To use the containerised chrony daemon and disable the host NTP daemon, set the
following in ``${KAYOBE_CONFIG_PATH}/kolla.yml``:

.. code-block:: yaml

   kolla_enable_chrony: true

.. _configuration-hosts-lvm:

LVM
===

Logical Volume Manager (LVM) physical volumes, volume groups, and logical
volumes may be configured via the ``lvm_groups`` variable. For convenience,
this is mapped to the following variables:

* ``seed_hypervisor_lvm_groups``
* ``seed_lvm_groups``
* ``compute_lvm_groups``
* ``controller_lvm_groups``
* ``monitoring_lvm_groups``
* ``storage_lvm_groups``

The format of these variables is as defined by the ``lvm_groups`` variable of
the `mrlesmithjr.manage-lvm
<https://galaxy.ansible.com/mrlesmithjr/manage-lvm>`__ Ansible role.

LVM for libvirt
---------------

LVM is not configured by default on the seed hypervisor. It is possible to
configure LVM to provide storage for a ``libvirt`` storage pool, typically
mounted at ``/var/lib/libvirt/images``.

To use this configuration, set the ``seed_hypervisor_lvm_groups`` variable to
``"{{ seed_hypervisor_lvm_groups_with_data }}"`` and provide a list of disks
via the ``seed_hypervisor_lvm_group_data_disks`` variable.

LVM for Docker
--------------

The default LVM configuration is optimised for the ``devicemapper`` Docker
storage driver, which requires a thin provisioned LVM volume. A second logical
volume is used for storing Docker volume data, mounted at
``/var/lib/docker/volumes``. Both logical volumes are created from a single
``data`` volume group.

To use this configuration, a list of disks must be configured via the following
variables:

* ``seed_lvm_group_data_disks``
* ``compute_lvm_group_data_disks``
* ``controller_lvm_group_data_disks``
* ``monitoring_lvm_group_data_disks``
* ``storage_lvm_group_data_disks``

For example, to configure two of the seed's disks for use by LVM:

.. code-block:: yaml
   :caption: ``seed.yml``

   seed_lvm_group_data_disks:
     - /dev/sdb
     - /dev/sdc

The Docker volumes LVM volume is assigned a size given by the following
variables, with a default value of 75% (of the volume group's capacity):

* ``seed_lvm_group_data_lv_docker_volumes_size``
* ``compute_lvm_group_data_lv_docker_volumes_size``
* ``controller_lvm_group_data_lv_docker_volumes_size``
* ``monitoring_lvm_group_data_lv_docker_volumes_size``
* ``storage_lvm_group_data_lv_docker_volumes_size``

If using a Docker storage driver other than ``devicemapper``, the remaining 25%
of the volume group can be used for Docker volume data. In this case, the LVM
volume's size can be increased to 100%:

.. code-block:: yaml
   :caption: ``controllers.yml``

   controller_lvm_group_data_lv_docker_volumes_size: 100%

If using a Docker storage driver other than ``devicemapper``, it is possible to
avoid using LVM entirely, thus avoiding the requirement for multiple disks. In
this case, set the appropriate ``<host>_lvm_groups`` variable to an empty list:

.. code-block:: yaml
   :caption: ``storage.yml``

   storage_lvm_groups: []

Custom LVM
----------

To define additional logical logical volumes in the default ``data`` volume
group, modify one of the following variables:

* ``seed_lvm_group_data_lvs``
* ``compute_lvm_group_data_lvs``
* ``controller_lvm_group_data_lvs``
* ``monitoring_lvm_group_data_lvs``
* ``storage_lvm_group_data_lvs``

Include the variable ``<host>_lvm_group_data_lv_docker_volumes`` in the list to
include the LVM volume for Docker volume data:

.. code-block:: yaml
   :caption: ``monitoring.yml``

   monitoring_lvm_group_data_lvs:
     - "{{ monitoring_lvm_group_data_lv_docker_volumes }}"
     - lvname: other-vol
       size: 1%
       create: true
       filesystem: ext4
       mount: true
       mntp: /path/to/mount

It is possible to define additional LVM volume groups via the following
variables:

* ``seed_lvm_groups_extra``
* ``compute_lvm_groups_extra``
* ``controller_lvm_groups_extra``
* ``monitoring_lvm_groups_extra``
* ``storage_lvm_groups_extra``

For example:

.. code-block:: yaml
   :caption: ``compute.yml``

   compute_lvm_groups_extra:
     - vgname: other-vg
       disks: /dev/sdb
       create: true
       lvnames:
         - lvname: other-vol
           size: 100%
           create: true
           mount: false

Alternatively, replace the entire volume group list via one of the
``<host>_lvm_groups`` variables to replace the default configuration with a
custom one.

.. code-block:: yaml
   :caption: ``controllers.yml``

   controller_lvm_groups:
     - vgname: only-vg
       disks: /dev/sdb
       create: true
       lvnames:
         - lvname: only-vol
           size: 100%
           create: true
           mount: false

Kolla-ansible bootstrap-servers
===============================

Kolla Ansible provides some host configuration functionality via the
``bootstrap-servers`` command, which may be leveraged by Kayobe. Due to the
bootstrapping nature of the command, Kayobe uses ``kayobe_ansible_user`` to
execute it, and uses the Kayobe remote Python virtual environment (or the
system Python interpreter if no virtual environment is in use).

See the `Kolla Ansible documentation
<https://docs.openstack.org/kolla-ansible/latest/reference/deployment-and-bootstrapping/bootstrap-servers.html>`__
for more information on the functions performed by this command, and how to
configure it.

Kolla-ansible Remote Virtual Environment
========================================

See :ref:`configuration-kolla-ansible-venv` for information about remote Python
virtual environments for Kolla Ansible.

.. _configuration-hosts-docker:

Docker Engine
=============

Docker engine configuration is applied by both Kayobe and Kolla Ansible (during
bootstrap-servers).

The ``docker_storage_driver`` variable sets the Docker storage driver, and by
default the ``devicemapper`` driver is used. If using this driver, see
:ref:`configuration-hosts-lvm` for information about configuring LVM for
Docker.

Various options are defined in ``${KAYOBE_CONFIG_PATH}/docker.yml``
for configuring the ``devicemapper`` storage.

A private Docker registry may be configured via ``docker_registry``, with a
Certificate Authority (CA) file configured via ``docker_registry_ca``.

To use one or more Docker Registry mirrors, use the ``docker_registry_mirrors``
variable.

If using an MTU other than 1500, ``docker_daemon_mtu`` can be used to configure
this. This setting does not apply to containers using ``net=host`` (as Kolla
Ansible's containers do), but may be necessary when building images.

Docker's live restore feature can be configured via
``docker_daemon_live_restore``, although it is disabled by default due to
issues observed.

Ceph Block Devices
==================

If using Kolla Ansible to deploy Ceph, some preparation of block devices is
required. The list of disks to configure for use by Ceph is specified via
``ceph_disks``. This is mapped to the following variables:

* ``compute_ceph_disks``
* ``controller_ceph_disks``
* ``storage_ceph_disks``

The format of the variable is a list of dict/mapping objects. Each mapping
should contain an ``osd`` item that defines the full path to a block device to
use for data. Optionally, each mapping may contain a ``journal`` item that
specifies the full path to a block device to use for journal data.

The following example defines two OSDs for use by controllers, one of which has
a journal:

.. code-block:: yaml
   :caption: ``controller.yml``

   controller_ceph_disks:
     - osd: /dev/sdb
     - osd: /dev/sdc
       journal: /dev/sdd
