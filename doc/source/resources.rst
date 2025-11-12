==========
Resources
==========

This section contains links to external Kayobe resources.

.. _a-universe-from-nothing:

A Universe From Nothing
========================

.. note:: The 'A Universe From Nothing' deployment guide is intended for
  educational & testing purposes only. It is *not* production ready.

Originally created as a workshop, A 'Universe From Nothing' is an example
guide for the deployment of Kayobe on virtual hardware. You can find it on
GitHub `here <https://github.com/stackhpc/a-universe-from-nothing/>`_.

The repository contains a configuration suitable for deploying containerised
OpenStack using Kolla, Ansible and Kayobe. The guide makes use of
`Tenks <https://opendev.org/openstack/tenks>`_ to provision a virtual
baremetal environment running on a single hypervisor.

To complete the walkthrough you will require a baremetal or VM hypervisor
running CentOS Stream 10 (since Flamingo 19.0.0), Rocky Linux 10 (since
Flamingo 19.0.0) or Ubuntu Noble 24.04 (since Dalmatian 17.0.0) with at least
32GB RAM & 80GB disk space. Preparing the deployment can take some time - where
possible it is beneficial to snapshot the hypervisor. We advise making a
snapshot after creating the initial 'seed' VM as this will make additional
deployments significantly faster.
