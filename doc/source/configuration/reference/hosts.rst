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
``rocky`` or ``ubuntu``. This user defaults to the ``os_distribution``
variable, except for CentOS which uses ``cloud-user``, but may be set via the
following variables:

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

On CentOS and Rocky, Kayobe supports configuration of package repositories via
DNF, via variables in ``${KAYOBE_CONFIG_PATH}/dnf.yml``.

Configuration of dnf.conf
-------------------------

Global configuration of DNF is stored in ``/etc/dnf/dnf.conf``, and options can
be set via the ``dnf_config`` variable. Options are added to the ``[main]``
section of the file. For example, to configure DNF to use a proxy server:

.. code-block:: yaml
   :caption: ``dnf.yml``

   dnf_config:
     proxy: https://proxy.example.com

CentOS/Rocky and EPEL Mirrors
-----------------------------

CentOS/Rocky and EPEL mirrors can be enabled by setting
``dnf_use_local_mirror`` to ``true``. CentOS repository mirrors are configured
via the following variables:

* ``dnf_centos_mirror_host`` (default ``mirror.centos.org``) is the mirror
  hostname.
* ``dnf_centos_mirror_directory`` (default ``centos``) is a directory on the
  mirror in which repositories may be accessed.

Rocky repository mirrors are configured via the following variables:

* ``dnf_rocky_mirror_host`` (default ``dl.rockylinux.org``) is the mirror
  hostname
* ``dnf_rocky_mirror_directory`` (default ``pub/rocky``) is a directory on the
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

Enabling or disabling EPEL
--------------------------

Prior to the Yoga release, the EPEL DNF repository was enabled by default
(``dnf_install_epel: true``). Since Yoga, it is disabled by default
(``dnf_install_epel: false``).

Previously, EPEL was required to install some packages such as ``python-pip``,
however this is no longer the case.

It is possible to enable or disable the EPEL DNF repository by setting
``dnf_install_epel`` to ``true`` or ``false`` respectively.

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
*tags:*
  | ``apt``

On Ubuntu, Apt is used to manage packages and package repositories.

Apt cache
---------

The Apt cache timeout may be configured via ``apt_cache_valid_time`` (in
seconds) in ``etc/kayobe/apt.yml``, and defaults to 3600.

Apt proxy
---------

Apt can be configured to use a proxy via ``apt_proxy_http`` and
``apt_proxy_https`` in ``etc/kayobe/apt.yml``. These should be set to the full
URL of the relevant proxy (e.g. ``http://squid.example.com:3128``).

Apt configuration
-----------------

Arbitrary global configuration options for Apt may be defined via the
``apt_config`` variable in ``etc/kayobe/apt.yml`` since the Yoga release. The
format is a list, with each item mapping to a dict/map with the following
items:

* ``content``: free-form configuration file content
* ``filename``: name of a file in ``/etc/apt/apt.conf.d/`` in which to write
  the configuration

The default of ``apt_config`` is an empty list.

For example, the following configuration tells Apt to use 2 attempts when
downloading packages:

.. code-block:: yaml
   :caption: ``apt.yml``

   apt_config:
     - content: |
         Acquire::Retries 1;
       filename: 99retries

Apt repositories
----------------

Kayobe supports configuration of custom Apt repositories via the
``apt_repositories`` variable in ``etc/kayobe/apt.yml`` since the Yoga release.
The format is a list, with each item mapping to a dict/map with the following
items:

* ``name``: the ``<name>.sources`` filename part. Optional. Default is
  ``kayobe`` and the default filename is ``kayobe.sources``.
* ``types``: whitespace-separated list of repository types, e.g. ``deb`` or
  ``deb-src`` (optional, default is ``deb``)
* ``url``: URL of the repository
* ``suites``: whitespace-separated list of suites, e.g. ``noble`` (optional,
  default is ``ansible_facts.distribution_release``)
* ``components``: whitespace-separated list of components, e.g. ``main``
  (optional, default is ``main``)
* ``signed_by``: whitespace-separated list of names of GPG keyring files in
  ``apt_keys_path`` (optional, default is unset)
* ``architecture``: whitespace-separated list of architectures that will be used
  (optional, default is unset)
* ``trusted``: boolean value (optional, default is unset)

The default of ``apt_repositories`` is an empty list.

For example, the following configuration defines a single Apt repository:

.. code-block:: yaml
   :caption: ``apt.yml``

   apt_repositories:
     - types: deb
       url: https://example.com/repo
       suites: noble
       components: all

In the following example, the Ubuntu Noble 24.04 repositories are consumed from
a local package mirror. The ``apt_disable_sources_list`` variable is set to
``true``, which disables all repositories in ``/etc/apt/sources.list``,
including the default Ubuntu ones.

.. code-block:: yaml
   :caption: ``apt.yml``

   apt_repositories:
     - url: http://mirror.example.com/ubuntu/
       suites: noble noble-updates
       components: main restricted universe multiverse
     - url: http://mirror.example.com/ubuntu/
       suites: noble-security
       components: main restricted universe multiverse

   apt_disable_sources_list: true

Apt keys
--------

Some repositories may be signed by a key that is not one of Apt's trusted keys.
Kayobe avoids the use of the deprecated ``apt-key`` utility, and instead allows
keys to be downloaded to a directory. This enables repositories to use the
``SignedBy`` option to state that they are signed by a specific key. This
approach is more secure than using globally trusted keys.

Keys to be downloaded are defined by the ``apt_keys`` variable. The format is a
list, with each item mapping to a dict/map with the following items:

* ``url``: URL of key
* ``filename``: Name of a file in which to store the downloaded key in
  ``apt_keys_path``. The extension should be ``.asc`` for ASCII-armoured keys,
  or ``.gpg`` otherwise.

The default value of ``apt_keys`` is an empty list.

In the following example, a key is downloaded, and a repository is configured
that is signed by the key.

.. code-block:: yaml
   :caption: ``apt.yml``

   apt_keys:
     - url: https://example.com/GPG-key
       filename: example-key.asc

   apt_repositories:
     - types: deb
       url: https://example.com/repo
       suites: noble
       components: all
       signed_by: example-key.asc

Apt preferences
---------------

Arbitrary global preferences options for Apt may be defined via the
``apt_preferences`` variable in ``etc/kayobe/apt.yml``. The format is a list,
with each item mapping to a dict/map with the following items:

* ``content``: free-form preferences file content
* ``filename``: name of a file in ``/etc/apt/preferences.d/`` in which to
  write the configuration

The default of ``apt_preferences`` is an empty list.

For example, the following configuration tells Apt to only pin a specific
package from a custom repo, while preventing installing any other packages from
there:

.. code-block:: yaml
   :caption: ``apt.yml``

   apt_preferences:
     - content: |
         Package: *
         Pin: origin your.custom.repo
         Pin-Priority: 1

         Package: specific-package
         Pin: origin your.custom.repo
         Pin-Priority: 500
       filename: 99-pin-custom-repo

Apt auth configuration
----------------------

Some repositories may require authentication using HTTP basic auth. Apt
supports specifying credentials in URLs in ``sources.list`` files, but these
files must be world-readable. A more secure setup involves writing credentials
to `auth.conf
<https://manpages.ubuntu.com/manpages/noble/man5/apt_auth.conf.5.html>`__
files which can have more restrictive permissions.

Auth configuration is defined by the ``apt_auth`` variable. The format is a
list, with each item mapping to a dict/map with the following items:

* ``machine``: ``machine`` entry in the auth file
* ``login``: ``machine`` entry in the auth file
* ``password``: ``machine`` entry in the auth file
* ``filename``: Name of a file in ``/etc/apt/auth.conf.d`` in which to store
  the auth configuration. The extension should be ``.conf``.

The default value of ``apt_auth`` is an empty list.

In the following example, credentials are provided for package repositories at
apt.example.com.

.. code-block:: yaml
   :caption: ``apt.yml``

   apt_auth:
     - machine: apt.example.com
       login: my-username
       password: my-password
       filename: example.conf

Development tools
=================
*tags:*
  | ``dev-tools``

Development tools (additional OS packages) can be configured to be installed
on hosts. By default development tools are installed on all
``seed-hypervisor``, ``seed``, ``overcloud`` and ``infra-vms`` hosts.

The following variables can be used to set which packages to install:

* ``dev_tools_packages_default``: The list of packages installed by default.
  (default is: ``bash-completion``, ``tcpdump`` and ``vim``)
* ``dev_tools_packages_extra``: The list of additional packages installed
  alongside default packages. (default is an empty list)

In the following example, the list of default packages to be installed on all
hosts is modified to replace ``vim`` with ``emacs``. The ``bridge-utils``
package is added to all ``overcloud`` hosts:

.. code-block:: yaml
   :caption: ``dev-tools.yml``

   dev_tools_packages_default:
     - bash-completion
     - emacs
     - tcpdump

.. code-block:: yaml
   :caption: ``inventory/group_vars/overcloud/dev-tools``

   dev_tools_packages_extra:
     - bridge-utils

SELinux
=======
*tags:*
  | ``selinux``

.. note:: SELinux applies to CentOS and Rocky systems only.

SELinux is not supported by Kolla Ansible currently, so it is set to permissive
by Kayobe. If necessary, it can be configured to disabled by setting
``selinux_state`` to ``disabled``. Kayobe will reboot systems when required for
the SELinux configuration. The timeout for waiting for systems to reboot is
``selinux_reboot_timeout``. Alternatively, the reboot may be avoided by setting
``selinux_do_reboot`` to ``false``.

The ``selinux_update_kernel_param`` variable can be used to change the selinux
state set on the kernel command line; it takes a boolean value.

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

Firewalld can be used to provide a firewall on supported systems. Since the
Xena release, Kayobe provides support for enabling or disabling firewalld, as
well as defining zones and rules.
Since the Zed 13.0.0 release, Kayobe added support for configuring firewalld on
Ubuntu systems.

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

UFW
===
*tags:*
  | ``firewall``

Configuration of Uncomplicated Firewall (UFW) on Ubuntu hosts is currently not
supported. Instead, UFW is disabled. Since Yoga, this may be avoided as
follows:

.. code-block:: yaml

   ufw_enabled: true

Note that despite the name, this will not actively enable UFW. It may do so in
the future.

.. _configuration-hosts-tuned:

Tuned
=====
*tags:*
  | ``tuned``

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

IP routing and Source NAT
=========================
*tags:*
  | ``ip-routing``
  | ``snat``

IP routing and source NAT (SNAT) can be configured on the seed host, which
allows it to be used as a default gateway for overcloud hosts. This is disabled
by default since the Xena 11.0.0 release, and may be enabled by setting
``seed_enable_snat`` to ``true`` in ``${KAYOBE_CONFIG_PATH}/seed.yml``.

The seed-hypervisor host also can be configured the same way to be used as a
default gateway. This is disabled by default too, and may be enabled by setting
``seed_hypervisor_enable_snat`` to ``true``
in ``${KAYOBE_CONFIG_PATH}/seed-hypervisor.yml``.

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
``ntp`` group. The default hosts in this group are:

.. code-block:: ini

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

Internally, kayobe uses the `mrlesmithjr.chrony
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
the `mrlesmithjr.manage_lvm
<https://galaxy.ansible.com/mrlesmithjr/manage_lvm>`__ Ansible role.

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

A logical volume for storing Docker volume data, mounted at ``/var/lib/docker/volumes``
can optionally be created. The logical volume is created in volume group called data.

This configuration is enabled by the following variables, which default to
``false``:

* ``compute_lvm_group_data_enabled``
* ``controller_lvm_group_data_enabled``
* ``seed_lvm_group_data_enabled``
* ``infra_vm_lvm_group_data_enabled``
* ``storage_lvm_group_data_enabled``

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

You can control the amount of storage assigned to the docker volumes LV by
using the following variable.

.. code-block:: yaml
   :caption: ``controllers.yml``

   controller_lvm_group_data_lv_docker_volumes_size: 100%

It is possible to avoid using LVM entirely, thus avoiding the requirement for
multiple disks. In this case, set the appropriate ``<host>_lvm_groups``
variable to an empty list:

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
       disks:
         - /dev/sdb
       create: true
       lvnames:
         - lvname: other-vol
           size: 100%FREE
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

Kolla-Ansible Remote Virtual Environment
========================================
*tags:*
  | ``kolla-ansible``
  | ``kolla-target-venv``

See :ref:`configuration-kolla-ansible-venv` for information about remote Python
virtual environments for Kolla Ansible.

.. _configuration-hosts-container-engine:

Container Engine
================
*tags:*
  | ``docker``
  | ``podman``

Kayobe supports the following container engines:

- Podman
- Docker

The container engine can be configured by setting ``container_engine`` in
``container-engine.yml``. The default container engine is ``docker``. For
example, to use podman:

.. code-block:: yaml
   :caption: ``container-engine.yml``

   container_engine: podman

Podman
------

The ``openstack.kolla.podman`` role is used to configure Podman. Please refer
to the `role defaults
<https://github.com/openstack/ansible-collection-kolla/blob/master/roles/podman/defaults/main.yml>`__
for a list of configuration options (making sure to switch to correct branch).
These may be overridden via variables in the Ansible inventory or by using
extra vars, For example, in ``container-engine.yml``:

.. code-block:: yaml
   :caption: ``container-engine.yml``

   podman_storage_driver: overlay

A private image registry may be configured via ``podman_registry``. If using an
insecure (HTTP) registry, set ``podman_registry_insecure`` to ``true``.

Docker
------

The ``docker_storage_driver`` variable sets the Docker storage driver, and by
default the ``overlay2`` driver is used. See :ref:`configuration-hosts-lvm` for
information about configuring LVM for Docker.

If using an insecure (HTTP) registry, set ``docker_registry_insecure`` to
``true``.

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

Compute libvirt daemon
======================
*tags:*
  | ``libvirt-host``

.. note::

   This section is about the libvirt daemon on compute nodes, as opposed to the
   seed hypervisor.

Since Yoga, Kayobe provides support for deploying and configuring a libvirt
host daemon, as an alternative to the ``nova_libvirt`` container support by
Kolla Ansible. The host daemon is not used by default, but it is possible to
enable it by setting ``kolla_enable_nova_libvirt_container`` to ``false`` in
``$KAYOBE_CONFIG_PATH/kolla.yml``.

Migration of hosts from a containerised libvirt to host libvirt is currently
not supported.

The following options are available in ``$KAYOBE_CONFIG_PATH/compute.yml`` and
are relevant only when using the libvirt daemon rather than the
``nova_libvirt`` container:

``compute_libvirt_enabled``
    Whether to enable a host libvirt daemon. Default is true if
    ``kolla_enable_nova`` is ``true`` and
    ``kolla_enable_nova_libvirt_container`` is ``false``.
``compute_libvirt_conf_default``
    A dict of default configuration options to write to
    ``/etc/libvirt/libvirtd.conf``.
``compute_libvirt_conf_extra``
    A dict of additional configuration options to write to
    ``/etc/libvirt/libvirtd.conf``.
``compute_libvirt_conf``
    A dict of configuration options to write to ``/etc/libvirt/libvirtd.conf``.
    Default is a combination of ``compute_libvirt_conf_default`` and
    ``compute_libvirt_conf_extra``.
``compute_libvirtd_log_level``
    Numerical log level for libvirtd. Default is 3.
``compute_qemu_conf_default``
    A dict of default configuration options to write to
    ``/etc/libvirt/qemu.conf``.
``compute_qemu_conf_extra``
    A dict of additional configuration options to write to
    ``/etc/libvirt/qemu.conf``.
``compute_qemu_conf``
    A dict of configuration options to write to ``/etc/libvirt/qemu.conf``.
    Default is a combination of ``compute_qemu_conf_default`` and
    ``compute_qemu_conf_extra``.
``compute_libvirt_enable_sasl``
    Whether to enable libvirt SASL authentication.  Default is the same as
    ``compute_libvirt_tcp_listen``.
``compute_libvirt_sasl_password``
    libvirt SASL password. Default is unset. This must be defined when
    ``compute_libvirt_enable_sasl`` is ``true``.
``compute_libvirt_enable_tls``
    Whether to enable a libvirt TLS listener. Default is false.
``compute_libvirt_ceph_repo_install``
    Whether to install a Ceph package repository on CentOS and Rocky hosts.
    Default is ``true``.
``compute_libvirt_ceph_repo_release``
    Ceph package repository release to install on CentOS and Rocky hosts when
    ``compute_libvirt_ceph_repo_install`` is ``true``. Default is ``squid``.

Example: custom libvirtd.conf
-----------------------------

To customise the libvirt daemon log output to send level 3 to the journal:

.. code-block:: yaml
   :caption: ``compute.yml``

   compute_libvirt_conf_extra:
     log_outputs: "3:journald"

Example: custom qemu.conf
-------------------------

To customise QEMU to avoid adding timestamps to logs:

.. code-block:: yaml
   :caption: ``compute.yml``

   compute_qemu_conf_extra:
     log_timestamp: 0

Example: SASL
-------------

SASL authentication is enabled by default.  This provides authentication for
TCP and TLS connections to the libvirt API. A password is required, and should
be encrypted using Ansible Vault.

.. code-block:: yaml
   :caption: ``compute.yml``

   compute_libvirt_sasl_password: !vault |
     $ANSIBLE_VAULT;1.1;AES256
     63363937303539373738356236393563636466313130633435353933613637343231303836343933
     3463623265653030323665383337376462363434396361320a653737376237353261303066616637
     66613562316533313632613433643537346463303363376664396661343835373033326261383065
     3731643633656636360a623534313665343066656161333866613338313266613465336332376463
     3234

Example: enabling libvirt TLS listener
--------------------------------------

To enable the libvirt TLS listener:

.. code-block:: yaml
   :caption: ``compute.yml``

   compute_libvirt_enable_tls: true

When the TLS listener is enabled, it is necessary to provide client, server and
CA certificates. The following files should be provided:

``cacert.pem``
    CA certificate used to sign client and server certificates.
``clientcert.pem``
    Client certificate.
``clientkey.pem``
    Client key.
``servercert.pem``
    Server certificate.
``serverkey.pem``
    Server key.

It is recommended to encrypt the key files using Ansible Vault.

The following paths are searched for these files:

* ``$KAYOBE_CONFIG_PATH/certificates/libvirt/{{ inventory_hostname }}/``
* ``$KAYOBE_CONFIG_PATH/certificates/libvirt/``

In this way, certificates may be generated for each host, or shared using
wildcard certificates.

If using Kayobe environments, certificates in the environment take precedence.

Kayobe makes the CA certificate and client certificate and key available to
Kolla Ansible, for use by the ``nova_compute`` service.

Example: disabling Ceph repository installation
-----------------------------------------------

On CentOS and Rocky hosts, a CentOS Storage SIG Ceph repository is installed
that provides more recent Ceph libraries than those available in CentOS/Rocky
AppStream.  This may be necessary when using Ceph for Cinder volumes or Nova
ephemeral block devices. In some cases, such as when using local package
mirrors, the upstream repository may not be appropriate. The installation of
the repository may be disabled as follows:

.. code-block:: yaml
   :caption: ``compute.yml``

   compute_libvirt_ceph_repo_install: false

Example: installing additional packages
---------------------------------------

In some cases it may be useful to install additional packages on compute hosts
for use by libvirt. The `stackhpc.libvirt-host
<https://galaxy.ansible.com/stackhpc/libvirt-host>`__ Ansible role supports
this via the ``libvirt_host_extra_daemon_packages`` variable. The variable
should be defined via group variables in the Ansible inventory, to avoid
applying the change to the seed hypervisor. For example, to install the
``trousers`` package used for accessing TPM hardware:

.. code-block:: yaml
   :caption: ``inventory/group_vars/compute/libvirt``

   libvirt_host_extra_daemon_packages:
     - trousers

Swap
====

*tags:*
  | ``swap``

Swap files and devices may be configured via the ``swap`` variable. For
convenience, this is mapped to the following variables:

* ``seed_swap``
* ``seed_hypervisor_swap``
* ``infra_vm_swap``
* ``compute_swap``
* ``controller_swap``
* ``monitoring_swap``
* ``storage_swap``

The format is a list, with each item mapping to a dict/map. For a swap device,
the following item should be present:

* ``device``: Absolute path to a swap device.

For a swap file, the following items should be present:

* ``path``: Absolute path to a swap file to create.
* ``size_mb``: Size of the swap file in MiB.

The default value of ``swap`` is an empty list.

Example: enabling swap using a swap partition
---------------------------------------------

The following example defines a swap device using an existing ``/dev/sda3``
partition on controller hosts:

.. code-block:: yaml
   :caption: ``controllers.yml``

   controller_swap:
     - device: /dev/sda3

Example: enabling swap using a swap file
----------------------------------------

The following example defines a 1GiB swap file that will be created at
``/swapfile`` on compute hosts:

.. code-block:: yaml
   :caption: ``compute.yml``

   compute_swap:
     - path: /swapfile
       size_mb: 1024

AppArmor for the libvirt container
==================================
*tags:*
  | ``apparmor-libvirt``

.. note::

   Prior to the Yoga release, this was handled by the ``kolla-ansible
   bootstrap-servers`` command.

On Ubuntu systems running the ``nova_libvirt`` Kolla container, AppArmor rules
for libvirt are disabled.

Adding entries to /etc/hosts
============================
*tags:*
  | ``etc-hosts``

.. note::

   Prior to the Yoga release, this was handled by the ``kolla-ansible
   bootstrap-servers`` command.

Since Yoga, Kayobe adds entries to ``/etc/hosts`` for all hosts in the
``overcloud`` group.  The entries map the hostname and FQDN of a host to its IP
address on the internal API network. This may be avoided as follows:

.. code-block:: yaml

   customize_etc_hosts: false

By default, each host gets an entry for every other host in the ``overcloud``
group by default. The list of hosts that will be added may be customised:

.. code-block:: yaml

   etc_hosts_hosts: "{{ groups['compute'] }}"

It should be noted that this functionality requires facts to be populated for
all hosts that will be added to any ``/etc/hosts`` file. When using the
``--limit`` argument, Kayobe will gather facts for all hosts without facts,
including those outside of the limit. Enabling fact caching for Kayobe may
reduce the impact of this. This fact gathering process may be avoided as
follows:

.. code-block:: yaml

   etc_hosts_gather_facts: false

Installing packages required by Kolla Ansible
=============================================
*tags:*
  | ``kolla-packages``

.. note::

   Prior to the Yoga release, this was handled by the ``kolla-ansible
   bootstrap-servers`` command.

A small number of packages are required to be installed on the hosts for Kolla
Ansible and the services that it deploys, while some others must be removed.

Logging
=======
*tags:*
  | ``logging``

Kayobe will configure persistent logging for nodes in the following ansible groups:

- seed-hypervisor
- seed
- overcloud
- infra-vms

This means that the systemd journal will be written to local storage (instead
of to memory) and will allow you to view the journal from previous boots. The
storage limit defaults to 10% of the filesystem with a 4GiB hard limit (when
using journald defaults). See `journald documentation
<https://www.freedesktop.org/software/systemd/man/latest/journald.conf.html#SystemMaxUse=>`__
for more details.

Should you wish to disable this feature, you can set ``journald_storage`` to
``volatile``.
