============
Virtual GPUs
============

Kayobe contains playbooks to configure virtualised GPUs on supported NVIDIA hardware.
This allows you to statically create mdev devices that can be used by Nova to present
a virtualised GPU to guest VMs. Known working GPUs are:

- NVIDIA A100

BIOS configuration
==================

Intel
-----

* Enable ``VT-x`` in the BIOS for virtualisation support.
* Enable ``VT-d`` in the BIOS for IOMMU support.

AMD
---

* Enable ``AMD-V`` in the BIOS for virtualisation support.
* Enable ``AMD-Vi`` in the BIOS for IOMMU support.

Example: Dell
-------------

Enabling SR-IOV with `racadm`:

.. code:: shell

    /opt/dell/srvadmin/bin/idracadm7 set BIOS.IntegratedDevices.SriovGlobalEnable Enabled
    /opt/dell/srvadmin/bin/idracadm7 jobqueue create BIOS.Setup.1-1
    <reboot>

Enabling CPU Virtualization with `racadm`:

.. code:: shell

    /opt/dell/srvadmin/bin/idracadm7 set BIOS.ProcSettings.ProcVirtualization Enabled
    /opt/dell/srvadmin/bin/idracadm7 jobqueue create BIOS.Setup.1-1
    <reboot>


Obtain driver from NVIDIA licensing portal
==========================================

Download NVIDIA GRID driver from `here <https://docs.nvidia.com/grid/latest/grid-software-quick-start-guide/index.html#redeeming-pak-and-downloading-grid-software>`__
(This requires a login).

.. _Configuration:

Configuration
=============

.. seealso::

   For further context, please see:

   * :ref:`configuration-kayobe`

Add hosts with supported GPUs to the ``compute-vgpu`` group. If using bifrost
and the ``kayobe overcloud inventory discover`` mechanism, this can be achieved with:

.. code-block:: yaml
   :caption: ``$KAYOBE_CONFIG_PATH/overcloud.yml``

   overcloud_group_hosts_map:
     compute-vgpu:
       - "computegpu000"

Configure the location of the NVIDIA driver:

.. code-block:: yaml
   :caption: ``$KAYOBE_CONFIG_PATH/vgpu.yml``

    ---
    vgpu_driver_url: "https://example.com/NVIDIA-GRID-Linux-KVM-525.105.14-525.105.17-528.89.zip"

If you don't know which vGPU types your card supports, these
can be determined by following :ref:`VGPU_Types`.

You can then define ``group_vars`` describing the vGPU configuration:

.. code-block:: yaml
   :caption: ``$KAYOBE_CONFIG_PATH/inventory/group_vars/compute-vgpu/vgpu``

   #nvidia-692 GRID A100D-4C
   #nvidia-693 GRID A100D-8C
   #nvidia-694 GRID A100D-10C
   #nvidia-695 GRID A100D-16C
   #nvidia-696 GRID A100D-20C
   #nvidia-697 GRID A100D-40C
   #nvidia-698 GRID A100D-80C
   #nvidia-699 GRID A100D-1-10C
   #nvidia-700 GRID A100D-2-20C
   #nvidia-701 GRID A100D-3-40C
   #nvidia-702 GRID A100D-4-40C
   #nvidia-703 GRID A100D-7-80C
   #nvidia-707 GRID A100D-1-10CME
   vgpu_definitions:
     # Configuring a MIG backed VGPU
     - pci_address: "0000:17:00.0"
       mig_devices:
         # This section describes how to partition the card using MIG. The key
         # in the dictionary represents a MIG profile supported by your card and
         # the value is the number of MIG devices of that type that you want
         # to create. The vGPUS are then created on top of these MIG devices.
         # The available profiles can be found in the NVIDIA documentation:
         # https://docs.nvidia.com/grid/15.0/grid-vgpu-user-guide/index.html#virtual-gpu-types-grid-reference
         "1g.10gb": 1
         "2g.20gb": 3
       virtual_functions:
         # The mdev type is the NVIDIA identifier for a particular vGPU. When using
         # MIG backed vGPUs these must match up with your MIG devices. See the NVIDIA
         # vGPU types section in this document.
         - mdev_type: nvidia-700
           index: 0
         - mdev_type: nvidia-700
           index: 1
         - mdev_type: nvidia-700
           index: 2
         - mdev_type: nvidia-699
           index: 3
     # Configuring a card in a time-sliced configuration (non-MIG backed)
     - pci_address: "0000:65:00.0"
       virtual_functions:
         - mdev_type: nvidia-697
           index: 0
         - mdev_type: nvidia-697
           index: 1

To apply this configuration, use:

.. code:: shell

    (kayobe) $ kayobe overcloud host configure -t vgpu

.. _VGPU_Types:

NVIDIA vGPU types
=================

.. seealso::

    For further context, please see:

    * `NVIDIA docs on vGPU types <https://docs.nvidia.com/grid/15.0/grid-vgpu-user-guide/index.html#virtual-gpu-types-grid-reference>`__
    * :ref:`configuration-kolla-ansible`

The NVIDIA vGPU drivers must be installed to be able to query for the available
vGPU types. This can be achieved by not defining any virtual functions in the
vGPU definition:

.. code-block:: yaml
   :caption: ``$KAYOBE_CONFIG_PATH/inventory/group_vars/compute-vgpu/vgpu``

   vgpu_definitions:
     - pci_address: "0000:17:00.0"
       virtual_functions: []

See :ref:`Configuration`. You can then use ``mdevctl`` to query for the
available vGPU types.

.. code:: shell

   mdevctl types

.. _VGPU_Kolla_Configuration:

Kolla Ansible configuration
===========================

.. seealso::

   For further context, please see:

   * :nova-doc:`Attaching virtual GPU devices to guests in the Nova documentation <admin/virtual-gpu.html>`
   * :ref:`configuration-kolla-ansible`

To use the mdev devices that were created, modify ``nova.conf`` to add a list of mdev devices that
can be passed through to guests:

.. code-block:: ini
   :caption: ``$KAYOBE_CONFIG_PATH/kolla/config/nova/nova-compute.conf``

   {% raw %}
   {% if inventory_hostname in groups['compute-vgpu'] %}
   [devices]
   enabled_mdev_types = nvidia-700, nvidia-699, nvidia-697
   [mdev_nvidia-700]
   device_addresses = 0000:17:00.4,0000:17:00.5,0000:17:00.6
   mdev_class = CUSTOM_NVIDIA_700
   [mdev_nvidia-699]
   device_addresses = 0000:17:00.7
   mdev_class = CUSTOM_NVIDIA_699
   [mdev_nvidia-697]
   device_addresses = 0000:65:00.4,0000:65:00.5
   mdev_class = CUSTOM_NVIDIA_697
   {% endif %}
   {% endraw %}

You will need to adjust the PCI addresses to match the virtual function
addresses. These can be obtained by checking the mdevctl configuration after
applying the :ref:`configuration <Configuration>`:

.. code-block:: shell

   # mdevctl list
   73269d0f-b2c9-438d-8f28-f9e4bc6c6995 0000:17:00.4 nvidia-700 manual (defined)
   dc352ef3-efeb-4a5d-a48e-912eb230bc76 0000:17:00.5 nvidia-700 manual (defined)
   a464fbae-1f89-419a-a7bd-3a79c7b2eef4 0000:17:00.6 nvidia-700 manual (defined)
   f3b823d3-97c8-4e0a-ae1b-1f102dcb3bce 0000:17:00.7 nvidia-699 manual (defined)
   330be289-ba3f-4416-8c8a-b46ba7e51284 0000:65:00.4 nvidia-700 manual (defined)
   1ba5392c-c61f-4f48-8fb1-4c6b2bbb0673 0000:65:00.5 nvidia-700 manual (defined)
   f6868020-eb3a-49c6-9701-6c93e4e3fa9c 0000:65:00.6 nvidia-700 manual (defined)
   00501f37-c468-5ba4-8be2-8d653c4604ed 0000:65:00.7 nvidia-699 manual (defined)

The mdev_class maps to a resource class that you can set in your flavor definition.
Note that if you only define a single mdev type on a given hypervisor, then the
mdev_class configuration option is silently ignored and it will use the ``VGPU``
resource class (See `bug 1943934 <https://bugs.launchpad.net/nova/+bug/1943934>`__).

To apply the configuration to Nova:

.. code:: shell

   (kayobe) $ kayobe overcloud service deploy -kt nova

OpenStack flavors
=================

Define some flavors that request the resource class that was configured in ``nova.conf``.
An example definition, that can be used with ``openstack.cloud.compute_flavor`` Ansible module,
is shown below:

.. code-block:: yaml

   openstack.cloud.compute_flavor:
     name: "vgpu.a100.2g.20gb"
     ram: 65536
     disk: 30
     vcpus: 8
     is_public: false
     extra_specs:
       hw:cpu_policy: "dedicated"
       hw:cpu_thread_policy: "prefer"
       hw:mem_page_size: "1GB"
       hw:cpu_sockets: 2
       hw:numa_nodes: 8
       hw_rng:allowed: "True"
       resources:CUSTOM_NVIDIA_700: "1"

Changing VGPU device types
==========================

Converting the second card to an NVIDIA-698 (whole card). The hypervisor
should be empty so we can freely delete mdevs. If this is not the case you will need
to check which mdevs are in use and use extreme caution. First clean up the mdev
definitions to make room for the new device:

.. code:: shell

   [stack@computegpu000 ~]$ sudo mdevctl list
   5c630867-a673-5d75-aa31-a499e6c7cb19 0000:21:00.4 nvidia-697 manual (defined)
   eaa6e018-308e-58e2-b351-aadbcf01f5a8 0000:21:00.5 nvidia-697 manual (defined)
   72291b01-689b-5b7a-9171-6b3480deabf4 0000:81:00.4 nvidia-697 manual (defined)
   0a47ffd1-392e-5373-8428-707a4e0ce31a 0000:81:00.5 nvidia-697 manual (defined)

   [stack@computegpu000 ~]$ sudo mdevctl stop --uuid 72291b01-689b-5b7a-9171-6b3480deabf4
   [stack@computegpu000 ~]$ sudo mdevctl stop --uuid 0a47ffd1-392e-5373-8428-707a4e0ce31a

   [stack@computegpu000 ~]$ sudo mdevctl undefine --uuid 0a47ffd1-392e-5373-8428-707a4e0ce31a
   [stack@computegpu000 ~]$ sudo mdevctl undefine --uuid 72291b01-689b-5b7a-9171-6b3480deabf4

   [stack@computegpu000 ~]$ sudo mdevctl list --defined
   5c630867-a673-5d75-aa31-a499e6c7cb19 0000:21:00.4 nvidia-697 manual (active)
   eaa6e018-308e-58e2-b351-aadbcf01f5a8 0000:21:00.5 nvidia-697 manual (active)

   # We can re-use the first virtual function

Secondly remove the systemd unit that starts the mdev device:

.. code:: shell

   [stack@computegpu000 ~]$ sudo rm /etc/systemd/system/multi-user.target.wants/nvidia-mdev@0a47ffd1-392e-5373-8428-707a4e0ce31a.service
   [stack@computegpu000 ~]$ sudo rm /etc/systemd/system/multi-user.target.wants/nvidia-mdev@72291b01-689b-5b7a-9171-6b3480deabf4.service

Adapt your :ref:`Kayobe <Configuration>` and :ref:`Kolla Ansible <VGPU_Kolla_Configuration>` configuration to
match the desired state and then re-run host configure:

.. code:: shell

   (kayobe) $ kayobe overcloud host configure --tags vgpu --limit computegpu000

Check the result:

.. code:: shell

   [stack@computegpu000 ~]$ mdevctl list
   5c630867-a673-5d75-aa31-a499e6c7cb19 0000:21:00.4 nvidia-697 manual
   eaa6e018-308e-58e2-b351-aadbcf01f5a8 0000:21:00.5 nvidia-697 manual
   72291b01-689b-5b7a-9171-6b3480deabf4 0000:81:00.4 nvidia-698 manual

Reconfigure nova to match the change:

.. code:: shell

   (kayobe) $ kayobe overcloud service reconfigure -kt nova --kolla-limit computegpu000 --skip-prechecks
