===================
All in one scenario
===================

.. note::
   This documentation is intended as a walk through of the configuration
   required for a minimal all-in-one overcloud host. If you are looking
   for an all-in-one environment for test or development, see
   :ref:`contributor-automated`.

This scenario describes how to configure an all-in-one controller and compute
node using Kayobe. This is a very minimal setup, and not one that is
recommended for a production environment, but is useful for learning about how
to use and configure Kayobe.

.. _configuration-scenario-aio-prerequisites:

Prerequisites
=============

This scenario requires a basic understanding of Linux, networking and
OpenStack.

It also requires a single host running a :ref:`supported operating system
<support-matrix-supported-os>` (VM or bare metal), with:

* 1 CPU
* 8GB RAM
* 40GB disk
* at least one network interface that has Internet access

You will need access to a user account with passwordless sudo. The default user
in a cloud image (e.g. ``cloud-user`` or ``rocky`` or ``ubuntu``) is typically
sufficient. This user will be used to run Kayobe commands. It will also be used
by Kayobe to bootstrap other user accounts.

.. _configuration-scenario-aio-overview:

Overview
========

An all in one environment consists of a single node that provides both control
and compute services. There is no seed host, and no provisioning of the
overcloud host. Customisation is minimal, in order to demonstrate the basic
required configuration in Kayobe::

       +---------------------------+
       |       Overcloud host      |
       |                           |
       |                           |
       |      +-------------+      |
       |      |             |+     |
       |      |  Containers ||     |
       |      |             ||     |
       |      +-------------+|     |
       |       +-------------+     |
       |                           |
       +---------+-------+---------+
                 |       |
                 | NIC 1 |
                 |       |
                 +---+---+
                     |
                     |
   +-----------------+------------------+ Internet

The networking in particular is relatively simple. The main interface of the
overcloud host, labelled NIC 1 in the above diagram, will be used only for
connectivity to the host and Internet access. A single Kayobe network called
``aio`` carries all control plane traffic, and is based on virtual networking
that is local to the host.

Later in this tutorial, we will create a dummy interface called ``dummy0``, and
plug it into a bridge called ``br0``::

    +--------------+
    |              |
    |      OVS     |
    |              |
    +--------------+
            |
            |
    +--------------+
    |              |
    |      br0     |
    | 192.168.33.3 |
    | 192.168.33.2 |
    +--------------+
       | dummy0 |
       +--------+

The use of a bridge here allows Kayobe to connect this network to the Open
vSwitch network, while maintaining an IP address on the bridge. Ordinarily,
``dummy0`` would be a NIC providing connectivity to a physical network. We're
using a dummy interface here to keep things simple by using a fixed IP subnet,
``192.168.33.0/24``. The bridge will be assigned a static IP address of
``192.168.33.3``, and this address will by used for various things, including
Ansible SSH access and OpenStack control plane traffic. Kolla Ansible will
manage a Virtual IP (VIP) address of ``192.168.33.2`` on ``br0``, which will be
used for OpenStack API endpoints.

Contents
========

.. toctree::
   :maxdepth: 2

   overcloud
