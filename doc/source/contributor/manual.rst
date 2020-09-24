.. _contributor-manual:

============
Manual Setup
============

This section provides a set of manual steps to set up a development environment
for an OpenStack controller in a virtual machine using `Vagrant
<https://www.vagrantup.com/>`_ and Kayobe.

For a more automated and flexible procedure, see :ref:`contributor-automated`.

Preparation
===========

Follow the steps in :ref:`contributor-vagrant` to prepare your environment for
use with Vagrant and bring up a Vagrant VM.

Manual Installation
===================

Sometimes the best way to learn a tool is to ditch the scripts and perform a
manual installation.

SSH into the controller VM::

    vagrant ssh

Source the kayobe virtualenv activation script::

    source kayobe-venv/bin/activate

Change the current directory to the Vagrant shared directory::

    cd /vagrant

Source the kayobe environment file::

    source kayobe-env

Bootstrap the kayobe Ansible control host::

    kayobe control host bootstrap

Configure the controller host::

    kayobe overcloud host configure

At this point, container images must be acquired. They can either be built
locally or pulled from an image repository if appropriate images are available.

Either build container images::

    kayobe overcloud container image build

Or pull container images::

    kayobe overcloud container image pull

Deploy the control plane services::

    kayobe overcloud service deploy

Source the OpenStack environment file::

    source ${KOLLA_CONFIG_PATH:-/etc/kolla}/admin-openrc.sh

Perform post-deployment configuration::

    kayobe overcloud post configure

Next Steps
==========

The OpenStack control plane should now be active. Try out the following:

* register a user
* create an image
* upload an SSH keypair
* access the horizon dashboard

The cloud is your oyster!

To Do
=====

Create virtual baremetal nodes to be managed by the OpenStack control plane.
