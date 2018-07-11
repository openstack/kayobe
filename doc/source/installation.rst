============
Installation
============

Prerequisites
=============

Currently Kayobe supports the following Operating Systems on the Ansible
control host:

- CentOS 7.3
- Ubuntu 16.04

To avoid conflicts with python packages installed by the system package manager
it is recommended to install Kayobe in a virtualenv. Ensure that the
``virtualenv`` python module is available on the Ansible control host. It is
necessary to install the GCC compiler chain in order to build the extensions of
some of kayobe's python dependencies. Finally, for cloning and working with the
kayobe source code repository, Git is required.

On CentOS::

    $ yum install -y python-devel python-virtualenv gcc git

On Ubuntu::

    $ apt install -y python-dev python-virtualenv gcc git

Installation
============

This guide will describe how to install Kayobe from source in a virtualenv.

The directory structure for a kayobe Ansible control host environment is
configurable, but the following is recommended, where ``<base_path>`` is the
path to a top level directory::

    <base_path>/
        src/
            kayobe/
            kayobe-config/
            kolla-ansible/
        venvs/
            kayobe/
            kolla-ansible/

First, change to the top level directory, and make the directories for source
code repositories and python virtual environments::

    $ cd <base_path>
    $ mkdir -p src venvs

Next, obtain the Kayobe source code. For example::

    $ cd <base_path>/src
    $ git clone https://git.openstack.org/openstack/kayobe.git

Create a virtualenv for Kayobe::

    $ virtualenv <base_path>/venvs/kayobe

Activate the virtualenv and update pip::

    $ source <base_path>/venvs/kayobe/bin/activate
    (kayobe) $ pip install -U pip

Install Kayobe and its dependencies using the source code checkout::

    (kayobe) $ cd <base_path>/src/kayobe
    (kayobe) $ pip install .

Finally, deactivate the virtualenv::

    (kayobe) $ deactivate

Creation of a ``kayobe-config`` source code repository will be covered in the
:ref:`configuration guide <configuring-kayobe>`. The kolla-ansible source code
checkout and python virtual environment will be created automatically by
kayobe.
