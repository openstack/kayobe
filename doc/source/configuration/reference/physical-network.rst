.. _configuration-physical-network:

==============================
Physical Network Configuration
==============================

Kayobe supports configuration of physical network devices.  This feature is
optional, and this section may be skipped if network device configuration will
be managed via other means.

Devices are added to the Ansible inventory, and configured using Ansible's
networking modules.  Configuration is applied via the ``kayobe physical network
configure`` command.  See :ref:`physical-network` for details.

The following switch operating systems are currently supported:

* Arista EOS
* Cumulus Linux (via `Network Command Line Utility (NCLU)
  <https://docs.nvidia.com/networking-ethernet-software/cumulus-linux-44/System-Configuration/Network-Command-Line-Utility-NCLU/>`__)
* Cumulus Linux (via `NVIDIA User Experience command line utility (NVUE)
  <https://docs.nvidia.com/networking-ethernet-software/cumulus-linux/System-Configuration/NVIDIA-User-Experience-NVUE/>`__)
* Dell OS 6
* Dell OS 9
* Dell OS 10
* Dell PowerConnect
* Juniper Junos OS
* Mellanox MLNX OS

.. note::

   When developing switch configuration, it can be helpful to see what commands
   will be generated.  This can be done using the ``--display`` parameter for
   ``kayobe physical network configure``, which will output switch global and port
   configuration as terminal output without applying it.

Adding Devices to the Inventory
===============================

Network devices should be added to the Kayobe Ansible inventory, and should be
members of the ``switches`` group.

.. code-block:: ini
   :caption: ``inventory/hosts``

   [switches]
   switch0
   switch1

In some cases it may be useful to differentiate different types of switches,
For example, a ``mgmt`` network might carry out-of-band management traffic, and
a ``ctl`` network might carry control plane traffic.  A group could be created
for each of these networks, with each group being a child of the ``switches``
group.

.. code-block:: ini
   :caption: ``inventory/hosts``

   [switches:children]
   mgmt-switches
   ctl-switches

   [mgmt-switches]
   switch0

   [ctl-switches]
   switch1

Network Device Configuration
============================

Configuration is typically specific to each network device.  It is therefore
usually best to add a ``host_vars`` file to the inventory for each device.
Common configuration for network devices can be added in a ``group_vars`` file
for the ``switches`` group or one of its child groups.

.. code-block:: yaml
   :caption: ``inventory/host_vars/switch0``

   ---
   # Host configuration for switch0
   ansible_host: 1.2.3.4

.. code-block:: yaml
   :caption: ``inventory/host_vars/switch1``

   ---
   # Host configuration for switch1
   ansible_host: 1.2.3.5

.. code-block:: yaml
   :caption: ``inventory/group_vars/switches``

   ---
   # Group configuration for 'switches' group.
   ansible_user: alice

Common Configuration Variables
==============================

The type of switch should be configured via the ``switch_type`` variable.  See
:ref:`physical-network-device-specific` for details of the value to set for
each device type.

``ansible_host`` should be set to the management IP address used to access the
device.  ``ansible_user`` should be set to the user used to access the device.

Global switch configuration is specified via the ``switch_config`` variable.
It should be a list of configuration lines to apply.

Per-interface configuration is specified via the ``switch_interface_config``
variable.  It should be an object mapping switch interface names to
configuration objects.  Each configuration object contains a ``description``
item and a ``config`` item.  The ``config`` item should contain a list of
per-interface configuration lines.

The ``switch_interface_config_enable_discovery`` and
``switch_interface_config_disable_discovery`` variables take the same format as
the ``switch_interface_config`` variable.  They define interface configuration
to apply to enable or disable hardware discovery of bare metal compute nodes.

.. code-block:: yaml
   :caption: ``inventory/host_vars/switch0``

   ---
   ansible_host: 1.2.3.4

   ansible_user: alice

   switch_config:
     - global config line 1
     - global config line 2

   switch_interface_config:
     interface-0:
       description: controller0
       config:
         - interface-0 config line 1
         - interface-0 config line 2
     interface-1:
       description: compute0
       config:
         - interface-1 config line 1
         - interface-1 config line 2

Network device configuration can become quite repetitive, so it can be helpful
to define group variables that can be referenced by multiple devices. For
example:

.. code-block:: yaml
   :caption: ``inventory/group_vars/switches``

   ---
   # Group configuration for the 'switches' group.
   switch_config_default:
     - default global config line 1
     - default global config line 2

   switch_interface_config_controller:
     - controller interface config line 1
     - controller interface config line 2

   switch_interface_config_compute:
     - compute interface config line 1
     - compute interface config line 2

.. code-block:: yaml
   :caption: ``inventory/host_vars/switch0``

   ---
   ansible_host: 1.2.3.4

   ansible_user: alice

   switch_config: "{{ switch_config_default }}"

   switch_interface_config:
     interface-0:
       description: controller0
       config: "{{ switch_interface_config_controller }}"
     interface-1:
       description: compute0
       config: "{{ switch_interface_config_compute }}"

Support for Older Devices
=========================

Some network devices may use SSH key exchange algorithms that are no longer
supported by the Ansible control host. This will cause ``ssh-keyscan`` to fail,
preventing Kayobe from configuring the devices. To work around this, set
``switch_skip_keyscan`` to ``true`` for the affected devices. The SSH known
hosts file on the Ansible control host will need to be populated manually.

.. _physical-network-device-specific:

Device-specific Configuration Variables
=======================================

Arista EOS
----------

Configuration for these devices is applied using the ``arista-switch`` Ansible
role in Kayobe. The role configures Arista switches using the ``eos`` Ansible
modules.

``switch_type`` should be set to ``arista``.

* ``ansible_host`` is the hostname or IP address.  Optional.
* ``ansible_user`` is the SSH username.
* ``ansible_ssh_pass`` is the SSH password.
* ``ansible_connection`` should be ``ansible.netcommon.network_cli``.
* ``ansible_network_os`` should be ``arista.eos.eos``.
* ``ansible_become`` should be ``true``.
* ``ansible_become_method`` should be ``enable``.

Cumulus Linux (with NCLU)
-------------------------

Configuration for these devices is applied using the ``nclu`` Ansible module.

``switch_type`` should be set to ``nclu``.

Cumulus Linux (with NVUE)
-------------------------

Configuration for these devices is applied using the ``nvidia.nvue.command``
Ansible module.

``switch_type`` should be set to ``nvue``.

SSH configuration
^^^^^^^^^^^^^^^^^

As with any non-switch host in the inventory, the ``nclu`` and
``nvidia.nvue.command`` modules rely on the default connection parameters used
by Ansible:

* ``ansible_host`` is the hostname or IP address.  Optional.

* ``ansible_user`` is the SSH username.

Dell OS6, OS9, and OS10
-----------------------

Configuration for these devices is applied using the ``dellos6_config``,
``dellos9_config``, and ``dellos10_config`` Ansible modules.

``switch_type`` should be set to ``dellos6``, ``dellos9``, or ``dellos10``.

``switch_config_save`` may be set to ``true`` to enable saving configuration
after it has been applied.

Provider
^^^^^^^^

* ``ansible_host`` is the hostname or IP address.  Optional.

* ``ansible_user`` is the SSH username.

* ``ansible_ssh_pass`` is the SSH password.

* ``switch_auth_pass`` is the 'enable' password.

Alternatively, set ``switch_dellos_provider`` to the value to be passed as the
``provider`` argument to the ``dellos*_config`` module.

Dell PowerConnect
-----------------

Configuration for these devices is applied using the
``stackhpc.network.dell_powerconnect_switch`` Ansible role.  The role uses the
``expect`` Ansible module to automate interaction with the switch CLI via SSH.

``switch_type`` should be set to ``dell-powerconnect``.

Provider
^^^^^^^^

* ``ansible_host`` is the hostname or IP address.  Optional.

* ``ansible_user`` is the SSH username.

* ``switch_auth_pass`` is the SSH password.

Juniper Junos OS
----------------

Configuration for these devices is applied using the ``junos_config`` Ansible
module.

``switch_type`` should be set to ``junos``.

``switch_junos_config_format`` may be used to set the format of the
configuration.  The variable is passed as the ``src_format`` argument to the
``junos_config`` module.  The default value is ``text``.

* ``ansible_host`` is the hostname or IP address.  Optional.
* ``ansible_user`` is the SSH username.
* ``ansible_ssh_pass`` is the SSH password.  Mutually exclusive with
  ``ansible_ssh_private_key_file``.
* ``ansible_ssh_private_key_file`` is the SSH private key file.  Mutually
  exclusive with ``ansible_ssh_pass``.
* ``ansible_connection`` should be ``ansible.netcommon.netconf``.
* ``ansible_network_os`` should be ``junipernetworks.junos.junos``.

Mellanox MLNX OS
----------------

Configuration for these devices is applied using the
``stackhpc.network.mellanox_switch`` Ansible role.  The role uses the
``expect`` Ansible module to automate interaction with the switch CLI via SSH.

``switch_type`` should be set to ``mellanox``.

Provider
^^^^^^^^

* ``ansible_host`` is the hostname or IP address.  Optional.

* ``ansible_user`` is the SSH username.

* ``switch_auth_pass`` is the SSH password.
