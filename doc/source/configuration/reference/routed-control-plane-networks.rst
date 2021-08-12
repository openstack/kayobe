=============================
Routed Control Plane Networks
=============================

This section describes configuration for routed control plane networks. This is
an advanced concept and generally applies only to larger deployments that
exceed the reasonable size of a broadcast domain.

Concept
=======

Kayobe currently supports the definition of various different networks -
public, internal, tunnel, etc. These typically map to a VLAN or flat network,
with an associated IP subnet. When a cloud exceeds the reasonable size of a
single VLAN/subnet, or is physically distributed, this approach no longer
works.

One way to resolve this is to have multiple subnets that map to a single
logical network, and provide routing between them. This is a similar concept to
Neutron's :neutron-doc:`routed provider networks
<admin/config-routed-networks.html>`, but for the control plane networks.

Limitations
===========

There are currently a few limitations to using routed control plane networks.
Only the following networks have been tested:

* ``admin_oc``
* ``internal``
* ``tunnel``
* ``storage``
* ``storage_mgmt``

Additionally, only compute nodes and storage nodes have been tested with routed
control plane networks - controllers were always placed on the same set of
networks during testing.

Bare metal provisioning (of the overcloud or baremetal compute) has not been
tested with routed control plane networks, and would not be expected to work
without taking additional steps.

Configuration
=============

The approach to configuring Kayobe for routed control plane networks is as
follows:

* create groups in the inventory for the different sets of networks
* place hosts in the appropriate groups
* move ``vip_address`` and ``fqdn`` network attributes to :ref:`global
  variables <configuration-kolla-ansible-api-addresses>`
* move global network name configuration to group variables
* add new networks to configuration
* add network interface group variables

Example
=======

In this example, we initially have a number of different logical networks:

* ``public_0``

  * ``10.0.0.0/24``
  * VLAN 100

* ``internal_0``

  * ``10.0.1.0/24``
  * VLAN 101

* ``tunnel_0``

  * ``10.0.2.0/24``
  * VLAN 102

* ``storage_0``

  * ``10.0.3.0/24``
  * VLAN 103

* ``storage_mgmt_0``

  * ``10.0.4.0/24``
  * VLAN 104

Initially the following hosts are connected to these networks:

* ``controllers[0:2]``: ``public_0``, ``internal_0``, ``tunnel_0``,
  ``storage_0``
* ``compute[0:127]``: ``internal_0``, ``tunnel_0``, ``storage_0``
* ``storage[0:63]``: ``internal_0``, ``storage_0``, ``storage_mgmt_0``

Now consider that we wish to add 128 compute nodes and 64 storage nodes. This
would exceed size of the current subnets. We could increase the subnet sizes,
but there are good reasons to keep broadcast domains reasonably small.

To resolve this, we can add some more networks:

* ``internal_1``

  * ``10.1.1.0/24``
  * VLAN 111

* ``tunnel_1``

  * ``10.1.2.0/24``
  * VLAN 112

* ``storage_1``

  * ``10.1.3.0/24``
  * VLAN 113

* ``storage_mgmt_1``

  * ``10.1.4.0/24``
  * VLAN 114

The network must provide routes between the following networks:

* ``internal_0`` and ``internal_1``
* ``tunnel_0`` and ``tunnel_1``
* ``storage_0`` and ``storage_1``
* ``storage_mgmt_0`` and ``storage_mgmt_1``

Now we can connect the new hosts to these networks:

* ``compute[128:255]``: ``internal_1``, ``tunnel_1``, ``storage_1``
* ``storage[64:127]``: ``internal_1``, ``storage_1``, ``storage_mgmt_1``

Inventory
---------

To model this change we could use an inventory such as the following:

.. code-block:: console
   :caption: ``inventory/hosts``

   localhost ansible_connection=local

   [controllers]
   controller[0:2]

   [compute]
   compute[0:255]

   [storage]
   storage[0:127]

   [network-0]
   controller[0:2]

   [compute-network-0]
   compute[0:127]

   [storage-network-0]
   storage[0:63]

   [network-0:children]
   compute-network-0
   storage-network-0

   [network-1]

   [compute-network-1]
   compute[128:255]

   [storage-network-1]
   storage[64:127]

   [network-1:children]
   compute-network-1
   storage-network-1

Kolla API addresses
-------------------

Remove all variables defining ``vip_address`` or ``fqdn`` network attributes
from ``networks.yml``, and move the configuration to the :ref:`API address
variables <configuration-kolla-ansible-api-addresses>` in ``kolla.yml``.

Network names
-------------

To move global network name configuration to group variables, the following
variables should be commented out in ``networks.yml``:

.. code-block:: yaml
   :caption: ``networks.yml``

   #admin_oc_net_name:
   #internal_net_name:
   #tunnel_net_name:
   #storage_net_name:
   #storage_mgmt_net_name:

Create group variable files in ``inventory/group_vars/network-0`` and
``inventory/group_vars/network-1``:

.. code-block:: yaml
   :caption: ``inventory/group_vars/network-0``

   admin_oc_net_name: internal_0
   internal_net_name: internal_0
   tunnel_net_name: tunnel_0
   storage_net_name: storage_0
   storage_mgmt_net_name: storage_mgmt_0

.. code-block:: yaml
   :caption: ``inventory/group_vars/network-1``

   admin_oc_net_name: internal_1
   internal_net_name: internal_1
   tunnel_net_name: tunnel_1
   storage_net_name: storage_1
   storage_mgmt_net_name: storage_mgmt_1

Networks
--------

Now, ensure both sets of networks are defined in ``networks.yml``. Static
routes are added between the pairs of networks here, although these will depend
on your routing configuration.  Other network attributes may be necessary, we
are including ``cidr``, ``vlan`` and ``routes`` only here for brevity:

.. code-block:: yaml
   :caption: ``networks.yml``

   public_0_cidr: 10.0.0.0/24
   public_0_vlan: 100

   internal_0_cidr: 10.0.1.0/24
   internal_0_vlan: 101
   internal_0_routes:
     - cidr: "{{ internal_1_cidr }}"
       gateway: 10.0.1.1

   internal_1_cidr: 10.1.1.0/24
   internal_1_vlan: 111
   internal_1_routes:
     - cidr: "{{ internal_0_cidr }}"
       gateway: 10.1.1.1

   tunnel_0_cidr: 10.0.2.0/24
   tunnel_0_vlan: 102
   tunnel_0_routes:
     - cidr: "{{ tunnel_1_cidr }}"
       gateway: 10.0.2.1

   tunnel_1_cidr: 10.1.2.0/24
   tunnel_1_vlan: 112
   tunnel_1_routes:
     - cidr: "{{ tunnel_0_cidr }}"
       gateway: 10.1.2.1

   storage_0_cidr: 10.0.3.0/24
   storage_0_vlan: 103
   storage_0_routes:
     - cidr: "{{ storage_1_cidr }}"
       gateway: 10.0.3.1

   storage_1_cidr: 10.1.3.0/24
   storage_1_vlan: 113
   storage_1_routes:
     - cidr: "{{ storage_0_cidr }}"
       gateway: 10.1.3.1

   storage_mgmt_0_cidr: 10.0.4.0/24
   storage_mgmt_0_vlan: 104
   storage_mgmt_0_routes:
     - cidr: "{{ storage_mgmt_1_cidr }}"
       gateway: 10.0.4.1

   storage_mgmt_1_cidr: 10.1.4.0/24
   storage_mgmt_1_vlan: 114
   storage_mgmt_1_routes:
     - cidr: "{{ storage_mgmt_0_cidr }}"
       gateway: 10.1.4.1

Network interfaces
------------------

Since there are now differently named networks, the network interface variables
are named differently. This means that we must provide a group variables file
for each set of networks and each type of host. For example:

.. code-block:: yaml
   :caption: ``inventory/group_vars/compute-network-0/network-interfaces``

   internal_0_interface: eth0.101
   tunnel_0_interface: eth0.102
   storage_0_interface: eth0.103

.. code-block:: yaml
   :caption: ``inventory/group_vars/compute-network-1/network-interfaces``

   internal_1_interface: eth0.111
   tunnel_1_interface: eth0.112
   storage_1_interface: eth0.113

.. code-block:: yaml
   :caption: ``inventory/group_vars/storage-network-0/network-interfaces``

   internal_0_interface: eth0.101
   storage_0_interface: eth0.103
   storage_mgmt_0_interface: eth0.104

.. code-block:: yaml
   :caption: ``inventory/group_vars/storage-network-1/network-interfaces``

   internal_1_interface: eth0.111
   storage_1_interface: eth0.113
   storage_mgmt_1_interface: eth0.114

The normal interface configuration group variables files
``inventory/group_vars/compute/network-interfaces`` and
``inventory/group_vars/storage/network-interfaces`` should be
removed.

Group variables for controller network interfaces may be placed in
``inventory/group_vars/controllers/network-interfaces`` as normal.

Alternative approach
====================

There is an alternative approach which has not been tested, but may be of
interest. Rather than having differently named networks (e.g. ``internal_0``
and ``internal_1``), it should be possible to use the same name everywhere
(e.g. ``internal``), but define the network attributes in group variables. This
approach may be a little less verbose, and allows the same group variables file
to set the network interfaces as normal (e.g. via ``internal_interface``).
