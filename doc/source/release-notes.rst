=============
Release Notes
=============

In Development
==============

Features
--------

* Adds ``--interface-limit`` and ``--interface-description-limit`` arguments to
  the ``kayobe physical network configure`` command.  These arguments allow
  configuration to be limited to a subset of switch interfaces.
* Adds a ``--display`` argument to ``kayobe physical network configure``
  command.  This will output the candidate switch configuration without
  applying it.
* Adds support for configuration of custom fluentd filters, and additional
  config file templates for heat, ironic, keystone, magnum, murano, sahara, and
  swift in ``$KAYOBE_CONFIG_PATH/kolla/config/<component>/``.
* Adds support for specifying a local Yum mirror for package installation.
* Adds the command ``kayobe network connectivity check`` which can be used to
  verify network connectivity in the cloud hosts.
* Adds a variable ``kolla_nova_compute_ironic_host`` which may be used to set
  which hosts run the nova compute service for ironic. This may be used to
  avoid the experimental HA nova compute service for ironic, by specifying a
  single host.
* Adds support for deployment of virtualised compute hosts.  These hosts should
  be added to the ``[compute]`` group.
* Adds support for multiple external networks.  ``external_net_names`` should
  be a list of names of networks.
* Adds commands for management of baremetal compute nodes - ``kayobe baremetal
  compute inspect``, ``kayobe baremetal compute manage``, and ``kayobe
  baremetal compute provide``.
* Adds support for installation and use of a python virtual environment for
  remote execution of ansible modules, providing isolation from the system's
  python packages. This is enabled by setting a host variable,
  ``ansible_python_interpreter``, to the path to a python interpreter in a
  virtualenv, noting that Jinja2 templating is not supported for this variable.
* Adds support for configuration of a python virtual environment for remote
  execution of ansible modules in kolla-ansible, providing isolation from the
  system's python packages. This is enabled by setting the variable
  ``kolla_ansible_target_venv`` to a path to the virtualenv. The default for
  this variable is ``{{ virtualenv_path }}/kolla-ansible``.
* Adds tags to plays to support more fine grained configuration using the
  ``--tags`` argument.

Upgrade Notes
-------------

* Modifies the default value for ``inspector_manage_firewall`` from ``False``
  to ``True``.  Management of the firewall by ironic inspector is important to
  ensure that DHCP offers are not made to nodes during provisioning by
  inspector's DHCP server.
* Disables swift by default. The default value of ``kolla_enable_swift`` is
  now ``no``.
* The default list of neutron ML2 mechanism drivers
  (``kolla_neutron_ml2_mechanism_drivers``) has been removed in favour of using
  the defaults provided by kolla-ansible. Users relying on the default list of
  ``openvswitch`` and ``genericswitch`` should set the value explicitly.
* Adds a variable ``config_path``, used to set the base path to configuration
  on remote hosts. The default value is ``/opt/kayobe/etc``.
* Modifies the variable used to configure the kolla build configuration path
  from ``kolla_config_path`` to ``kolla_build_config_path``.  This provides a
  cleaner separation of kolla and kolla-ansible configuration options. The
  default value is ``{{ config_path }}/kolla``.
* Adds a group ``container-image-builders``, which defaults to containing the
  seed.  Hosts in this group will build container images. Previously, container
  images for the seed were built on the seed, and container images for the
  overcloud were built on the controllers.  The new design is intended to
  encourage a build, push, pull workflow.
* It is now possible to configure kayobe to use a virtual environment for
  remote execution of ansible modules.  If this is required, the following
  commands should be run in order to ensure that the virtual environments exist
  on the remote hosts::

      (kayobe) $ kayobe seed hypervisor host upgrade
      (kayobe) $ kayobe seed host upgrade
      (kayobe) $ kayobe overcloud host upgrade

* The default behaviour is now to configure kolla-ansible to use a virtual
  environment for remote execution of ansible modules. In order to ensure the
  virtual environment exists on the remote hosts, run the following commands::

      (kayobe) $ kayobe seed hypervisor host upgrade
      (kayobe) $ kayobe seed host upgrade
      (kayobe) $ kayobe overcloud host upgrade

  The previous behaviour of installing python dependencies directly to the host
  can be used by setting ``kolla_ansible_target_venv`` to ``None``.

Kayobe 3.0.0
============

Kayobe 3.0.0 was released on 20th September 2017.

Features
--------

* Adds support for the OpenStack Pike release.
* Adds support for saving overcloud service configuration to the ansible
  control host.
* Adds support for generating overcloud service configuration, without applying
  it to the running system.

Upgrade Notes
-------------

See the upgrade notes for the pike release of the OpenStack services in use.

Kayobe 2.0.0
============

Kayobe 2.0.0 was released on 15th September 2017.

Features
--------

* Adds support for configuration of networks for out-of-band management for
  the overcloud and control plane hosts via the ``oob_oc_net_name`` and
  ``oob_wl_net_name`` variables respectively.
* Adds support for configuration of a *seed hypervisor* host. This host runs
  the *seed VM*. Currently, configuration of host networking, NTP, and libvirt
  storage pools and networks is supported.
* Adds a ``base_path`` variable to simplify configuration of paths. This is
  used to set the default value of ``image_cache_path`` and
  ``source_checkout_path``. The default value of the base path may be set by
  the ``$KAYOBE_BASE_PATH`` environment variable.
* Adds a ``virtualenv_path`` variable to configure the path on which to create
  virtual environments.
* Uses the CentOS 7 cloud image for the seed VM by default.
* Adds a command to deprovision the seed VM, ``kayobe seed vm deprovision``.
* Adds support for configuration of Juniper switches.
* Adds support for bonded (LAG) host network interfaces.
* Adds support for the overlay docker storage driver on the seed and overcloud
  hosts.
* Improves the Vagrant development environment, and provides configuration for
  a single controller with a single network.
* Adds support for building customised Ironic Python Agent (IPA) deployment
  images using Diskimage Builder (DIB). These can be built using the commands
  ``kayobe seed deployment image build`` and
  ``kayobe overcloud deployment image build``.
* Adds a command to save overcloud introspection data,
  ``kayobe overcloud introspection data save``.
* Separates the external network into external and public networks. The public
  network carries public API traffic, and is configured via
  ``public_net_name``.
* Adds a ``network`` group, with networking and load balancing services moved
  to it. The group is a subgroup of the ``controllers`` group by default.
* Decomposes the overcloud inventory into top level, components, and services.
  This allows a deployer to customise their inventory at various levels, by
  providing a custom inventory template for one or more sections of the
  inventory.
* Adds support for configuration of sysctl parameters on the seed, seed
  hypervisor and overcloud hosts.
* Adds an **inspection-store** container for storage of workload hardware
  inspection data in environments without Swift.
* Adds configuration of gatewys in provisioning and inspection networks.
* Adds support for free-form configuration of Glance.
* Adds support for Ubuntu control hosts.
* Adds support for passing through host variables from kayobe to kolla-ansible.
  By default ``ansible_host``, ``ansible_port``, and
  ``ansible_ssh_private_key_file``.

Upgrade Notes
-------------

* It is no longer necessary to set the ``seed_vm_interfaces`` variable, as
  the seed VM's network interfaces are now determined by the standard
  ``seed_network_interfaces`` variable.
* If using a CentOS 7 cloud image for the seed VM, it is no longer necessary to
  set the ``seed_vm_root_image`` variable.
* The default value of ``kolla_enable_haproxy`` has been changed to ``True``.
* If using a custom inventory, a ``network`` group should be added to it. If
  the control hosts are providing networking services, then the ``network``
  group should be a subgroup of the ``controllers`` group.
* The ``overcloud_groups`` variable is now determined more intelligently, and
  it is generally no longer necessary to set it manually.
* The provisioning network is now used to access the TFTP server during
  workload hardware inspection.
* A default gateway may be advertised to compute nodes during workload
  inspection, allowing access to an ironic inspector API on the internal API
  network.

Kayobe 1.1.0
============

Kayobe 1.1.0 was released on 17th July 2017.

Features
--------

* Support static routes on control plane networks
* Improve documentation
* Initial support for in-development Pike release
* Upgrade kayobe control host & control plane
* Support overcloud service destroy command
* Support fluentd custom output configuration

Kayobe 1.0.0
============

1.0.0 is the first 'official' release of the Kayobe OpenStack deployment tool.
It was released on 29th June 2017.

Features
--------

This release includes the following features:

* Heavily automated using Ansible
* ``kayobe`` Command Line Interface (CLI) for cloud operators
* Deployment of a seed VM used to manage the OpenStack control plane
* Configuration of physical network infrastructure
* Discovery, introspection and provisioning of control plane hardware using
  OpenStack bifrost
* Deployment of an OpenStack control plane using OpenStack kolla-ansible
* Discovery, introspection and provisioning of bare metal compute hosts using
  OpenStack ironic and ironic inspector
* Containerised workloads on bare metal using OpenStack magnum
* Big data on bare metal using OpenStack sahara
