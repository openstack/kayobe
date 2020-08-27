==========
Nova cells
==========

In the Train release, Kolla Ansible gained full support for the Nova cells v2
scale out feature. Whilst configuring Nova cells is documented in
:kolla-ansible-doc:`Kolla Ansible <reference/compute/nova-cells-guide>`,
implementing that configuration in Kayobe is documented here.

In Kolla Ansible, Nova cells :kolla-ansible-doc:`are configured
<reference/compute/nova-cells-guide#groups>` via group variables. In Kayobe,
these group variables can be set via Kayobe configuration. For example, to
configure ``cell0001`` the following file could be created:

.. code-block:: yaml
   :caption: ``$KAYOBE_CONFIG_PATH/kolla/inventory/group_vars/cell0001/all``

   ---
   nova_cell_name: cell0001
   nova_cell_novncproxy_group: cell0001-vnc
   nova_cell_conductor_group: cell0001-control
   nova_cell_compute_group: cell0001-compute

After defining the cell ``group_vars`` the Kayobe inventory can be configured.
In Kayobe, cell controllers and cell compute hosts become part of the existing
``controllers`` and ``compute`` Kayobe groups because typically they will need
to be provisioned in the same way. In Kolla Ansible, to prevent non-cell
services being mapped to cell controllers, the ``controllers`` group must be
split into two. The inventory file should also include the cell definitions.
The following groups and hosts files give an example of how this may be
achieved:

.. code-block:: yaml
   :caption: ``$KAYOBE_CONFIG_PATH/inventory/groups``

    # Kayobe groups inventory file. This file should generally not be modified.
    # If declares the top-level groups and sub-groups.

    ###############################################################################
    # Seed groups.

    [seed]
    # Empty group to provide declaration of seed group.

    [seed-hypervisor]
    # Empty group to provide declaration of seed-hypervisor group.

    [container-image-builders:children]
    # Build container images on the seed by default.
    seed

    ###############################################################################
    # Overcloud groups.

    [controllers]
    # Empty group to provide declaration of controllers group.

    [network:children]
    # Add controllers to network group by default for backwards compatibility,
    # although they could be separate hosts.
    top-level-controllers

    [monitoring]
    # Empty group to provide declaration of monitoring group.

    [storage]
    # Empty group to provide declaration of storage group.

    [compute]
    # Empty group to provide declaration of compute group.

    # Empty group to provide declaration of top-level controllers.
    [top-level-controllers]

    [overcloud:children]
    controllers
    network
    monitoring
    storage
    compute

    ###############################################################################
    # Docker groups.

    [docker:children]
    # Hosts in this group will have Docker installed.
    seed
    controllers
    network
    monitoring
    storage
    compute

    [docker-registry:children]
    # Hosts in this group will have a Docker Registry deployed. This group should
    # generally contain only a single host, to avoid deploying multiple independent
    # registries which may become unsynchronized.
    seed

    ###############################################################################
    # Baremetal compute node groups.

    [baremetal-compute]
    # Empty group to provide declaration of baremetal-compute group.

    ###############################################################################
    # Networking groups.

    [mgmt-switches]
    # Empty group to provide declaration of mgmt-switches group.

    [ctl-switches]
    # Empty group to provide declaration of ctl-switches group.

    [hs-switches]
    # Empty group to provide declaration of hs-switches group.

    [switches:children]
    mgmt-switches
    ctl-switches
    hs-switches


.. code-block:: yaml
   :caption: ``$KAYOBE_CONFIG_PATH/inventory/hosts``

    # Kayobe hosts inventory file. This file should be modified to define the hosts
    # and their top-level group membership.

    # This host acts as the configuration management Ansible control host. This must be
    # localhost.
    localhost ansible_connection=local

    [seed-hypervisor]
    # Add a seed hypervisor node here if required. This host will run a seed node
    # Virtual Machine.

    [seed]
    operator

    [controllers:children]
    top-level-controllers
    cell-controllers

    [top-level-controllers]
    control01

    [cell-controllers:children]
    cell01-control
    cell02-control

    [compute:children]
    cell01-compute
    cell02-compute

    [cell01:children]
    cell01-control
    cell01-compute
    cell01-vnc

    [cell01-control]
    control02

    [cell01-vnc]
    control02

    [cell01-compute]
    compute01

    [cell02:children]
    cell02-control
    cell02-compute
    cell02-vnc

    [cell02-control]
    control03

    [cell02-vnc]
    control03

    [cell02-compute]
    compute02
    compute03

    ##################################

    [mgmt-switches]
    # Add management network switches here if required.

    [ctl-switches]
    # Add control and provisioning switches here if required.

    [hs-switches]
    # Add high speed switches here if required.

Having configured the Kayobe inventory, the Kolla Ansible inventory can be
configured. Currently this can be done via the
``kolla_overcloud_inventory_top_level_group_map`` variable. For example, to
configure the two cells defined in the Kayobe inventory above, the variable
could be set to the following:

.. code-block:: yaml
   :caption: ``$KAYOBE_CONFIG_PATH/kolla.yml``

   kolla_overcloud_inventory_top_level_group_map:
     control:
       groups:
         - top-level-controllers
     network:
       groups:
         - network
     compute:
       groups:
         - compute
     monitoring:
       groups:
         - monitoring
     cell-control:
       groups:
         - cell-controllers
     cell0001:
       groups:
         - cell01
     cell0001-control:
        groups:
         - cell01-control
     cell0001-compute:
       groups:
         - cell01-compute
     cell0001-vnc:
       groups:
         - cell01-vnc
     cell0002:
       groups:
         - cell02
     cell0002-control:
       groups:
         - cell02-control
     cell0002-compute:
       groups:
         - cell02-compute
     cell0002-vnc:
       groups:
         - cell02-vnc

Finally, Nova cells can be enabled in Kolla Ansible:

.. code-block:: yaml
   :caption: ``$KAYOBE_CONFIG_PATH/kolla/globals.yml``

    enable_cells: True
