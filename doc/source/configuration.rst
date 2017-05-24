=============
Configuration
=============

This section covers configuration of Kayobe.  As an Ansible-based project,
Kayobe is for the most part configured using YAML files.

Configuration Location
======================

Kayobe configuration is by default located in ``/etc/kayobe`` on the Ansible
control host. This location can be overridden to a different location to avoid
touching the system configuration directory by setting the environment variable
``KAYOBE_CONFIG_PATH``.  Similarly, kolla configuration on the Ansible control
host will by default be located in ``/etc/kolla`` and can be overridden via
``KOLLA_CONFIG_PATH``.

Configuration Directory Layout
==============================

The Kayobe configuration directory contains Ansible ``extra-vars`` files and
the Ansible inventory.  An example of the directory structure is as follows::

    extra-vars1.yml
    extra-vars2.yml
    inventory/
        group_vars/
            group1-vars
            group2-vars
        groups
        host_vars/
            host1-vars
            host2-vars
        hosts

Configuration Patterns
======================

Ansible's variable precedence rules are `fairly well documented
<http://docs.ansible.com/ansible/playbooks_variables.html#variable-precedence-where-should-i-put-a-variable>`_
and provide a mechanism we can use for providing site localisation and
customisation of OpenStack in combination with some reasonable default values.
For global configuration options, Kayobe typically uses the following patterns:

- Playbook group variables for the *all* group in
  ``<kayobe repo>/ansible/group_vars/all/*`` set **global defaults**.  These
  files should not be modified.
- Playbook group variables for other groups in
  ``<kayobe repo>/ansible/group_vars/<group>/*`` set **defaults for some subsets
  of hosts**.  These files should not be modified.
- Extra-vars files in ``${KAYOBE_CONFIG_PATH}/*.yml`` set **custom values
  for global variables** and should be used to apply global site localisation
  and customisation.  By default these variables are commented out.

Additionally, variables can be set on a per-host basis using inventory host
variables files in ``${KAYOBE_CONFIG_PATH}/inventory/host_vars/*``.  It should
be noted that variables set in extra-vars files take precedence over per-host
variables.

Configuring Kayobe
==================

The `kayobe-config <https://github.com/stackhpc/kayobe-config>`_ git repository
contains a Kayobe configuration directory structure and unmodified
configuration files.  This repository can be used as a mechanism for version
controlling Kayobe configuration.  As Kayobe is updated, the configuration
should be merged to incorporate any upstream changes with local modifications.

Alternatively, the baseline Kayobe configuration may be copied from a checkout
of the Kayobe repository to the Kayobe configuration path::

    $ cp -r etc/ ${KAYOBE_CONFIG_PATH:-/etc/kayobe}

Once in place, each of the YAML and inventory files should be manually
inspected and configured as required.

Inventory
----------

The inventory should contain the following hosts:

Control host
    This should be localhost and should be a member of the ``config-mgmt``
    group.
Seed hypervisor
    If provisioning a seed VM, a host should exist for the hypervisor that
    will run the VM, and should be a member of the ``seed-hypervisor`` group.
Seed
    The seed host, whether provisioned as a VM by Kayobe or externally managed,
    should exist in the ``seed`` group.

Cloud hosts and bare metal compute hosts are not required to exist in the
inventory.

Site Localisation and Customisation
-----------------------------------

Site localisation and customisation is applied using Ansible extra-vars files
in ``${KAYOBE_CONFIG_PATH}/*.yml``.

Encryption of Secrets
---------------------

Kayobe supports the use of `Ansible vault
<http://docs.ansible.com/ansible/playbooks_vault.html>`_ to encrypt sensitive
information in its configuration.  The ``ansible-vault`` tool should be used to
manage individual files for which encryption is required.  Any of the
configuration files may be encrypted.  Since encryption can make working with
Kayobe difficult, it is recommended to follow `best practice
<http://docs.ansible.com/ansible/playbooks_best_practices.html#best-practices-for-variables-and-vaults>`_,
adding a layer of indirection and using encryption only where necessary.

Network Configuration
---------------------

Kayobe provides a flexible mechanism for configuring the networks in a system.
Kayobe networks are assigned a name which is used as a prefix for variables
that define the network's attributes.  For example, to configure the ``cidr``
attribute of a network named ``arpanet``, we would use a variable named
``arpanet_cidr``.

Global network configuration is stored in
``${KAYOBE_CONFIG_PATH}/networks.yml``.  The following attributes are
supported:

``cidr``
    CIDR representation (<IP>/<prefix length>) of the network's IP subnet.
``allocation_pool_start``
    IP address of the start of Kayobe's allocation pool range.
``allocation_pool_end``
    IP address of the end of Kayobe's allocation pool range.
``inspection_allocation_pool_start``
    IP address of the start of ironic inspector's allocation pool range.
``inspection_allocation_pool_end``
    IP address of the end of ironic inspector's allocation pool range.
``neutron_allocation_pool_start``
    IP address of the start of neutron's allocation pool range.
``neutron_allocation_pool_end``
    IP address of the end of neutron's allocation pool range.
``gateway``
    IP address of the network's default gateway.
``vlan``
    VLAN ID.
``mtu``
    Maximum Transmission Unit (MTU).

IP addresses are allocated automatically by Kayobe from the
allocation pool
defined by ``allocation_pool_start`` and ``allocation_pool_end``.  The
allocated addresses are stored in
``${KAYOBE_CONFIG_PATH}/network-allocation.yml`` using the global per-network
attribute ``ips`` which maps Ansible inventory hostnames to allocated IPs.

Some network attributes are specific to a host's role in the system, and
these are stored in
``${KAYOBE_CONFIG_PATH}/inventory/group_vars/<group>/network-interfaces``.
The following attributes are supported:

``interface``
    The name of the network interface attached to the network.
``bridge_ports``
    For bridge interfaces, a list of names of network interfaces to add to the
    bridge.

In order to provide flexibility in the system's network topology, Kayobe maps
the named networks to logical network roles.  A single named network may
perform multiple roles, or even none at all.  The available roles are:

``provision_oc_net_name``
    Name of the network used by the seed to provision the bare metal overcloud
    hosts.
``provision_wl_net_name``
    Name of the network used by the overcloud hosts to provision the bare metal
    workload hosts.
``internal_net_name``
    Name of the network used to expose the internal OpenStack API endpoints.
``external_net_name``
    Name of the network used to expose the external OpenStack API endpoints and
    to provide external network access via Neutron.
``storage_net_name``
    Name of the network used to carry storage data traffic.
``storage_mgmt_net_name``
    Name of the network used to carry storage management traffic.
``inspection_net_name``
    Name of the network used to perform hardware introspection on the bare
    metal workload hosts.

These roles are configured in ``${KAYOBE_CONFIG_PATH}/networks.yml``.

Networks are mapped to hosts using the variable ``network_interfaces``.
Kayobe's playbook group variables define some sensible defaults for this
variable for hosts in the ``seed`` and ``controllers`` groups based on the
logical network roles.  These defaults can be extended by setting the variables
``seed_extra_network_interfaces`` and ``controller_extra_network_interfaces``
in ``${KAYOBE_CONFIG_PATH}/seed.yml`` and
``${KAYOBE_CONFIG_PATH}/controllers.yml`` respectively.

Example
^^^^^^^

In our example cloud we have three networks: ``management``, ``cloud`` and
``external``:

.. parsed-literal::

                 +------------+         +----------------+             +----------------+
                 |            |         |                +-+           |                +-+
                 |            |         |                | +-+         |  Bare metal    | +-+
                 |    Seed    |         |  Cloud hosts   | | |         |  compute hosts | | |
                 |            |         |                | | |         |                | | |
                 |            |         |                | | |         |                | | |
                 +-----+------+         +----------------+ | |         +----------------+ | |
                       |                 +-----------------+ |          +-----------------+ |
                       |                   +-----------------+            +-----------------+
                       |                        |  |  |                           |
                       |                        |  |  |                           |
                       |                        |  |  |                           |
                       |                        |  |  |                           |
   management +--------+------------------------+----------------------------------------------+
                                                   |  |                           |
   cloud      +------------------------------------+------------------------------+------------+
                                                      |
   external   +---------------------------------------+----------------------------------------+

The ``management`` network is used to access the servers' BMCs and by the seed
to provision the cloud hosts.  The ``cloud`` network carries all internal
control plane and storage traffic, and is used by the control plane to
provision the bare metal compute hosts.  Finally, the ``external`` network
links the cloud to the outside world.

We could describe such a network as follows:

.. code-block:: yaml
   :name: networks.yml
   :caption: ``networks.yml``

   ---
   # Network role mappings.
   provision_oc_net_name: management
   provision_wl_net_name: cloud
   internal_net_name: cloud
   external_net_name: external
   storage_net_name: cloud
   storage_mgmt_net_name: cloud
   inspection_net_name: cloud

   # management network definition.
   management_cidr: 10.0.0.0/24
   management_allocation_pool_start: 10.0.0.1
   management_allocation_pool_end: 10.0.0.127
   management_inspection_allocation_pool_start: 10.0.0.128
   management_inspection_allocation_pool_end: 10.0.0.254

   # cloud network definition.
   cloud_cidr: 10.0.1.0/23
   cloud_allocation_pool_start: 10.0.1.1
   cloud_allocation_pool_end: 10.0.1.127
   cloud_inspection_allocation_pool_start: 10.0.1.128
   cloud_inspection_allocation_pool_end: 10.0.1.255
   cloud_neutron_allocation_pool_start: 10.0.2.0
   cloud_neutron_allocation_pool_end: 10.0.2.254

   # external network definition.
   external_cidr: 10.0.3.0/24
   external_allocation_pool_start: 10.0.3.1
   external_allocation_pool_end: 10.0.3.127
   external_neutron_allocation_pool_start: 10.0.3.128
   external_neutron_allocation_pool_end: 10.0.3.254

We can map these networks to network interfaces on the seed and controller hosts:

.. code-block:: yaml
   :name: inventory/group_vars/seed/network-interfaces
   :caption: ``inventory/group_vars/seed/network-interfaces``

   ---
   management_interface: eth0

.. code-block:: yaml
   :name: inventory/group_vars/controllers/network-interfaces
   :caption: ``inventory/group_vars/controllers/network-interfaces``

   ---
   management_interface: eth0
   cloud_interface: breth1
   cloud_bridge_ports:
     - eth1
   external_interface: eth2

We have defined a bridge for the cloud network on the controllers as this will
allow it to be plugged into a neutron Open vSwitch bridge.

Kayobe will allocate IP addresses for the hosts that it manages:

.. code-block:: yaml
   :name: network-allocation.yml
   :caption: ``network-allocation.yml``

   ---
   management_ips:
     seed: 10.0.0.1
     control0: 10.0.0.2
     control1: 10.0.0.3
     control2: 10.0.0.4
   cloud_ips:
     control0: 10.0.1.1
     control1: 10.0.1.2
     control2: 10.0.1.3
   external_ips:
     control0: 10.0.3.1
     control1: 10.0.3.2
     control2: 10.0.3.3

Note that although this file does not need to be created manually, doing so
allows for a predictable IP address mapping which may be desirable in some
cases.
