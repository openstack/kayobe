.. _control-plane-service-placement:

===============================
Control Plane Service Placement
===============================

.. note::

   This is an advanced topic and should only be attempted when familiar with
   kayobe and OpenStack.

The default configuration in kayobe places all control plane services on a
single set of servers described as 'controllers'.  In some cases it may be
necessary to introduce more than one server role into the control plane, and
control which services are placed onto the different server roles.

Configuration
=============

Overcloud Inventory Discovery
-----------------------------

If using a seed host to enable discovery of the control plane services, it is
necessary to configure how the discovered hosts map into kayobe groups. This
is done using the ``overcloud_group_hosts_map`` variable, which maps names of
kayobe groups to a list of the hosts to be added to that group.

This variable will be used during the command ``kayobe overcloud inventory
discover``.  An inventory file will be generated in
``${KAYOBE_CONFIG_PATH}/inventory/overcloud`` with discovered hosts added to
appropriate kayobe groups based on ``overcloud_group_hosts_map``.

Kolla-ansible Inventory Mapping
-------------------------------

Once hosts have been discovered and enrolled into the kayobe inventory, they
must be added to the kolla-ansible inventory.  This is done by mapping from top
level kayobe groups to top level kolla-ansible groups using the
``kolla_overcloud_inventory_top_level_group_map`` variable.  This variable maps
from kolla-ansible groups to lists of kayobe groups, and variables to define
for those groups in the kolla-ansible inventory.

Variables For Custom Server Roles
---------------------------------

Certain variables must be defined for hosts in the ``overcloud`` group.  For
hosts in the ``controllers`` group, many variables are mapped to other
variables with a ``controller_`` prefix in files under
``ansible/inventory/group_vars/controllers/``. This is done in order that they
may be set in a global extra variables file, typically ``controllers.yml``,
with defaults set in ``ansible/inventory/group_vars/all/controllers``.  A
similar scheme is used for hosts in the ``monitoring`` group.

.. table:: Overcloud host variables

   ====================== =====================================================
   Variable               Purpose
   ====================== =====================================================
   ``ansible_user``       Username with which to access the host via SSH.
   ``bootstrap_user``     Username with which to access the host before
                          ``ansible_user`` is configured.
   ``lvm_groups``         List of LVM volume groups to configure.  See
                          `mrlesmithjr.manage_lvm role
                          <https://galaxy.ansible.com/mrlesmithjr/manage_lvm/>`_
                          for format.
   ``mdadm_arrays``       List of software RAID arrays. See `mrlesmithjr.mdadm
                          role
                          <https://galaxy.ansible.com/mrlesmithjr/mdadm/>`_ for
                          format.
   ``network_interfaces`` List of names of networks to which the host is
                          connected.
   ``sysctl_parameters``  Dict of sysctl parameters to set.
   ``users``              List of users to create. See
                          `singleplatform-eng.users role
                          <https://galaxy.ansible.com/singleplatform-eng/users/>`_
   ====================== =====================================================

If configuring BIOS and RAID via ``kayobe overcloud bios raid configure``, the
following variables should also be defined:

.. table:: Overcloud BIOS & RAID host variables

   ====================== =====================================================
   Variable               Purpose
   ====================== =====================================================
   ``bios_config``        Dict mapping BIOS configuration options to their
                          required values. See `stackhpc.drac role
                          <https://galaxy.ansible.com/stackhpc/drac/>`_ for
                          format.
   ``raid_config``        List of RAID virtual disks to configure. See
                          `stackhpc.drac role
                          <https://galaxy.ansible.com/stackhpc/drac/>`_ for
                          format.
   ====================== =====================================================

These variables can be defined in inventory host or group variables files,
under ``${KAYOBE_CONFIG_PATH}/inventory/host_vars/<host>`` or
``${KAYOBE_CONFIG_PATH}/inventory/group_vars/<group>`` respectively.

Custom Kolla-ansible Inventories
--------------------------------

As an advanced option, it is possible to fully customise the content of the
kolla-ansible inventory, at various levels.  To facilitate this, kayobe breaks
the kolla-ansible inventory into three separate sections.

**Top level** groups define the roles of hosts, e.g. ``controller`` or ``compute``,
and it is to these groups that hosts are mapped directly.

**Components** define groups of services, e.g. ``nova`` or ``ironic``, which
are mapped to top level groups.

**Services** define single containers, e.g. ``nova-compute`` or ``ironic-api``,
which are mapped to components.

The default top level inventory is generated from
``kolla_overcloud_inventory_top_level_group_map``.
Kayobe's component- and service-level inventory for
kolla-ansible is static, and taken from the kolla-ansible example ``multinode``
inventory.  The complete inventory is generated by concatenating these
inventories.

Each level may be separately overridden by setting the following variables:

.. table:: Custom kolla-ansible inventory variables

   =============================================== =================================
   Variable                                        Purpose
   =============================================== =================================
   ``kolla_overcloud_inventory_custom_top_level``  Overcloud inventory containing a
                                                   mapping from top level groups
                                                   to hosts.
   ``kolla_overcloud_inventory_custom_components`` Overcloud inventory
                                                   containing a mapping from
                                                   components to top level
                                                   groups.
   ``kolla_overcloud_inventory_custom_services``   Overcloud inventory
                                                   containing a mapping from
                                                   services to components.
   ``kolla_overcloud_inventory_custom``            Full overcloud inventory
                                                   contents.
   =============================================== =================================

Examples
========

.. _control-plane-service-placement-network-hosts:

Example 1: Adding Network Hosts
-------------------------------

This example walks through the configuration that could be applied to enable
the use of separate hosts for neutron network services and load balancing.
The control plane consists of three controllers, ``controller-[0-2]``, and two
network hosts, ``network-[0-1]``. All file paths are relative to
``${KAYOBE_CONFIG_PATH}``.

First, we must make the network group separate from controllers:

.. code-block:: ini
   :caption: ``inventory/groups``

    [controllers]
    # Empty group to provide declaration of controllers group.

    [network]
    # Empty group to provide declaration of network group.

Then, we must map the hosts to kayobe groups.

.. code-block:: yaml
   :caption: ``overcloud.yml``

   overcloud_group_hosts_map:
     controllers:
       - controller-0
       - controller-1
       - controller-2
     network:
       - network-0
       - network-1

Next, we must map these groups to kolla-ansible groups.

.. code-block:: yaml
   :caption: ``kolla.yml``

   kolla_overcloud_inventory_top_level_group_map:
     control:
       groups:
         - controllers
     network:
       groups:
         - network

Finally, we create a group variables file for hosts in the network group,
providing the necessary variables for a control plane host.

.. code-block:: yaml
   :caption: ``inventory/group_vars/network``

   ansible_user: "{{ kayobe_ansible_user }}"
   bootstrap_user: "{{ controller_bootstrap_user }}"
   lvm_groups: "{{ controller_lvm_groups }}"
   mdadm_arrays: "{{ controller_mdadm_arrays }}"
   network_interfaces: "{{ controller_network_host_network_interfaces }}"
   sysctl_parameters: "{{ controller_sysctl_parameters }}"
   users: "{{ controller_users }}"

Here we are using the controller-specific values for some of these variables,
but they could equally be different.

.. _custom-kolla-inventory-templates:

Example 2: Overriding the Kolla-ansible Inventory
-------------------------------------------------

This example shows how to override one or more sections of the kolla-ansible
inventory.  All file paths are relative to ``${KAYOBE_CONFIG_PATH}``.

It is typically best to start with an inventory template taken from the Kayobe
source code, and then customize it. The templates can be found in
``ansible/roles/kolla-ansible/templates``, e.g. components template is ``overcloud-components.j2``.

First, create a file containing the customised inventory section. We'll use the
**components** section in this example.

.. code-block:: console
   :caption: ``kolla/inventory/overcloud-components.j2``

   [nova]
   control

   [ironic]
   {% if kolla_enable_ironic | bool %}
   control
   {% endif %}

   ...

Next, we must configure kayobe to use this inventory template.

.. code-block:: yaml
   :caption: ``kolla.yml``

   kolla_overcloud_inventory_custom_components: "{{ lookup('template', kayobe_env_config_path ~ '/kolla/inventory/overcloud-components.j2') }}"

Here we use the ``template`` lookup plugin to render the Jinja2-formatted
inventory template.

Fine-grained placement
======================

Kayobe has fairly coarse-grained default groups - ``controller``, ``compute``,
etc, which work well in the majority of cases. Kolla Ansible allows much
more fine-grained placement on a per-service basis, e.g.
``ironic-conductor``. If the operator has taken advantage of this
fine-grained placement, then it is possible that some of the assumptions
in Kayobe may be incorrect. This is one downside of the split between
Kayobe and Kolla Ansible.

For example, Ironic conductor services may have been moved to a subset of the
top level ``controllers`` group. In this case, we would not want the Ironic
networks to be mapped to all hosts in the controllers group - only those
running Ironic conductor services. The same argument can be made if the
loadbalancer services (HAProxy & keepalived) or Neutron dataplane services
(e.g. L3 & DHCP agents) have been separated from the top level ``network``
group.

In these cases, the following variables may be used to tune placement:

``controller_ironic_conductor_group``
    Ansible inventory group in which Ironic conductor services are deployed.
    Default is ``controllers``.
``controller_ironic_inspector_group``
    Ansible inventory group in which Ironic inspector services are deployed.
    Default is ``controllers``.
``controller_loadbalancer_group``
    Ansible inventory group in which control plane load balancer services are
    deployed. Default is ``network``.
``controller_network_group``
    Ansible inventory group in which network data plane services are deployed.
    Default is ``network``.
