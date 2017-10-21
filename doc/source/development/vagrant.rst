.. _development-vagrant:

=======
Vagrant
=======

Kayobe provides a Vagrantfile that can be used to bring up a virtual machine
for use as a development environment. The VM is based on the `stackhpc/centos-7
<https://app.vagrantup.com/stackhpc/boxes/centos-7>`_ CentOS 7 image, and
supports the following providers:

* VirtualBox
* VMWare Fusion

The VM is configured with 4GB RAM. It has a single private network in addition
to the standard Vagrant NAT network.

Preparation
===========

First, ensure that Vagrant is installed and correctly configured to use
virtual box. Also install the following vagrant plugins::

    vagrant plugin install vagrant-vbguest
    vagrant plugin install vagrant-reload

Note: if using Ubuntu 16.04 LTS, you may be unable to install any plugins. To
work around this install the upstream version from www.virtualbox.org.

Usage
=====

Later sections in the development guide cover in more detail how to use the
development VM in different configurations.  These steps cover bringing up and
accessing the VM.

Clone the kayobe repository::

    git clone https://github.com/stackhpc/kayobe

Change the current directory to the kayobe repository::

    cd kayobe

Inspect kayobe's ``Vagrantfile``, noting the provisioning steps::

    less Vagrantfile

Bring up a virtual machine::

    vagrant up

Wait for the VM to boot, then SSH in::

    vagrant ssh
