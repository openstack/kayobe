===================
All in one scenario
===================

This scenario describes how to configure an all-in-one controller and compute
node using Kayobe.

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
       |      |             |      |
       |      |  Containers |      |
       |      |             |      |
       |      +-------------+      |
       |                           |
       |                           |
       +---------+-------+---------+
                 |       |
                 | NIC 1 |
                 |       |
                 +---+---+
                     |
                     |
   +-----------------+------------------+ Internet


Prerequisites
=============

This scenario requires:

* a basic understanding of Linux, networking and OpenStack
* a single host running a :ref:`supported operating system
  <support-matrix-supported-os>` (VM or bare metal)
* at least one network interface that has Internet access
* an IP subnet with a free IP address for the OpenStack API virtual IP, and a
  range of free IP addresses for external network access

Contents
========

.. toctree::
   :maxdepth: 2

   overcloud
