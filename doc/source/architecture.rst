============
Architecture
============

Hosts in the System
===================

In a system deployed by Kayobe we define a number of classes of hosts.

Ansible control host
    The Ansible control host is the host on which kayobe, kolla and
    kolla-ansible will be installed, and is typically where the cloud will be
    managed from.
Seed host
    The seed host runs the bifrost deploy container and is used to provision
    the cloud hosts.  By default, container images are built on the seed.
    Typically the seed host is deployed as a VM but this is not mandatory.
Infrastructure VM hosts
    Infrastructure VMs (or Infra VMs) are virtual machines that may be deployed
    to provide supplementary infrastructure services. They may be for things
    like proxies or DNS servers that are dependencies of the Cloud hosts.
Cloud hosts
    The cloud hosts run the OpenStack control plane, network, monitoring,
    storage, and virtualised compute services.  Typically the cloud hosts run
    on bare metal but this is not mandatory.
Bare metal compute hosts
    In a cloud providing bare metal compute services to tenants via ironic,
    these hosts will run the bare metal tenant workloads.  In a cloud with only
    virtualised compute this category of hosts does not exist.

.. note::

   In many cases the control and seed host will be the same, although this is
   not mandatory.

Cloud Hosts
-----------

Cloud hosts can further be divided into subclasses.

Controllers
    Controller hosts run the OpenStack control plane services.
Network
    Network hosts run the neutron networking services and load balancers for
    the OpenStack API services.
Monitoring
    Monitoring host run the control plane and workload monitoring services.
    Currently, kayobe does not deploy any services onto monitoring hosts.
Virtualised compute hypervisors
    Virtualised compute hypervisors run the tenant Virtual Machines (VMs) and
    associated OpenStack services for compute, networking and storage.

Networks
========

Kayobe's network configuration is very flexible but does define a few default
classes of networks.  These are logical networks and may map to one or more
physical networks in the system.

Overcloud out-of-band network
    Name of the network used by the seed to access the out-of-band management
    controllers of the bare metal overcloud hosts.
Overcloud provisioning network
    The overcloud provisioning network is used by the seed host to provision
    the cloud hosts.
Workload out-of-band network
    Name of the network used by the overcloud hosts to access the out-of-band
    management controllers of the bare metal workload hosts.
Workload provisioning network
    The workload provisioning network is used by the cloud hosts to provision
    the bare metal compute hosts.
Internal network
    The internal network hosts the internal and admin OpenStack API endpoints.
Public network
    The public network hosts the public OpenStack API endpoints.
External network
    The external network provides external network access for the hosts in the
    system.
