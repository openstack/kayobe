=======
Testing
=======

Kayobe has a number of test suites covering different areas of code. Many tests
are run in virtual environments using ``tox``.

Preparation
===========

System Prerequisites
--------------------

The following packages should be installed on the development system prior to
running kayobe's tests.

* Ubuntu/Debian::

      sudo apt-get install build-essential python3-dev libssl-dev python3-pip git

* Fedora or CentOS Stream 10/Rocky 10/RHEL 10::

      sudo dnf install python3-devel openssl-devel python3-pip git gcc

* OpenSUSE/SLE 12::

      sudo zypper install python3-devel python3-pip libopenssl-devel git

Python Prerequisites
--------------------

If your distro has at least ``tox 1.8``, use your system package manager to
install the ``python-tox`` package. Otherwise install this on all distros::

    sudo pip install -U tox

You may need to explicitly upgrade ``virtualenv`` if you've installed the one from
your OS distribution and it is too old (tox will complain). You can upgrade it
individually, if you need to::

    sudo pip install -U virtualenv

Running Unit Tests Locally
==========================

If you haven't already, the kayobe source code should be pulled directly from
git:

.. parsed-literal::

   # from your home or source directory
   cd ~
   git clone \https://opendev.org/openstack/kayobe.git -b |current_release_git_branch_name|
   cd kayobe

Running Unit and Style Tests
----------------------------

Kayobe defines a number of different tox environments in ``tox.ini``. The
default environments may be displayed::

    tox -list

To run all default environments::

    tox

To run one or more specific environments, including any of the non-default
environments::

    tox -e <environment>[,<environment>]

Environments
------------

The following tox environments are provided:

ansible
    Run Ansible tests for some ansible roles using Ansible playbooks.
ansible-lint
    Run Ansible linter.
ansible-syntax
    Run a syntax check for all Ansible files.
docs
    Build Sphinx documentation.
molecule
    Run Ansible tests for some Ansible roles using the molecule test framework.
pep8
    Run style checks for all shell, python and documentation files.
py3
    Run python unit tests for kayobe python module.

Writing Tests
=============

Unit Tests
----------

Unit tests follow the lead of OpenStack, and use ``unittest``. One difference
is that tests are run using the discovery functionality built into
``unittest``, rather than ``ostestr``/``stestr``.  Unit tests are found in
``kayobe/tests/unit/``, and should be added to cover all new python code.

Ansible Role Tests
------------------

Two types of test exist for Ansible roles - pure Ansible and molecule tests.

Pure Ansible Role Tests
^^^^^^^^^^^^^^^^^^^^^^^

These tests exist for the ``kolla-ansible`` role, and are found in
``ansible/<role>/tests/*.yml``. The role is exercised using an ansible
playbook.

Molecule Role Tests
^^^^^^^^^^^^^^^^^^^

`Molecule <https://molecule.readthedocs.io/en/latest/>`_ is an Ansible role
testing framework that allows roles to be tested in isolation, in a stable
environment, under multiple scenarios. Kayobe uses Docker engine to provide the
test environment, so this must be installed and running on the development
system.

Molecule scenarios are found in ``ansible/<role>/molecule/<scenario>``, and
defined by the config file ``ansible/<role>/molecule/<scenario>/molecule.yml``
Tests are written in python using the `pytest
<https://docs.pytest.org/en/latest/>`_ framework, and are found in
``ansible/<role>/molecule/<scenario>/tests/test_*.py``.

Molecule tests currently exist for the ``kolla-openstack`` role, and should be
added for all new roles where practical.
