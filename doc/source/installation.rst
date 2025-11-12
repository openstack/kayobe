.. _installation:

============
Installation
============

Kayobe can be installed via the released Python packages on PyPI, or from
source. Installing from PyPI ensures the use of well used and tested software,
whereas installing from source allows for the use of unreleased or patched
code.  Installing from a Python package is supported from Kayobe 5.0.0 onwards.

Prerequisites
=============

Currently Kayobe supports the following Operating Systems on the Ansible
control host:

- CentOS Stream 10 (since Flamingo 19.0.0 release)
- Rocky Linux 10 (since Flamingo 19.0.0 release)
- Ubuntu Noble 24.04 (since Dalmatian 17.0.0 release)

See the :doc:`support matrix <support-matrix>` for details of supported
Operating Systems for other hosts.

To avoid conflicts with python packages installed by the system package manager
it is recommended to install Kayobe in a virtualenv. Ensure that the
``virtualenv`` python module is available on the Ansible control host. It is
necessary to install the GCC compiler chain in order to build the extensions of
some of kayobe's python dependencies.

On CentOS/Rocky::

    $ dnf install -y python3-devel gcc libffi-devel

On Ubuntu::

    $ apt install -y python3-dev gcc libffi-dev python3-venv

If installing Kayobe from source, then Git is required for cloning and working
with the source code repository.

On CentOS/Rocky::

    $ dnf install -y git

On Ubuntu::

    $ apt install -y git

On Ubuntu, ensure that /usr/bin/python points to a Python 3 interpreter::

    $ apt install -y python-is-python3

Local directory structure
=========================

The directory structure for a Kayobe Ansible control host environment is
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

This pattern ensures that all dependencies for a particular environment are
installed under a single top level path, and nothing is installed to a shared
location. This allows for the option of using multiple Kayobe environments on
the same control host.

Creation of a ``kayobe-config`` source code repository will be covered in the
:ref:`configuration guide <configuring-kayobe>`. The Kolla Ansible source code
checkout and Python virtual environment will be created automatically by
kayobe.

Not all of these directories will be used in all scenarios - if Kayobe or Kolla
Ansible are installed from a Python package then the source code repository is
not required.

Installation from PyPI
======================

This section describes how to install Kayobe from a Python package in a
virtualenv. This is supported from Kayobe 5.0.0 onwards.

First, change to the top level directory, and make the directories for source
code repositories and python virtual environments::

    $ cd <base_path>
    $ mkdir -p src venvs

Create a virtualenv for Kayobe::

    $ python3 -m venv <base_path>/venvs/kayobe

Activate the virtualenv and update pip::

    $ source <base_path>/venvs/kayobe/bin/activate
    (kayobe) $ pip install -U pip

If using the latest version of Kayobe::

    (kayobe) $ pip install kayobe

Alternatively, to install a specific release of Kayobe::

    (kayobe) $ pip install kayobe==5.0.0

Finally, deactivate the virtualenv::

    (kayobe) $ deactivate

.. _installation-source:

Installation from source
========================

This section describes how to install Kayobe from source in a virtualenv.

First, change to the top level directory, and make the directories for source
code repositories and python virtual environments::

    $ cd <base_path>
    $ mkdir -p src venvs

Next, obtain the Kayobe source code. For example:

.. parsed-literal::

   $ cd <base_path>/src
   $ git clone \https://opendev.org/openstack/kayobe.git -b |current_release_git_branch_name|

Create a virtualenv for Kayobe::

    $ python3 -m venv <base_path>/venvs/kayobe

Activate the virtualenv and update pip::

    $ source <base_path>/venvs/kayobe/bin/activate
    (kayobe) $ pip install -U pip

Install Kayobe and its dependencies using the source code checkout::

    (kayobe) $ cd <base_path>/src/kayobe
    (kayobe) $ pip install .

Finally, deactivate the virtualenv::

    (kayobe) $ deactivate

.. _installation-editable:

Editable source installation
----------------------------

From Kayobe 5.0.0 onwards it is possible to create an `editable install
<https://pip.pypa.io/en/stable/topics/local-project-installs/#editable-installs>`__
of Kayobe. In an editable install, any changes to the Kayobe source tree will
immediately be visible when running any Kayobe commands.  To create an editable
install, add the ``-e`` flag::

    (kayobe) $ cd <base_path>/src/kayobe
    (kayobe) $ pip install -e .

This is particularly useful when installing Kayobe for development.
