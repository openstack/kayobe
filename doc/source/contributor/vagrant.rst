.. _contributor-vagrant:

=======
Vagrant
=======

Kayobe provides a Vagrantfile that can be used to bring up a virtual machine
for use as a development environment. The VM is based on the `centos/8
<https://app.vagrantup.com/centos/boxes/8>`_ CentOS 8 image, and
supports the following providers:

* VirtualBox
* VMWare Fusion

The VM is configured with 4GB RAM and a 20GB HDD. It has a single private network in addition
to the standard Vagrant NAT network.

Preparation
===========

First, ensure that Vagrant is installed and correctly configured to use
the required provider. Also install the following vagrant plugins::

    vagrant plugin install vagrant-reload vagrant-disksize

If using the VirtualBox provider, install the following vagrant plugin::

    vagrant plugin install vagrant-vbguest

Note: if using Ubuntu 16.04 LTS, you may be unable to install any plugins. To
work around this install the upstream version from www.virtualbox.org.

Usage
=====

Later sections in the development guide cover in more detail how to use the
development VM in different configurations.  These steps cover bringing up and
accessing the VM.

Clone the kayobe repository:

.. parsed-literal::

   git clone \https://opendev.org/openstack/kayobe.git -b |current_release_git_branch_name|

Change the current directory to the kayobe repository::

    cd kayobe

Inspect kayobe's ``Vagrantfile``, noting the provisioning steps::

    less Vagrantfile

Bring up a virtual machine::

    vagrant up

Wait for the VM to boot, then SSH in::

    vagrant ssh
