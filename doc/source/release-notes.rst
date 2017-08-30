=============
Release Notes
=============

Kayobe 1.1.0
============

Kayobe 1.1.0 was released on 17th July 2017.

Features
--------

* Support static routes on control plane networks
* Improve documentation
* Initial support for in-development Pike release
* Upgrade kayobe control host & control plane
* Support overcloud service destroy command
* Support fluentd custom output configuration

Kayobe 1.0.0
============

1.0.0 is the first 'official' release of the Kayobe OpenStack deployment tool.
It was released on 29th June 2017.

Features
--------

This release includes the following features:

* Heavily automated using Ansible
* ``kayobe`` Command Line Interface (CLI) for cloud operators
* Deployment of a seed VM used to manage the OpenStack control plane
* Configuration of physical network infrastructure
* Discovery, introspection and provisioning of control plane hardware using
  OpenStack bifrost
* Deployment of an OpenStack control plane using OpenStack kolla-ansible
* Discovery, introspection and provisioning of bare metal compute hosts using
  OpenStack ironic and ironic inspector
* Containerised workloads on bare metal using OpenStack magnum
* Big data on bare metal using OpenStack sahara
