======
Kayobe
======

Deployment of Scientific OpenStack using OpenStack kolla.

Kayobe is a tool for automating deployment of Scientific OpenStack onto a set
of bare metal servers.  Kayobe is composed of Ansible playbooks, a python
module, and makes heavy use of the OpenStack kolla project.  Kayobe aims to
complement the kolla-ansible project, providing an opinionated yet highly
configurable OpenStack deployment and automation of many operational
procedures.

* Documentation: https://github.com/stackhpc/kayobe/tree/master/docs
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

Plus more to follow...
