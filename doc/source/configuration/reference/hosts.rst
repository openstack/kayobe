.. _configuration-hosts:

==================
Host Configuration
==================

This section covers configuration of hosts. It does not cover configuration or
deployment of containers. Hosts that are configured by Kayobe include:

* Seed hypervisor (``kayobe seed hypervisor host configure``)
* Seed (``kayobe seed host configure``)
* Infra VMs (``kayobe infra vm host configure``)
* Overcloud (``kayobe overcloud host configure``)

Unless otherwise stated, all host configuration described here is applied to
each of these types of host.

.. seealso:: Ansible tags for limiting the scope of Kayobe commands are
             included under the relevant sections of this page
             (for more information see :ref:`usage-tags`).

Configuration Location
======================

Some host configuration options are set via global variables, and others have a
variable for each type of host. The latter variables are included in the
following files under ``${KAYOBE_CONFIG_PATH}``:

* ``seed-hypervisor.yml``
* ``seed.yml``
* ``compute.yml``
* ``controller.yml``
* ``infra-vms.yml``
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
*tags:*
  | ``ssh-known-host``

While strictly this configuration is applied to the Ansible control host
(``localhost``), it is applied during the ``host configure`` commands.
The ``ansible_host`` of each host is added as an SSH known host. This is
typically the host's IP address on the admin network (``admin_oc_net_name``),
as defined in ``${KAYOBE_CONFIG_PATH}/network-allocation.yml`` (see
:ref:`configuration-network-ip-allocation`).

Kayobe User Bootstrapping
=========================
*tags:*
  | ``kayobe-ansible-user``

Kayobe uses a user account defined by the ``kayobe_ansible_user`` variable (in
``${KAYOBE_CONFIG_PATH}/globals.yml``) for remote SSH access. By default, this
is ``stack``.

Typically, the image used to provision these hosts will not include this user
account, so Kayobe performs a bootstrapping step to create it, as a different
user. In cloud images, there is often a user named after the OS distro, e.g.
``centos`` or ``ubuntu``. This user defaults to the ``os_distribution``
variable, but may be set via the following variables:

* ``seed_hypervisor_bootstrap_user``
* ``seed_bootstrap_user``
* ``infra_vm_bootstrap_user``
* ``compute_bootstrap_user``
* ``controller_bootstrap_user``
* ``monitoring_bootstrap_user``
* ``storage_bootstrap_user``

For example, to set the bootstrap user for controllers to ``example-user``:

.. code-block:: yaml
   :caption: ``controllers.yml``

   controller_bootstrap_user: example-user

PyPI Mirror and proxy
=====================
*tags:*
  | ``pip``

Kayobe supports configuration of a PyPI mirror and/or proxy, via variables in
``${KAYOBE_CONFIG_PATH}/pip.yml``.
Mirror functionality is enabled by setting the ``pip_local_mirror`` variable to
``true`` and proxy functionality is enabled by setting ``pip_proxy`` variable
to a proxy URL.

Kayobe will generate configuration for:

* ``pip`` to use the mirror and proxy
* ``easy_install`` to use the mirror

for the list of users defined by ``pip_applicable_users`` (default
``kayobe_ansible_user`` and ``root``), in addition to the user used for Kolla
Ansible (``kolla_ansible_user``). The mirror URL is configured via
``pip_index_url``, and ``pip_trusted_hosts`` is a list of 'trusted' hosts, for
which SSL verification will be disabled.

For example, to configure use of the test PyPI mirror at
https://test.pypi.org/simple/:

.. code-block:: yaml
   :caption: ``pip.yml``

   pip_local_mirror: true
   pip_index_url: https://test.pypi.org/simple/

To configure use of the PyPI proxy:

.. code-block:: yaml
   :caption: ``pip.yml``

   pip_proxy: http://your_proxy_server:3128


Kayobe Remote Virtual Environment
=================================
*tags:*
  | ``kayobe-target-venv``

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
*tags:*
  | ``wipe-disks``

Using hosts that may have stale data on their disks could affect the deployment
of the cloud. This is not a configuration option, since it should only be
performed once to avoid losing useful data. It is triggered by passing the
``--wipe-disks`` argument to the ``host configure`` commands.

Users and Groups
================
*tags:*
  | ``users``

Linux user accounts and groups can be configured using the ``users_default``
variable in ``${KAYOBE_CONFIG_PATH}/users.yml``. The format of the list is
that used by the ``users`` variable of the `singleplatform-eng.users
<https://galaxy.ansible.com/singleplatform-eng/users>`__ role.  The following
variables can be used to set the users for specific types of hosts:

* ``seed_hypervisor_users``
* ``seed_users``
* ``infra_vm_users``
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

DNF Package Repositories
========================
*tags:*
  | ``dnf``

On CentOS, Kayobe supports configuration of package repositories via DNF, via
variables in ``${KAYOBE_CONFIG_PATH}/dnf.yml``.

Configuration of dnf.conf
-------------------------

Global configuration of DNF is stored in ``/etc/dnf/dnf.conf``, and options can
be set via the ``dnf_config`` variable. Options are added to the ``[main]``
section of the file. For example, to configure DNF to use a proxy server:

.. code-block:: yaml
   :caption: ``dnf.yml``

   dnf_config:
     proxy: https://proxy.example.com

CentOS and EPEL Mirrors
-----------------------

CentOS and EPEL mirrors can be enabled by setting ``dnf_use_local_mirror`` to
``true``.  CentOS repository mirrors are configured via the following
variables:

* ``dnf_centos_mirror_host`` (default ``mirror.centos.org``) is the mirror
  hostname.
* ``dnf_centos_mirror_directory`` (default ``centos``) is a directory on the
  mirror in which repositories may be accessed.

EPEL repository mirrors are configured via the following variables:

* ``dnf_epel_mirror_host`` (default ``download.fedoraproject.org``) is the
  mirror hostname.
* ``dnf_epel_mirror_directory`` (default ``pub/epel``) is a directory on the
  mirror in which repositories may be accessed.

For example, to configure CentOS and EPEL mirrors at mirror.example.com:

.. code-block:: yaml
   :caption: ``dnf.yml``

   dnf_use_local_mirror: true
   dnf_centos_mirror_host: mirror.example.com
   dnf_epel_mirror_host: mirror.example.com

Custom DNF Repositories
-----------------------

It is also possible to configure a list of custom DNF repositories via the
``dnf_custom_repos`` variable. The format is a dict/map, with repository names
mapping to a dict/map of arguments to pass to the Ansible ``yum_repository``
module.

For example, the following configuration defines a single DNF repository called
``widgets``.

.. code-block:: yaml
   :caption: ``dnf.yml``

   dnf_custom_repos:
     widgets:
       baseurl: http://example.com/repo
       file: widgets
       gpgkey: http://example.com/gpgkey
       gpgcheck: yes

Disabling EPEL
--------------

It is possible to disable the EPEL DNF repository by setting
``dnf_install_epel`` to ``false``.

DNF Automatic
-------------

DNF Automatic provides a mechanism for applying regular updates of packages.
DNF Automatic is disabled by default, and may be enabled by setting
``dnf_automatic_enabled`` to ``true``.

.. code-block:: yaml
   :caption: ``dnf.yml``

   dnf_automatic_enabled:  true

By default, only security updates are applied. Updates for all packages may be
installed by setting ``dnf_automatic_upgrade_type`` to ``default``. This may
cause the system to be less predictable as packages are updated without
oversight or testing.

Apt
===

On Ubuntu, Apt is used to manage packages and package repositories. Currently
Kayobe does not provide support for configuring custom Apt repositories.

Apt cache
---------

The Apt cache timeout may be configured via ``apt_cache_valid_time`` (in
seconds) in ``etc/kayobe/apt.yml``, and defaults to 3600.

Apt can be configured to use a proxy via ``apt_proxy_http`` and
``apt_proxy_https`` in ``etc/kayobe/apt.yml``. These should be set to the full
URL of the relevant proxy (e.g. ``http://squid.example.com:3128``).

SELinux
=======
*tags:*
  | ``disable-selinux``

.. note:: SELinux applies to CentOS systems only.

SELinux is not supported by Kolla Ansible currently, so it is disabled by
Kayobe. If necessary, Kayobe will reboot systems in order to apply a change to
the SELinux configuration. The timeout for waiting for systems to reboot is
``disable_selinux_reboot_timeout``. Alternatively, the reboot may be avoided by
setting ``disable_selinux_do_reboot`` to ``false``.

Network Configuration
=====================
*tags:*
  | ``network``

Configuration of host networking is covered in depth in
:ref:`configuration-network`.

Firewalld
=========
*tags:*
  | ``firewall``

.. note:: Firewalld is supported on CentOS systems only. Currently no
          firewall is supported on Ubuntu.

Firewalld can be used to provide a firewall on CentOS systems. Since the Xena
release, Kayobe provides support for enabling or disabling firewalld, as well
as defining zones and rules.

The following variables can be used to set whether to enable firewalld:

* ``seed_hypervisor_firewalld_enabled``
* ``seed_firewalld_enabled``
* ``infra_vm_firewalld_enabled``
* ``compute_firewalld_enabled``
* ``controller_firewalld_enabled``
* ``monitoring_firewalld_enabled``
* ``storage_firewalld_enabled``

When firewalld is enabled, the following variables can be used to configure a
list of zones to create. Each item is a dict containing a ``zone`` item:

* ``seed_hypervisor_firewalld_zones``
* ``seed_firewalld_zones``
* ``infra_vm_firewalld_zones``
* ``compute_firewalld_zones``
* ``controller_firewalld_zones``
* ``monitoring_firewalld_zones``
* ``storage_firewalld_zones``

The following variables can be used to set a default zone. The default is
unset, in which case the default zone will not be changed:

* ``seed_hypervisor_firewalld_default_zone``
* ``seed_firewalld_default_zone``
* ``infra_vm_firewalld_default_zone``
* ``compute_firewalld_default_zone``
* ``controller_firewalld_default_zone``
* ``monitoring_firewalld_default_zone``
* ``storage_firewalld_default_zone``

The following variables can be used to set a list of rules to apply. Each item
is a dict containing arguments to pass to the ``firewalld`` module. Arguments
are omitted if not provided, with the following exceptions: ``offline``
(default ``true``), ``permanent`` (default ``true``), ``state`` (default
``enabled``):

* ``seed_hypervisor_firewalld_rules``
* ``seed_firewalld_rules``
* ``infra_vm_firewalld_rules``
* ``compute_firewalld_rules``
* ``controller_firewalld_rules``
* ``monitoring_firewalld_rules``
* ``storage_firewalld_rules``

In the following example, firewalld is enabled on controllers. ``public`` and
``internal`` zones are created, with their default rules disabled. TCP port
8080 is open in the ``internal`` zone, and the ``http`` service is open in the
``public`` zone:

.. code-block:: yaml

   controller_firewalld_enabled: true

   controller_firewalld_zones:
     - zone: public
     - zone: internal

   controller_firewalld_rules:
     # Disable default rules in internal zone.
     - service: dhcpv6-client
       state: disabled
       zone: internal
     - service: samba-client
       state: disabled
       zone: internal
     - service: ssh
       state: disabled
       zone: internal
     # Disable default rules in public zone.
     - service: dhcpv6-client
       state: disabled
       zone: public
     - service: ssh
       state: disabled
       zone: public
     # Enable TCP port 8080 in internal zone.
     - port: 8080/tcp
       zone: internal
     # Enable the HTTP service in the public zone.
     - service: http
       zone: public

.. _configuration-hosts-tuned:

Tuned
=====
*tags:*
  | ``tuned``

.. note:: Tuned configuration only supports CentOS systems for now.

Built-in ``tuned`` profiles can be applied to hosts. The following variables
can be used to set a ``tuned`` profile to specific types of hosts:

* ``seed_hypervisor_tuned_active_builtin_profile``
* ``seed_tuned_active_builtin_profile``
* ``compute_tuned_active_builtin_profile``
* ``controller_tuned_active_builtin_profile``
* ``monitoring_tuned_active_builtin_profile``
* ``storage_tuned_active_builtin_profile``
* ``infra_vm_tuned_active_builtin_profile``

By default, Kayobe applies a ``tuned`` profile matching the role of each host
in the system:

* seed hypervisor: ``virtual-host``
* seed: ``virtual-guest``
* infrastructure VM: ``virtual-guest``
* compute: ``virtual-host``
* controllers: ``throughput-performance``
* monitoring: ``throughput-performance``
* storage: ``throughput-performance``

For example, to change the ``tuned`` profile of controllers to
``network-throughput``:

.. code-block:: yaml
   :caption: ``controllers.yml``

   controller_tuned_active_builtin_profile: network-throughput

Sysctls
=======
*tags:*
  | ``sysctl``

Arbitrary ``sysctl`` configuration can be applied to hosts. The variable format
is a dict/map, mapping parameter names to their required values. The following
variables can be used to set ``sysctl`` configuration specific types of hosts:

* ``seed_hypervisor_sysctl_parameters``
* ``seed_sysctl_parameters``
* ``infra_vm_sysctl_parameters``
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
*tags:*
  | ``disable-cloud-init``

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
*tags:*
  | ``disable-glean``

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
*tags:*
  | ``timezone``

The timezone can be configured via the ``timezone`` variable in
``${KAYOBE_CONFIG_PATH}/time.yml``. The value must be a valid Linux
timezone. For example:

.. code-block:: yaml
   :caption: ``time.yml``

   timezone: Europe/London

NTP
===
*tags:*
  | ``ntp``

Kayobe will configure `Chrony <https://chrony.tuxfamily.org/>`__ on all hosts in the
``ntp`` group. The default hosts in this group are::

.. code-block:: console

    [ntp:children]
    # Kayobe will configure Chrony on members of this group.
    seed
    seed-hypervisor
    overcloud

This provides a flexible way to opt in or out of having kayobe manage
the NTP service.

Variables
---------

Network Time Protocol (NTP) may be configured via variables in
``${KAYOBE_CONFIG_PATH}/time.yml``. The list of NTP servers is
configured via ``chrony_ntp_servers``, and by default the ``pool.ntp.org``
servers are used.

Internally, kayobe uses the the `mrlesmithjr.chrony
<https://galaxy.ansible.com/mrlesmithjr/chrony>`__ Ansible role. Rather than
maintain a mapping between the ``kayobe`` and ``mrlesmithjr.chrony`` worlds, all
variables are simply passed through. This means you can use all variables that
the role defines. For example to change ``chrony_maxupdateskew`` and override
the kayobe defaults for ``chrony_ntp_servers``:

.. code-block:: yaml
   :caption: ``time.yml``

   chrony_ntp_servers:
     - server: 0.debian.pool.ntp.org
       options:
         - option: iburst
         - option: minpoll
           val: 8
   chrony_maxupdateskew: 150.0

Software RAID
=============
*tags:*
  | ``mdadm``

While it is possible to use RAID directly with LVM, some operators may prefer
the userspace tools provided by ``mdadm`` or may have existing software RAID
arrays they want to manage with Kayobe.

Software RAID arrays may be configured via the ``mdadm_arrays`` variable. For
convenience, this is mapped to the following variables:

* ``seed_hypervisor_mdadm_arrays``
* ``seed_mdadm_arrays``
* ``infra_vm_mdadm_arrays``
* ``compute_mdadm_arrays``
* ``controller_mdadm_arrays``
* ``monitoring_mdadm_arrays``
* ``storage_mdadm_arrays``

The format of these variables is as defined by the ``mdadm_arrays`` variable of
the `mrlesmithjr.mdadm <https://galaxy.ansible.com/mrlesmithjr/mdadm>`__
Ansible role.

For example, to configure two of the seed's disks as a RAID1 ``mdadm`` array
available as ``/dev/md0``:

.. code-block:: yaml
   :caption: ``seed.yml``

   seed_mdadm_arrays:
     - name: md0
       devices:
         - /dev/sdb
         - /dev/sdc
       level: '1'
       state: present

.. _configuration-hosts-encryption:

Encryption
==========
*tags:*
  | ``luks``

Encrypted block devices may be configured via the ``luks_devices`` variable. For
convenience, this is mapped to the following variables:

* ``seed_hypervisor_luks_devices``
* ``seed_luks_devices``
* ``infra_vm_luks_devices``
* ``compute_luks_devices``
* ``controller_luks_devices``
* ``monitoring_luks_devices``
* ``storage_luks_devices``

The format of these variables is as defined by the ``luks_devices`` variable of
the `stackhpc.luks <https://galaxy.ansible.com/stackhpc/luks>`__
Ansible role.

For example, to encrypt the software raid device, ``/dev/md0``, on the seed, and make it
available as ``/dev/mapper/md0crypt``

.. code-block:: yaml
   :caption: ``seed.yml``

   seed_luks_devices:
     - name: md0crypt
       device: /dev/md0

..  note::

    It is not yet possible to encrypt the root device.

.. _configuration-hosts-lvm:

LVM
===
*tags:*
  | ``lvm``

Logical Volume Manager (LVM) physical volumes, volume groups, and logical
volumes may be configured via the ``lvm_groups`` variable. For convenience,
this is mapped to the following variables:

* ``seed_hypervisor_lvm_groups``
* ``seed_lvm_groups``
* ``infra_vm_lvm_groups``
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

.. note::

   In Train and earlier releases of Kayobe, the ``data`` volume group was
   always enabled by default.

If the ``devicemapper`` Docker storage driver is in use, the default LVM
configuration is optimised for it.  The ``devicemapper`` driver requires a thin
provisioned LVM volume. A second logical volume is used for storing Docker
volume data, mounted at ``/var/lib/docker/volumes``. Both logical volumes are
created from a single ``data`` volume group.

This configuration is enabled by the following variables, which default to
``true`` if the ``devicemapper`` driver is in use or ``false`` otherwise:

* ``compute_lvm_group_data_enabled``
* ``controller_lvm_group_data_enabled``
* ``seed_lvm_group_data_enabled``
* ``infra_vm_lvm_group_data_enabled``
* ``storage_lvm_group_data_enabled``

These variables can be set to ``true`` to enable the data volume group if the
``devicemapper`` driver is not in use. This may be useful where the
``docker-volumes`` logical volume is required.

To use this configuration, a list of disks must be configured via the following
variables:

* ``seed_lvm_group_data_disks``
* ``infra_vm_lvm_group_data_disks``
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
* ``infra_vm_lvm_group_data_lv_docker_volumes_size``
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
* ``infra_vm_lvm_group_data_lvs``
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
* ``infra_vm_lvm_groups_extra``
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

Kolla-Ansible bootstrap-servers
===============================

Kolla Ansible provides some host configuration functionality via the
``bootstrap-servers`` command, which may be leveraged by Kayobe.

See the :kolla-ansible-doc:`Kolla Ansible documentation
<reference/deployment-and-bootstrapping/bootstrap-servers.html>`
for more information on the functions performed by this command, and how to
configure it.

Note that from the Ussuri release, Kayobe creates a user account for Kolla
Ansible rather than this being done by Kolla Ansible during
``bootstrap-servers``. See :ref:`configuration-kolla-ansible-user-creation` for
details.

Kolla-Ansible Remote Virtual Environment
========================================
*tags:*
  | ``kolla-ansible``
  | ``kolla-target-venv``

See :ref:`configuration-kolla-ansible-venv` for information about remote Python
virtual environments for Kolla Ansible.

.. _configuration-hosts-docker:

Docker Engine
=============
*tags:*
  | ``docker``

Docker engine configuration is applied by both Kayobe and Kolla Ansible (during
bootstrap-servers).

The ``docker_storage_driver`` variable sets the Docker storage driver, and by
default the ``overlay2`` driver is used. If using the ``devicemapper`` driver,
see :ref:`configuration-hosts-lvm` for information about configuring LVM for
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
