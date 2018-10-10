=================================
Pike Series (3.x.y) Release Notes
=================================

Kayobe 3.1.0
============

Kayobe 3.1.0 was released on 22nd February 2018 and is based on the Pike
release of OpenStack.

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
* Adds support for deployment of storage hosts. These hosts should be added to
  the ``[storage]`` group.
* Adds support for the tagging of ceph disks.
* Adds support for post-deployment configuration of Grafana data sources and
  dashboards.

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
* Adds a workaround for an issue with CentOS cloud images 7.2 (1511) onwards,
  which have a bogus name server entry in /etc/resolv.conf, 10.0.2.3.
  Cloud-init only appends name server entries to this file, and will not remove
  this bogus entry. Typically this leads to a delay of around 30 seconds when
  connecting via SSH, due to a timeout in NSS. The workaround employed here is
  to remove this bogus entry from the image using virt-customize, if it exists.
  See https://bugs.centos.org/view.php?id=14369.
* Adds a group ``storage``, which used for deploy node with cinder-volume, LVM
  or ceph-osd. If you want to add these services to compute or control group,
  you need to override ``kolla_overcloud_inventory_storage_groups``.

Kayobe 3.0.0
============

Kayobe 3.0.0 was released on 20th September 2017.

Features
--------

* Adds support for the OpenStack Pike release.
* Adds support for saving overcloud service configuration to the Ansible
  control host.
* Adds support for generating overcloud service configuration, without applying
  it to the running system.

Upgrade Notes
-------------

See the upgrade notes for the pike release of the OpenStack services in use.
