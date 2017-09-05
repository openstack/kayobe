======
Kayobe
======

.. image:: https://travis-ci.org/stackhpc/kayobe.svg?branch=master
   :target: https://travis-ci.org/stackhpc/kayobe

Deployment of Scientific OpenStack using OpenStack kolla.

Kayobe is an open source tool for automating deployment of Scientific OpenStack
onto a set of bare metal servers.  Kayobe is composed of Ansible playbooks, a
python module, and makes heavy use of the OpenStack kolla project.  Kayobe aims
to complement the kolla-ansible project, providing an opinionated yet highly
configurable OpenStack deployment and automation of many operational
procedures.

* Documentation: https://kayobe.readthedocs.io/en/latest/
* Source: https://github.com/stackhpc/kayobe
* Bugs: https://github.com/stackhpc/kayobe/issues

Features
--------

* Heavily automated using Ansible
* *kayobe* Command Line Interface (CLI) for cloud operators
* Deployment of a *seed* VM used to manage the OpenStack control plane
* Configuration of physical network infrastructure
* Discovery, introspection and provisioning of control plane hardware using
  `OpenStack bifrost <https://docs.openstack.org/developer/bifrost/>`_
* Deployment of an OpenStack control plane using `OpenStack kolla-ansible
  <https://docs.openstack.org/developer/kolla-ansible/>`_
* Discovery, introspection and provisioning of bare metal compute hosts
  using `OpenStack ironic <https://docs.openstack.org/developer/ironic/>`_ and
  `ironic inspector <https://docs.openstack.org/developer/ironic-inspector/>`_
* Containerised workloads on bare metal using `OpenStack magnum
  <https://docs.openstack.org/developer/magnum/>`_
* Big data on bare metal using `OpenStack sahara
  <https://docs.openstack.org/developer/sahara/>`_

In the near future we aim to add support for the following:

* Control plane and workload monitoring and log aggregation using `OpenStack
  monasca <https://wiki.openstack.org/wiki/Monasca>`_
* Virtualised compute using `OpenStack nova
  <https://docs.openstack.org/developer/nova/>`_
