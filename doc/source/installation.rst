============
Installation
============

Prerequisites
=============

Currently Kayobe supports the following Operating Systems:

- CentOS 7.3

To avoid conflicts with python packages installed by the system package manager
it is recommended to install Kayobe in a virtualenv. Ensure that the
``virtualenv`` python module is available on the control host. For example, on
CentOS::

    $ yum install -y python-virtualenv

It is necessary to install the GCC compiler chain in order to build the
extensions of some of kayobe's python dependencies. On CentOS::

    $ yum install -y gcc

Finally, for cloning and working with the kayobe source code repository, Git is
required. On CentOS::

    $ yum install -y git

Installation
============

This guide will describe how to install Kayobe from source in a virtualenv.
First, obtain the Kayobe source code. For example::

    $ git clone https://github.com/stackhpc/kayobe

Create a virtualenv for Kayobe::

    $ cd kayobe
    $ virtualenv kayobe-venv

Activate the virtualenv and update pip::

    $ source kayobe-venv/bin/activate
    (kayobe-venv) $ pip install -U pip

Install Kayobe and its dependencies using the source code checkout::

    (kayobe-venv) $ pip install .

Finally, deactivate the virtualenv::

    (kayobe-venv) $ deactivate
