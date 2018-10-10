==========================================
Ocata Series (1.x.y - 2.x.y) Release Notes
==========================================

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
* Adds support for Ubuntu Ansible control hosts.
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
  the Ansible control hosts are providing networking services, then the
  ``network`` group should be a subgroup of the ``controllers`` group.
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
* Upgrade kayobe Ansible control host & control plane
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
