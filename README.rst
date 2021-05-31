Kayobe
======

.. image:: https://governance.openstack.org/tc/badges/kayobe.svg
    :target: https://governance.openstack.org/tc/reference/projects/kolla.html

Kayobe enables deployment of containerised OpenStack to bare metal.

Containers offer a compelling solution for isolating OpenStack services, but
running the control plane on an orchestrator such as Kubernetes or Docker
Swarm adds significant complexity and operational overheads.

The hosts in an OpenStack control plane must somehow be provisioned, but
deploying a secondary OpenStack cloud to do this seems like overkill.

Kayobe stands on the shoulders of giants:

* OpenStack bifrost discovers and provisions the cloud
* OpenStack kolla builds container images for OpenStack services
* OpenStack kolla-ansible delivers painless deployment and upgrade of
  containerised OpenStack services

To this solid base, kayobe adds:

* Configuration of cloud host OS & flexible networking
* Management of physical network devices
* A friendly openstack-like CLI

All this and more, automated from top to bottom using Ansible.

Features
--------

* Heavily automated using Ansible
* *kayobe* Command Line Interface (CLI) for cloud operators
* Deployment of a *seed* VM used to manage the OpenStack control plane
* Configuration of physical network infrastructure
* Discovery, introspection and provisioning of control plane hardware using
  `OpenStack bifrost <https://docs.openstack.org/bifrost/latest/>`_
* Deployment of an OpenStack control plane using `OpenStack kolla-ansible
  <https://docs.openstack.org/kolla-ansible/latest/>`_
* Discovery, introspection and provisioning of bare metal compute hosts
  using `OpenStack ironic <https://docs.openstack.org/ironic/latest/>`_ and
  `ironic inspector <https://docs.openstack.org/ironic-inspector/latest/>`_
* Virtualised compute using `OpenStack nova
  <https://docs.openstack.org/nova/latest/>`_
* Containerised workloads on bare metal using `OpenStack magnum
  <https://docs.openstack.org/magnum/latest/>`_
* Big data on bare metal using `OpenStack sahara
  <https://docs.openstack.org/sahara/latest/>`_
* Control plane and workload monitoring and log aggregation using `OpenStack
  monasca <https://wiki.openstack.org/wiki/Monasca>`_

Documentation
-------------

https://docs.openstack.org/kayobe/latest/

Release Notes
-------------

https://docs.openstack.org/releasenotes/kayobe/

Bugs
----

https://storyboard.openstack.org/#!/project/openstack/kayobe

Community
---------

OFTC's `IRC channel <http://webchat.oftc.net/?channels=openstack-kolla>`_: #openstack-kolla

License
-------

Kayobe is distributed under the `Apache 2.0 License <https://www.apache.org/licenses/LICENSE-2.0>`__.
