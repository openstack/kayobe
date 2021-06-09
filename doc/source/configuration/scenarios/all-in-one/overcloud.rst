=========
Overcloud
=========

.. note::
   This documentation is intended as a walk through of the configuration
   required for a minimal all-in-one overcloud host. If you are looking
   for an all-in-one environment for test or development, see
   :ref:`contributor-automated`.

Installation
============

SSH to the overcloud machine, then follow the instructions in
:doc:`/installation` to set up an Ansible control host environment.
Typically this would be on a separate machine, but here we are keeping things
as simple as possible.

Configuration
=============

Clone the `kayobe-config <https://opendev.org/openstack/kayobe-config>`_
git repository, using the correct branch for the release you are deploying.  In
this example we will use the |current_release_git_branch_name| branch.

.. parsed-literal::

   cd <base path>/src
   git clone \https://opendev.org/openstack/kayobe-config.git -b |current_release_git_branch_name|
   cd kayobe-config

This repository is bare, and needs to be populated.  The repository includes an
example inventory, which should be removed:

.. code-block:: console

   git rm etc/kayobe/inventory/hosts.example

Create an Ansible inventory file and add the machine to it. In this example our
machine is called ``controller0``. Since this is an all-in-one environment, we
add the controller to the ``compute`` group, however normally dedicated
compute nodes would be used.

.. code-block:: yaml
   :caption: ``etc/kayobe/inventory/hosts``

   # This host acts as the configuration management Ansible control host. This must be
   # localhost.
   localhost ansible_connection=local

   [controllers]
   controller0

   [compute:children]
   controllers

The ``inventory`` directory also contains group variables for network interface
configuration. In this example we will assume that the machine has a single
network interface called ``eth0``. We will create a bridge called ``breth0``
and plug ``eth0`` into it. This allows us to move the host's IP address to the
bridge, and pass traffic through to an Open vSwitch bridge for Neutron. Replace
the network interface configuration for the ``controllers`` group with the
following, replacing ``eth0`` with an appropriate interface:

.. code-block:: yaml
   :caption: ``etc/kayobe/inventory/group_vars/controllers/network-interfaces``

   # Controller interface on all-in-one network.
   aio_interface: breth0

   # Interface eth0 is plugged into the all-in-one network bridge.
   aio_bridge_ports:
     - eth0

In this scenario a single network called ``aio`` is used. We must therefore set
the name of the default controller networks to ``aio``:

.. code-block:: yaml
   :caption: ``etc/kayobe/networks.yml``

   ---
   # Kayobe network configuration.

   ###############################################################################
   # Network role to network mappings.

   # Map all networks to the all-in-one network.

   # Name of the network used for admin access to the overcloud
   #admin_oc_net_name:
   admin_oc_net_name: aio

   # Name of the network used by the seed to manage the bare metal overcloud
   # hosts via their out-of-band management controllers.
   #oob_oc_net_name:

   # Name of the network used by the seed to provision the bare metal overcloud
   # hosts.
   #provision_oc_net_name:

   # Name of the network used by the overcloud hosts to manage the bare metal
   # compute hosts via their out-of-band management controllers.
   #oob_wl_net_name:

   # Name of the network used by the overcloud hosts to provision the bare metal
   # workload hosts.
   #provision_wl_net_name:

   # Name of the network used to expose the internal OpenStack API endpoints.
   #internal_net_name:
   internal_net_name: aio

   # List of names of networks used to provide external network access via
   # Neutron.
   # Deprecated name: external_net_name
   # If external_net_name is defined, external_net_names will default to a list
   # containing one item, external_net_name.
   #external_net_names:
   external_net_names:
     - aio

   # Name of the network used to expose the public OpenStack API endpoints.
   #public_net_name:
   public_net_name: aio

   # Name of the network used by Neutron to carry tenant overlay network traffic.
   #tunnel_net_name:
   tunnel_net_name: aio

   # Name of the network used to carry storage data traffic.
   #storage_net_name:
   storage_net_name: aio

   # Name of the network used to carry storage management traffic.
   #storage_mgmt_net_name:
   storage_mgmt_net_name: aio

   # Name of the network used to carry swift storage data traffic.
   #swift_storage_net_name:

   # Name of the network used to carry swift storage replication traffic.
   #swift_storage_replication_net_name:

   # Name of the network used to perform hardware introspection on the bare metal
   # workload hosts.
   #inspection_net_name:

   # Name of the network used to perform cleaning on the bare metal workload
   # hosts
   #cleaning_net_name:

   ###############################################################################
   # Network definitions.

   <omitted for clarity>

Next the ``aio`` network must be defined. This is done using the various
attributes described in :doc:`/configuration/reference/network`. These
values should be adjusted to match the environment. The ``aio_vip_address``
variable should be a free IP address in the same subnet for the virtual IP
address of the OpenStack API.

.. code-block:: yaml
   :caption: ``etc/kayobe/networks.yml``

   <omitted for clarity>

   ###############################################################################
   # Network definitions.

   # All-in-one network.
   aio_cidr: 192.168.33.0/24
   aio_gateway: 192.168.33.1
   aio_vip_address: 192.168.33.2

   ###############################################################################
   # Network virtual patch link configuration.

   <omitted for clarity>

Kayobe will automatically allocate IP addresses. In this case however, we want
to ensure that the host uses the same IP address it has currently, to avoid
loss of connectivity. We can do this by populating the network allocation file.
Use the correct hostname and IP address for your environment.

.. code-block:: yaml
   :caption: ``etc/kayobe/network-allocation.yml``

   ---
   aio_ips:
     controller0: 192.168.33.3

The default OS distribution in Kayobe is CentOS. If using an Ubuntu host, set
the ``os_distribution`` variable in ``etc/kayobe/globals.yml`` to ``ubuntu``.

.. code-block:: yaml
   :caption: ``etc/kayobe/globals.yml``

   ---
   os_distribution: "ubuntu"

In a development environment, we may wish to tune some Kolla Ansible variables.
Using QEMU as the virtualisation type will be necessary if KVM is not
available. Reducing the number of OpenStack service workers helps to avoid
using too much memory.

.. code-block:: yaml
   :caption: ``etc/kayobe/kolla/globals.yml``

   ---
   # Most development environments will use nested virtualisation, and we can't
   # guarantee that nested KVM support is available. Use QEMU as a lowest common
   # denominator.
   nova_compute_virt_type: qemu

   # Reduce the control plane's memory footprint by limiting the number of worker
   # processes to one per-service.
   openstack_service_workers: "1"

Activate the Kayobe configuration environment:

.. code-block:: console

   source kayobe-env

Bootstrap the control host:

.. code-block:: console

   kayobe control host bootstrap

Configure the overcloud host:

.. code-block:: console

   kayobe overcloud host configure

The previous command is likely to reboot the machine to disable SELinux. SSH
again when it has booted, activate the Kayobe environment and complete the host
configuration:

.. code-block:: console

   kayobe overcloud host configure

Pull overcloud container images:

.. code-block:: console

   kayobe overcloud container image pull

Deploy overcloud services:

.. code-block:: console

   kayobe overcloud service deploy

There is an issue with Docker where it changes the default policy of the
``FORWARD`` chain to ``DROP``. This prevents traffic traversing the bridge.
Revert this change:

.. code-block:: console

   sudo iptables -P FORWARD ACCEPT

The ``init-runonce`` script provided by Kolla Ansible (not for production) can
be used to setup some resources for testing. This includes:

* some flavors
* a `cirros <https://download.cirros-cloud.net/>`_ image
* an external network
* a tenant network and router
* security group rules for ICMP, SSH, and TCP ports 8000 and 8080
* an SSH key
* increased quotas

For the external network, use the same subnet as before, with an allocation
pool range containing free IP addresses:

.. code-block:: console

   pip install python-openstackclient
   export EXT_NET_CIDR=192.168.33.0/24
   export EXT_NET_GATEWAY=192.168.33.1
   export EXT_NET_RANGE="start=192.168.33.4,end=192.168.33.254"
   source "${KOLLA_CONFIG_PATH:-/etc/kolla}/admin-openrc.sh"
   ${KOLLA_SOURCE_PATH}/tools/init-runonce

Create a server instance, assign a floating IP address, and check that it is
accessible. The floating IP address is displayed after it is created, in this
example it is ``192.168.33.4``:

.. code-block:: console

   openstack server create --image cirros --flavor m1.tiny --key-name mykey --network demo-net demo1
   openstack floating ip create public1
   openstack server add floating ip demo1 192.168.33.4
   ssh cirros@192.168.33.4
