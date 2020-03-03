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

* Cumulus Linux (via `Network Command Line Utility (NCLU)
  <https://docs.cumulusnetworks.com/display/DOCS/Network+Command+Line+Utility+-+NCLU>`__)
* Dell OS 6
* Dell OS 9
* Dell PowerConnect
* Juniper Junos OS
* Mellanox MLNX OS

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

.. _physical-network-device-specific:

Device-specific Configuration Variables
=======================================

Cumulus Linux (with NCLU)
-------------------------

Configuration for these devices is applied using the ``nclu`` Ansible module.

``switch_type`` should be set to ``nclu``.

SSH configuration
^^^^^^^^^^^^^^^^^

As with any non-switch host in the inventory, the ``nclu`` module relies on the
default connection parameters used by Ansible:

* ``ansible_host`` is the hostname or IP address.  Optional.

* ``ansible_user`` is the SSH username.

Dell OS6 and OS9
----------------

Configuration for these devices is applied using the ``dellos6_config`` and
``dellos9_config`` Ansible modules.

``switch_type`` should be set to ``dellos6`` or ``dellos9``.

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
``stackhpc.dell-powerconnect-switch`` Ansible role.  The role uses the
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

Provider
^^^^^^^^

* ``ansible_host`` is the hostname or IP address.  Optional.

* ``ansible_user`` is the SSH username.

* ``ansible_ssh_pass`` is the SSH password.  Mutually exclusive with
  ``ansible_ssh_private_key_file``.

* ``ansible_ssh_private_key_file`` is the SSH private key file.  Mutually
  exclusive with ``ansible_ssh_pass``.

* ``switch_junos_timeout`` may be set to a timeout in seconds for communicating
  with the device.

Alternatively, set ``switch_junos_provider`` to the value to be passed as the
``provider`` argument to the ``junos_config`` module.

Mellanox MLNX OS
----------------

Configuration for these devices is applied using the
``stackhpc.mellanox-switch`` Ansible role.  The role uses the ``expect``
Ansible module to automate interaction with the switch CLI via SSH.

``switch_type`` should be set to ``mellanox``.

Provider
^^^^^^^^

* ``ansible_host`` is the hostname or IP address.  Optional.

* ``ansible_user`` is the SSH username.

* ``switch_auth_pass`` is the SSH password.
