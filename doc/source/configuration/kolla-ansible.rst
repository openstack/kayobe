===========================
Kolla-ansible Configuration
===========================

Kayobe relies heavily on kolla-ansible for deployment of the OpenStack control
plane. Kolla-ansible is installed locally on the Ansible control host (the host
from which kayobe commands are executed), and kolla-ansible commands are
executed from there.

Local Environment
=================

Environment variables are used to configure the environment in which
kolla-ansible is installed and executed.

.. table:: Kolla-ansible environment variables

   ====================== ================================================== ============================
   Variable               Purpose                                            Default
   ====================== ================================================== ============================
   ``$KOLLA_CONFIG_PATH`` Path on the Ansible control host in which          ``/etc/kolla``
                          the kolla-ansible configuration will be generated.
                          These files should not be manually edited.
   ``$KOLLA_SOURCE_PATH`` Path on the Ansible control host in which          ``$PWD/src/kolla-ansible``
                          the kolla-ansible source code will be cloned.
   ``$KOLLA_VENV_PATH``   Path on the Ansible control host in which          ``$PWD/venvs/kolla-ansible``
                          the kolla-ansible virtualenv will be created.
   ====================== ================================================== ============================

Extra Python packages can be installed inside the kolla-ansible virtualenv,
such as when required by Ansible plugins, using the
``kolla_ansible_venv_extra_requirements`` list variable in
``$KAYOBE_CONFIG_PATH/kolla.yml``. For example, to use the `hashi_vault Ansible
lookup plugin
<https://docs.ansible.com/ansible/devel/plugins/lookup/hashi_vault.html>`_, its
``hvac`` dependency can be installed using:

.. code-block:: yaml
   :caption: ``$KAYOBE_CONFIG_PATH/kolla.yml``

   ---
   # Extra requirements to install inside the kolla-ansible virtualenv.
   kolla_ansible_venv_extra_requirements:
     - "hvac"

.. _configuration-kolla-ansible-venv:

Remote Execution Environment
============================

By default, ansible executes modules remotely using the system python
interpreter, even if the ansible control process is executed from within a
virtual environment (unless the ``local`` connection plugin is used).
This is not ideal if there are python dependencies that must be installed
with isolation from the system python packages. Ansible can be configured to
use a virtualenv by setting the host variable ``ansible_python_interpreter``
to a path to a python interpreter in an existing virtual environment.

If the variable ``kolla_ansible_target_venv`` is set, kolla-ansible will be
configured to create and use a virtual environment on the remote hosts.
This variable is by default set to ``{{ virtualenv_path }}/kolla-ansible``.
The previous behaviour of installing python dependencies directly to the host
can be used by setting ``kolla_ansible_target_venv`` to ``None``.

Control Plane Services
======================

Kolla-ansible provides a flexible mechanism for configuring the services that
it deploys. Kayobe adds some commonly required configuration options to the
defaults provided by kolla-ansible, but also allows for the free-form
configuration supported by kolla-ansible. The `kolla-ansible documentation
<https://docs.openstack.org/kolla-ansible/latest/>`_ should be used as a
reference.

Global Variables
----------------

Kolla-ansible uses a single file for global variables, ``globals.yml``. Kayobe
provides configuration variables for all required variables and many of the
most commonly used the variables in this file. Some of these are in
``$KAYOBE_CONFIG_PATH/kolla.yml``, and others are determined from other sources
such as the networking configuration in ``$KAYOBE_CONFIG_PATH/networks.yml``.

Configuring Custom Global Variables
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Additional global configuration may be provided by creating
``$KAYOBE_CONFIG_PATH/kolla/globals.yml``. Variables in this file will be
templated using Jinja2, and merged with the Kayobe ``globals.yml``
configuration.

.. code-block:: yaml
   :caption: ``$KAYOBE_CONFIG_PATH/kolla/globals.yml``

   ---
   # Use a custom tag for the nova-api container image.
   nova_api_tag: v1.2.3

Passwords
---------

Kolla-ansible auto-generates passwords to a file, ``passwords.yml``. Kayobe
handles the orchestration of this, as well as encryption of the file using an
ansible vault password specified in the ``KAYOBE_VAULT_PASSWORD`` environment
variable, if present. The file is generated to
``$KAYOBE_CONFIG_PATH/kolla/passwords.yml``, and should be stored along with
other kayobe configuration files. This file should not be manually modified.

Configuring Custom Passwords
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In order to write additional passwords to ``passwords.yml``, set the kayobe
variable ``kolla_ansible_custom_passwords`` in
``$KAYOBE_CONFIG_PATH/kolla.yml``.

.. code-block:: yaml
   :caption: ``$KAYOBE_CONFIG_PATH/kolla.yml``

   ---
   # Dictionary containing custom passwords to add or override in the Kolla
   # passwords file.
   kolla_ansible_custom_passwords: >
     {{ kolla_ansible_default_custom_passwords |
        combine({'my_custom_password': 'correcthorsebatterystaple'}) }}

Service Configuration
---------------------

Kolla-ansible's flexible configuration is described in the `kolla-ansible
service configuration documentation
<https://docs.openstack.org/kolla-ansible/latest/admin/advanced-configuration.html#openstack-service-configuration-in-kolla>`_.
We won't duplicate that here, but essentially it involves creating files under
a directory which for users of kayobe will be ``$KOLLA_CONFIG_PATH/config``. In
kayobe, files in this directory are auto-generated and managed by kayobe.
Instead, users should create files under ``$KAYOBE_CONFIG_PATH/kolla/config``
with the same directory structure.  These files will be templated using Jinja2,
merged with kayobe's own configuration, and written out to
``$KOLLA_CONFIG_PATH/config``.

The following files, if present, will be templated and provided to
kolla-ansible.  All paths are relative to ``$KAYOBE_CONFIG_PATH/kolla/config``.
Note that typically kolla-ansible does not use the same wildcard patterns, and
has a more restricted set of files that it will process.  In some cases, it may
be necessary to inspect the kolla-ansible configuration tasks to determine
which files are supported.

.. table: Kolla-ansible configuration files

   =============================== =======================================================
   File                            Purpose
   =============================== =======================================================
   ``ceph/*``                      Ceph configuration.
   ``glance.conf``                 Glance configuration.
   ``glance/*``                    Extended glance configuration.
   ``fluentd/filter``              Fluentd filter configuration.
   ``fluentd/input``               Fluentd input configuration.
   ``fluentd/output``              Fluentd output configuration.
   ``heat.conf``                   Heat configuration.
   ``heat/*``                      Extended heat configuration.
   ``horizon/*``                   Extended horizon configuration.
   ``ironic-inspector.conf``       Ironic inspector configuration.
   ``ironic.conf``                 Ironic configuration.
   ``ironic/*``                    Extended ironic configuration.
   ``keystone.conf``               Keystone configuration.
   ``keystone/*``                  Extended keystone configuration.
   ``magnum.conf``                 Magnum configuration.
   ``magnum/*``                    Extended magnum configuration.
   ``manila.conf``                 Manila configuration.
   ``manila/*``                    Extended manila configuration.
   ``murano.conf``                 Murano configuration.
   ``murano/*``                    Extended murano configuration.
   ``neutron.conf``                Neutron configuration.
   ``neutron/*``                   Extended neutron configuration.
   ``nova.conf``                   Nova configuration.
   ``nova/*``                      Extended nova configuration.
   ``sahara.conf``                 Sahara configuration.
   ``sahara/*``                    Extended sahara configuration.
   ``swift/*``                     Extended swift configuration.
   =============================== =======================================================

Configuring an OpenStack Component
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To provide custom configuration to be applied to all glance services, create
``$KAYOBE_CONFIG_PATH/kolla/config/glance.conf``.  For example:

.. code-block:: yaml
   :caption: ``$KAYOBE_CONFIG_PATH/kolla/config/glance.conf``

   [DEFAULT]
   api_limit_max = 500

Configuring an OpenStack Service
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To provide custom configuration for the glance API service, create
``$KAYOBE_CONFIG_PATH/kolla/config/glance/glance-api.conf``.  For example:

.. code-block:: yaml
   :caption: ``$KAYOBE_CONFIG_PATH/kolla/config/glance/glance-api.conf``

   [DEFAULT]
   api_limit_max = 500
