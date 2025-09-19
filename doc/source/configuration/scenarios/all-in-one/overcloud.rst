=========
Overcloud
=========

.. note::
   This documentation is intended as a walk through of the configuration
   required for a minimal all-in-one overcloud host. If you are looking
   for an all-in-one environment for test or development, see
   :ref:`contributor-automated`.

Preparation
===========

Use the bootstrap user described in :ref:`prerequisites
<configuration-scenario-aio-prerequisites>` to access the machine.

As described in the :ref:`overview <configuration-scenario-aio-overview>`, we
will use a bridge (``br0``) and a dummy interface (``dummy0``) for control
plane networking. Use the following commands to create them and assign the
bridge a static IP address of ``192.168.33.3``:

.. code-block:: console

   sudo ip l add br0 type bridge
   sudo ip l set br0 up
   sudo ip a add 192.168.33.3/24 dev br0
   sudo ip l add dummy0 type dummy
   sudo ip l set dummy0 up
   sudo ip l set dummy0 master br0

This configuration is not persistent, and must be recreated if the VM is
rebooted.

Installation
============

Follow the instructions in :doc:`/installation` to set up an Ansible control
host environment.  Typically this would be on a separate machine, but here we
are keeping things as simple as possible.

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
network interface called ``dummy0``. We will create a bridge called ``br0``
and plug ``dummy0`` into it.  Replace the network interface configuration for
the ``controllers`` group with the following:

.. code-block:: yaml
   :caption: ``etc/kayobe/inventory/group_vars/controllers/network-interfaces``

   # Controller interface on all-in-one network.
   aio_interface: br0

   # Interface dummy0 is plugged into the all-in-one network bridge.
   aio_bridge_ports:
     - dummy0

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
the ``os_distribution`` variable in ``etc/kayobe/globals.yml`` to ``ubuntu``
or ``rocky`` if using Rocky Linux..

.. code-block:: yaml
   :caption: ``etc/kayobe/globals.yml``

   os_distribution: "ubuntu"

Kayobe uses a bootstrap user to create a ``stack`` user account. By default,
this user is ``cloud-user`` on CentOS, ``rocky`` on Rocky and ``ubuntu`` on
Ubuntu, in line with the default user in the official cloud images. If you are
using a different bootstrap user, set the ``controller_bootstrap_user``
variable in ``etc/kayobe/controllers.yml``. For example, to set it to
``cloud-user`` (as seen in MAAS):

.. code-block:: yaml
   :caption: ``etc/kayobe/controllers.yml``

   controller_bootstrap_user: "cloud-user"

By default, on systems with SELinux disabled, Kayobe will put SELinux in
permissive mode and reboot the system to apply the change. In a test or
development environment this can be a bit disruptive, particularly when using
ephemeral network configuration.  To avoid rebooting the system after enabling
SELinux, set ``selinux_do_reboot`` to ``false`` in ``etc/kayobe/globals.yml``.

.. code-block:: yaml
   :caption: ``etc/kayobe/globals.yml``

   selinux_do_reboot: false

In a development environment, we may wish to tune some Kolla Ansible variables.
Using QEMU as the virtualisation type will be necessary if KVM is not
available. Reducing the number of OpenStack service workers helps to avoid
using too much memory.

.. code-block:: yaml
   :caption: ``etc/kayobe/kolla/globals.yml``

   # Most development environments will use nested virtualisation, and we can't
   # guarantee that nested KVM support is available. Use QEMU as a lowest common
   # denominator.
   nova_compute_virt_type: qemu

   # Reduce the control plane's memory footprint by limiting the number of worker
   # processes to one per-service.
   openstack_service_workers: "1"

We can see the changes that have been made to the configuration.

.. code-block:: console

   cd <base path>/src/kayobe-config
   git status

   On branch master
   Your branch is up to date with 'origin/master'.

   Changes to be committed:
     (use "git restore --staged <file>..." to unstage)
       deleted:    etc/kayobe/inventory/hosts.example

   Changes not staged for commit:
     (use "git add <file>..." to update what will be committed)
     (use "git restore <file>..." to discard changes in working directory)
       modified:   etc/kayobe/globals.yml
       modified:   etc/kayobe/inventory/group_vars/controllers/network-interfaces
       modified:   etc/kayobe/kolla/globals.yml
       modified:   etc/kayobe/networks.yml

   Untracked files:
     (use "git add <file>..." to include in what will be committed)
       etc/kayobe/inventory/hosts
       etc/kayobe/network-allocation.yml

The ``git diff`` command is also helpful. Once all configuration changes have
been made, they should be committed to the kayobe-config git repository.

.. code-block:: console

   cd <base path>/src/kayobe-config
   git add etc/kayobe/inventory/hosts etc/kayobe/network-allocation.yml
   git add --update
   git commit -m "All in one scenario config"

In a real environment these changes would be pushed to a central repository.

Deployment
==========

We are now ready to perform a deployment.

Activate the Kayobe virtual environment:

.. code-block:: console

   cd <base path>/venvs/kayobe
   source bin/activate

Activate the Kayobe configuration environment:

.. code-block:: console

   cd <base path>/src/kayobe-config
   source kayobe-env

Bootstrap the control host:

.. code-block:: console

   kayobe control host bootstrap

Configure the overcloud host:

.. code-block:: console

   kayobe overcloud host configure

After this command has run, some files in the kayobe-config repository will
have changed. Kayobe performs static allocation of IP addresses, and tracks
them in ``etc/kayobe/network-allocation.yml``. Normally there may be changes to
this file, but in this case we manually added the IP address of ``controller0``
earlier. Kayobe uses tools provided by Kolla Ansible to generate passwords, and
stores them in ``etc/kayobe/kolla/passwords.yml``. It is important to track
changes to this file.

.. code-block:: console

   cd <base path>/src/kayobe-config
   git add etc/kayobe/kolla/passwords.yml
   git commit -m "Add autogenerated passwords for Kolla Ansible"

Pull overcloud container images:

.. code-block:: console

   kayobe overcloud container image pull

Deploy overcloud services:

.. code-block:: console

   kayobe overcloud service deploy

Testing
=======

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
   export EXT_NET_GATEWAY=192.168.33.3
   export EXT_NET_RANGE="start=192.168.33.4,end=192.168.33.254"
   source "${KOLLA_CONFIG_PATH:-/etc/kolla}/admin-openrc.sh"
   ${KOLLA_SOURCE_PATH}/tools/init-runonce

Create a server instance, assign a floating IP address, and check that it is
accessible.

.. code-block:: console

   openstack server create --image cirros --flavor m1.tiny --key-name mykey --network demo-net demo1
   openstack floating ip create public1

The floating IP address is displayed after it is created, in this example it is
``192.168.33.4``:

.. code-block:: console

   openstack server add floating ip demo1 192.168.33.4
   ssh cirros@192.168.33.4
