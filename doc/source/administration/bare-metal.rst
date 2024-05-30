=================================
Baremetal Compute Node Management
=================================

When enrolling new hardware or performing maintenance, it can be useful to be
able to manage many bare metal compute nodes simultaneously.

In all cases, commands are delegated to one of the controller hosts, and
executed concurrently. Note that ansible's ``forks`` configuration option,
which defaults to 5, may limit the number of nodes configured concurrently.

By default these commands wait for the state transition to complete for each
node. This behavior can be changed by overriding the variable
``baremetal_compute_wait`` via ``-e baremetal_compute_wait=False``

Register
--------

This is an experimental workflow which acts as an alternative to enrolling
nodes through inspection. Bare metal compute nodes can be registered in Ironic
via Kayobe if defined in the Kayobe inventory. An example hosts file for group
r1 is below:

.. code-block:: ini

   [r1]
   hv100 ipmi_address=1.2.3.4
   ...

   [baremetal-compute:children]
   r1

You should also define a ``group_vars`` file for this group containing the
Ironic variables, this could be in
``etc/kayobe/inventory/group_vars/r1/ironic_vars`` or in the environment you
are using.

.. code-block:: yaml

   ironic_driver: redfish

   ironic_driver_info:
     redfish_system_id: "{{ ironic_redfish_system_id }}"
     redfish_address: "{{ ironic_redfish_address }}"
     redfish_username: "{{ ironic_redfish_username }}"
     redfish_password: "{{ ironic_redfish_password }}"
     redfish_verify_ca: "{{ ironic_redfish_verify_ca }}"
     ipmi_address: "{{ ipmi_address }}"

   ironic_properties:
     capabilities: "{{ ironic_capabilities }}"

   ironic_resource_class: "example_resource_class"
   ironic_redfish_system_id: "/redfish/v1/Systems/System.Embedded.1"
   ironic_redfish_verify_ca: "{{ inspector_rule_var_redfish_verify_ca }}"
   ironic_redfish_address: "{{ ipmi_address }}"
   ironic_redfish_username: "{{ inspector_redfish_username }}"
   ironic_redfish_password: "{{ inspector_redfish_password }}"
   ironic_capabilities: "boot_option:local,boot_mode:uefi"

It is essential that the Ironic username and password match the BMC username
and password for your nodes. If the username and password combination is not
the same for the entire group you will need to adjust your configuration
accordingly. The IPMI address should also match the BMC address for your node.

Once this has been completed you can begin enrolling the Ironic nodes::

    (kayobe) $ kayobe baremetal compute register

Inspector is not used to discover nodes and no node inspection will take place
on enrollment, nodes will automatically be placed into ``manageable`` state. To
inspect, you should use ``kayobe baremetal compute inspect`` following
enrollment.

Manage
------

A node may need to be set to the ``manageable`` provision state in order to
perform certain management operations, or when an enrolled node is
transitioned into service. In order to manage a node, it must be in one of
these states: ``enroll``, ``available``, ``cleaning``, ``clean failed``,
``adopt failed`` or ``inspect failed``. To move the baremetal compute nodes
to the ``manageable`` provision state::

    (kayobe) $ kayobe baremetal compute manage

Provide
-------

In order for nodes to be scheduled by nova, they must be ``available``. To
move the baremetal compute nodes from the ``manageable`` state to the
``available`` provision state::

    (kayobe) $ kayobe baremetal compute provide

Inspect
-------

Nodes must be in one of the following states: ``manageable``, ``inspect
failed``, or ``available``. To trigger hardware inspection on the baremetal
compute nodes::

    (kayobe) $ kayobe baremetal compute inspect

Saving Hardware Introspection Data
----------------------------------

Introspection data will be stored in the nginx service within the
``inspection_store`` container. This data may be saved to the control host::

    (kayobe) $ kayobe baremetal compute introspection data save

``--output-dir`` may be used to specify the directory in which introspection
data files will be saved. ``--output-format`` may be used to set the format of
the files.

Rename
------

Once nodes have been discovered, it is helpful to associate them with a name
to make them easier to work with. If you would like the nodes to be named
according to their inventory host names, you can run the following command::

    (kayobe) $ kayobe baremetal compute rename

This command will use the ``ipmi_address`` host variable from the inventory
to map the inventory host name to the correct node.

.. _update_deployment_image:

Update Deployment Image
-----------------------

When the overcloud deployment images have been rebuilt or there has been a change
to one of the following variables:

- ``ipa_kernel_upstream_url``
- ``ipa_ramdisk_upstream_url``

either by changing the url, or if the image to which they point
has been changed, you need to update the ``deploy_ramdisk``
and ``deploy_kernel`` properties on the Ironic nodes. To do
this you can run::

    (kayobe) $ kayobe baremetal compute update deployment image

You can optionally limit the nodes in which this affects by setting ``baremetal-compute-limit``::

    (kayobe) $ kayobe baremetal compute update deployment image --baremetal-compute-limit sand-6-1

which should take the form of an `ansible host pattern <https://docs.ansible.com/ansible/latest/user_guide/intro_patterns.html>`_.
This is matched against the Ironic node name.

Ironic Serial Console
---------------------

To access the baremetal nodes from within Horizon you need to enable the serial
console. For this to work the you must set
``kolla_enable_nova_serialconsole_proxy`` to ``true`` in
``etc/kayobe/kolla.yml``::

    kolla_enable_nova_serialconsole_proxy: true

The console interface on the Ironic nodes is expected to be ``ipmitool-socat``,
you can check this with::

    openstack baremetal node show <node_id> --fields console_interface

where <node_id> should be the UUID or name of the Ironic node you want to check.

If you have set ``kolla_ironic_enabled_console_interfaces`` in
``etc/kayobe/ironic.yml``, it should include ``ipmitool-socat`` in the list of
enabled interfaces.

The playbook to enable the serial console currently only works if the Ironic
node name matches the inventory hostname.

Once these requirements have been satisfied, you can run::

    (kayobe) $ kayobe baremetal compute serial console enable

This will reserve a TCP port for each node to use for the serial console
interface.  The allocations are stored in
``${KAYOBE_CONFIG_PATH}/console-allocation.yml``. The current implementation
uses a global pool, which is specified by
``ironic_serial_console_tcp_pool_start`` and
``ironic_serial_console_tcp_pool_end``; these variables can set in
``etc/kayobe/ironic.yml``.

To disable the serial console you can use::

    (kayobe) $ kayobe baremetal compute serial console disable

The port allocated for each node is retained and must be manually removed from
``${KAYOBE_CONFIG_PATH}/console-allocation.yml`` if you want it to be reused by
another Ironic node with a different name.

You can optionally limit the nodes targeted by setting
``baremetal-compute-limit``::

    (kayobe) $ kayobe baremetal compute serial console enable --baremetal-compute-limit sand-6-1

which should take the form of an `ansible host pattern
<https://docs.ansible.com/ansible/latest/user_guide/intro_patterns.html>`_.

Serial console auto-enable
~~~~~~~~~~~~~~~~~~~~~~~~~~

To enable the serial consoles automatically on ``kayobe overcloud post configure``, you can set
``ironic_serial_console_autoenable`` in ``etc/kayobe/ironic.yml``::

    ironic_serial_console_autoenable: true
