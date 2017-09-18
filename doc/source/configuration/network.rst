=====================
Network Configuration
=====================

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
``inspection_gateway``
    IP address of the gateway for the hardware introspection network.
``neutron_gateway``
    IP address of the gateway for a neutron subnet based on this network.
``vlan``
    VLAN ID.
``mtu``
    Maximum Transmission Unit (MTU).
``routes``
    List of static IP routes. Each item should be a dict containing the
    items ``cidr`` and ``gateway``. ``cidr`` is the CIDR representation of the
    route's destination. ``gateway`` is the IP address of the next hop.
``physical_network``
    Name of the physical network on which this network exists. This aligns with
    the physical network concept in neutron.
``libvirt_network_name``
    A name to give to a Libvirt network representing this network on the seed
    hypervisor.

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
``bond_mode``
    For bond interfaces, the bond's mode, e.g. 802.3ad.
``bond_slaves``
    For bond interfaces, a list of names of network interfaces to act as slaves
    for the bond.
``bond_miimon``
    For bond interfaces, the time in milliseconds between MII link monitoring.

In order to provide flexibility in the system's network topology, Kayobe maps
the named networks to logical network roles.  A single named network may
perform multiple roles, or even none at all.  The available roles are:

``oob_oc_net_name``
    Name of the network used by the seed to access the out-of-band management
    controllers of the bare metal overcloud hosts.
``provision_oc_net_name``
    Name of the network used by the seed to provision the bare metal overcloud
    hosts.
``oob_wl_net_name``
    Name of the network used by the overcloud hosts to access the out-of-band
    management controllers of the bare metal workload hosts.
``provision_wl_net_name``
    Name of the network used by the overcloud hosts to provision the bare metal
    workload hosts.
``internal_net_name``
    Name of the network used to expose the internal OpenStack API endpoints.
``public_net_name``
    Name of the network used to expose the public OpenStack API endpoints.
``external_net_name``
    Name of the network used to provide external network access via Neutron.
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
=======

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
   public_net_name: external
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
   external_routes:
     - cidr 10.0.4.0/24
       gateway: 10.0.3.1

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
