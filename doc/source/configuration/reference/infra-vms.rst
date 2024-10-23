.. _configuration-infra-vms:

==================
Infrastructure VMs
==================

Kayobe can deploy infrastructure VMs to the seed-hypervisor. These can be used
to provide supplementary services that do not run well within a containerised
environment or are dependencies of the control plane.

Configuration
=============

To deploy an infrastructure VM, add a new host to the ``infra-vms`` group
in the inventory:

.. code-block:: ini
   :caption: ``$KAYOBE_CONFIG_PATH/inventory/infra-vms``

    [infra-vms]
    an-example-vm

The configuration of the virtual machine should be done using ``host_vars``.
These override the ``group_vars`` defined for the ``infra-vms`` group. Most
variables have sensible defaults defined, but there are a few variables which
must be set.

Mandatory variables
-------------------

All networks must have an interface defined, as described in
:ref:`configuration-network-per-host`. By default the VMs are attached
to the admin overcloud network. If, for example, ``admin_oc_net_name`` was
set to ``example_net``, you would need to define ``example_net_interface``.
It is possible to change the list of networks that a VM is attached to
by modifying ``infra_vm_network_interfaces``. Additional interfaces
can be added by setting ``infra_vm_network_interfaces_extra``.

List of Kayobe applied defaults to required docker_container variables.
Any of these variables can be overridden with a ``host_var``.

.. literalinclude:: ../../../../ansible/inventory/group_vars/all/infra-vms
    :language: yaml

Customisations
--------------

Examples of common customisations are shown below.

By default the Ansible inventory name is used as the name of the VM. This may
be overridden via ``infra_vm_name``:

.. code-block:: yaml
   :caption: ``$KAYOBE_CONFIG_PATH/inventory/host_vars/an-example-vm``

    # Name of the infra VM.
    infra_vm_name: "the-special-one"

By default the VM has 16G of RAM. This may be changed via
``infra_vm_memory_mb``:

.. code-block:: yaml
   :caption: ``$KAYOBE_CONFIG_PATH/inventory/host_vars/an-example-vm``

    # Memory in MB. Defaults to 16GB.
    infra_vm_memory_mb: "{{ 8 * 1024 }}"

The default network configuration attaches infra VMs to the admin network. If
this is not appropriate, modify ``infra_vm_network_interfaces``. At a minimum
the network interface name for the network should be defined.

.. code-block:: yaml
   :caption: ``$KAYOBE_CONFIG_PATH/inventory/host_vars/an-example-vm``

    # Network interfaces that the VM is attached to.
    infra_vm_network_interfaces:
      - aio

    # Mandatory: All networks must have an interface defined.
    aio_interface: eth0

    # By default kayobe will connect to a host via ``admin_oc_net``.
    # As we have not attached this VM to this network, we must override
    # ansible_host.
    ansible_host: "{{ 'aio' | net_ip }}"

Configuration for all VMs can be set using ``extra_vars`` defined in
``$KAYOBE_CONFIG_PATH/infra-vms.yml``. Note that normal Ansible precedence
rules apply and the variables will override any ``host_vars``. If you need to
override the defaults, but still maintain per-host settings, use ``group_vars``
instead.

Deploying the virtual machine
=============================

Once the initial configuration has been done follow the steps in
:ref:`deployment-infrastructure-vms`.
