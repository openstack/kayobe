.. _configuration-kolla-ansible:

===========================
Kolla Ansible Configuration
===========================

Kayobe relies heavily on Kolla Ansible for deployment of the OpenStack control
plane. Kolla Ansible is installed locally on the Ansible control host (the host
from which Kayobe commands are executed), and Kolla Ansible commands are
executed from there.

Kolla Ansible configuration is stored in ``${KAYOBE_CONFIG_PATH}/kolla.yml``.

Kolla Ansible Installation
==========================

Prior to deploying containers, Kolla Ansible and its dependencies will be
installed on the Ansible control host. The following variables affect the
installation of Kolla Ansible:

``kolla_ansible_ctl_install_type``
    Type of Kolla Ansible control installation. One of ``binary`` (PyPI) or
    ``source`` (git). Default is ``source``.
``kolla_ansible_source_url``
    URL of Kolla Ansible source code repository if type is ``source``. Default
    is https://opendev.org/openstack/kolla-ansible.
``kolla_ansible_source_version``
    Version (branch, tag, etc.) of Kolla Ansible source code repository if type
    is ``source``. Default is the same as the Kayobe upstream branch.
``kolla_ansible_venv_extra_requirements``
    Extra requirements to install inside the Kolla Ansible virtualenv. Default
    is an empty list.
``kolla_upper_constraints_file``
    Upper constraints file for installation of Kolla. Default is
    ``{{ pip_upper_constraints_file }}``, which has a default of
    ``https://releases.openstack.org/constraints/upper/{{ openstack_branch }}``.

Example: custom git repository
------------------------------

To install Kolla Ansible from a custom git repository:

.. code-block:: yaml
   :caption: ``$KAYOBE_CONFIG_PATH/kolla.yml``

   kolla_ansible_source_url: https://git.example.com/kolla-ansible
   kolla_ansible_source_version: downstream

Virtual Environment Extra Requirements
--------------------------------------

Extra Python packages can be installed inside the Kolla Ansible virtualenv,
such as when required by Ansible plugins.

For example, to use the `hashi_vault Ansible lookup plugin
<https://docs.ansible.com/ansible/devel/plugins/lookup/hashi_vault.html>`_, its
``hvac`` dependency can be installed using:

.. code-block:: yaml
   :caption: ``$KAYOBE_CONFIG_PATH/kolla.yml``

   ---
   # Extra requirements to install inside the Kolla Ansible virtualenv.
   kolla_ansible_venv_extra_requirements:
     - "hvac"

Local environment
=================

The following variables affect the local environment on the Ansible control
host. They reference environment variables, and should be configured using
those rather than modifying the Ansible variable directly.  The file
``kayobe-env`` in the `kayobe-config git repository
<https://opendev.org/openstack/kayobe-config>`__ sets some sensible defaults
for these variables, based on the recommended environment directory structure.

``kolla_ansible_source_path``
    Path to directory for Kolla Ansible source code checkout. Default is
    ``$KOLLA_SOURCE_PATH``, or ``$PWD/src/kolla-ansible``.
``kolla_ansible_venv``
    Path to virtualenv in which to install Kolla Ansible on the Ansible control
    host. Default is ``$KOLLA_VENV_PATH`` or ``$PWD/venvs/kolla-ansible``.
``kolla_config_path``
    Path to Kolla Ansible configuration directory. Default is
    ``$KOLLA_CONFIG_PATH`` or ``/etc/kolla``.

.. _configuration-kolla-ansible-global:

Global Configuration
====================

The following variables are global, affecting all containers. They are used to
generate the Kolla Ansible configuration file, ``globals.yml``, and also affect
:ref:`Kolla image build configuration <configuration-kolla-global>`.

Kolla Images
------------

The following variables affect which Kolla images are used, and how they are
accessed.

``kolla_base_distro``
    Kolla base container image distribution. Default is ``centos``.
``kolla_install_type``
    Kolla container image type: ``binary`` or ``source``. Default is
    ``binary``.
``kolla_docker_registry``
    URL of docker registry to use for Kolla images. Default is not set, in
    which case Dockerhub will be used.
``kolla_docker_namespace``
    Docker namespace to use for Kolla images. Default is ``kolla``.
``kolla_docker_registry_username``
    Username to use to access a docker registry. Default is not set, in which
    case the registry will be used without authentication.
``kolla_docker_registry_password``
    Password to use to access a docker registry. Default is not set, in which
    case the registry will be used without authentication.
``kolla_openstack_release``
    Kolla OpenStack release version. This should be a Docker image tag. Default
    is ``{{ openstack_release }}``, which takes the OpenStack release name
    (e.g. ``rocky``) on stable branches and tagged releases, or ``master`` on
    the Kayobe ``master`` branch.

For example, to deploy Kolla ``centos`` ``binary`` images with a namespace of
``example``, and a private Docker registry at ``registry.example.com:4000``,
tagged with ``7.0.0.1``:

.. code-block:: yaml
   :caption: ``$KAYOBE_CONFIG_PATH/kolla.yml``

   kolla_base_distro: centos
   kolla_install_type: binary
   kolla_docker_namespace: example
   kolla_docker_registry: registry.example.com:4000
   kolla_openstack_release: 7.0.0.1

The deployed ``ironic-api`` image would be referenced as follows:

.. code-block:: console

   registry.example.com:4000/example/centos-binary-ironic-api:7.0.0.1

Ansible
-------

The following variables affect how Ansible accesses the remote hosts.

``kolla_ansible_user``
    User account to use for Kolla SSH access. Default is ``kolla``.
``kolla_ansible_group``
    Primary group of Kolla SSH user. Default is ``kolla``.
``kolla_ansible_become``
    Whether to use privilege escalation for all operations performed via Kolla
    Ansible. Default is ``true``.
``kolla_ansible_target_venv``
    Path to a virtual environment on remote hosts to use for Ansible module
    execution. Default is ``{{ virtualenv_path }}/kolla-ansible``. May be set
    to ``None`` to use the system Python interpreter.

.. _configuration-kolla-ansible-venv:

Context: Remote Execution Environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

By default, Ansible executes modules remotely using the system python
interpreter, even if the Ansible control process is executed from within a
virtual environment (unless the ``local`` connection plugin is used).
This is not ideal if there are python dependencies that must be installed
with isolation from the system python packages. Ansible can be configured to
use a virtualenv by setting the host variable ``ansible_python_interpreter``
to a path to a python interpreter in an existing virtual environment.

The variable ``kolla_ansible_target_venv`` configures the use of a virtual
environment on the remote hosts. The default configuration should work in most
cases.

OpenStack Logging
-----------------

The following variable affects OpenStack debug logging.

``kolla_openstack_logging_debug``
    Whether debug logging is enabled for OpenStack services. Default is
    ``false``.

Example: enabling debug logging
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In certain situations it may be necessary to enable debug logging for all
OpenStack services. This is not usually advisable in production.

.. code-block:: yaml
   :caption: ``$KAYOBE_CONFIG_PATH/kolla.yml``

   ---
   kolla_openstack_logging_debug: true

TLS Encryption of APIs
----------------------

The following variables affect TLS encryption of the public API.

``kolla_enable_tls_external``
    Whether TLS is enabled for the public API endpoints. Default is ``no``.
``kolla_external_tls_cert``
    A TLS certificate bundle to use for the public API endpoints, if
    ``kolla_enable_tls_external`` is ``true``.  Note that this should be
    formatted as a literal style block scalar.
``kolla_external_fqdn_cacert``
    Path to a CA certificate file to use for the ``OS_CACERT`` environment
    variable in openrc files when TLS is enabled, instead of Kolla Ansible's
    default.

The following variables affect TLS encryption of the internal API. Currently
this requires all Kolla images to be built with the API's root CA trusted.

``kolla_enable_tls_internal``
    Whether TLS is enabled for the internal API endpoints. Default is ``no``.
``kolla_internal_tls_cert``
    A TLS certificate bundle to use for the internal API endpoints, if
    ``kolla_enable_tls_internal`` is ``true``.  Note that this should be
    formatted as a literal style block scalar.
``kolla_internal_fqdn_cacert``
    Path to a CA certificate file to use for the ``OS_CACERT`` environment
    variable in openrc files when TLS is enabled, instead of Kolla Ansible's
    default.

Example: enabling TLS for the public API
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

It is highly recommended to use TLS encryption to secure the public API.
Here is an example:

.. code-block:: yaml
   :caption: ``$KAYOBE_CONFIG_PATH/kolla.yml``

   ---
   kolla_enable_tls_external: yes
   kolla_external_tls_cert: |
     -----BEGIN CERTIFICATE-----
     ...
     -----END CERTIFICATE-----
   kolla_external_fqdn_cacert: /path/to/ca/certificate/bundle

Example: enabling TLS for the internal API
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

It is highly recommended to use TLS encryption to secure the internal API.
Here is an example:

.. code-block:: yaml
   :caption: ``$KAYOBE_CONFIG_PATH/kolla.yml``

   ---
   kolla_enable_tls_internal: yes
   kolla_internal_tls_cert: |
     -----BEGIN CERTIFICATE-----
     ...
     -----END CERTIFICATE-----
   kolla_internal_fqdn_cacert: /path/to/ca/certificate/bundle

Custom Global Variables
-----------------------

Kolla Ansible uses a single file for global variables, ``globals.yml``. Kayobe
provides configuration variables for all required variables and many of the
most commonly used the variables in this file. Some of these are in
``$KAYOBE_CONFIG_PATH/kolla.yml``, and others are determined from other sources
such as the networking configuration in ``$KAYOBE_CONFIG_PATH/networks.yml``.

Additional global configuration may be provided by creating
``$KAYOBE_CONFIG_PATH/kolla/globals.yml``. Variables in this file will be
templated using Jinja2, and merged with the Kayobe ``globals.yml``
configuration.

Example: use a specific tag for each image
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For more fine-grained control over images, Kolla Ansible allows a tag to be
defined for each image. For example, for ``nova-api``:

.. code-block:: yaml
   :caption: ``$KAYOBE_CONFIG_PATH/kolla/globals.yml``

   ---
   # Use a custom tag for the nova-api container image.
   nova_api_tag: v1.2.3

Example: debug logging per-service
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Enabling debug logging globally can lead to a lot of additional logs being
generated. Often we are only interested in a particular service. For example,
to enable debug logging for Nova services:

.. code-block:: yaml
   :caption: ``$KAYOBE_CONFIG_PATH/kolla/globals.yml``

   ---
   nova_logging_debug: true

Host variables
--------------

Kayobe generates a host_vars file for each host in the Kolla Ansible
inventory. These contain network interfaces and other host-specific
things.

``kolla_seed_inventory_pass_through_host_vars``
    List of names of host variables to pass through from kayobe hosts to the
    Kolla Ansible seed host, if set. See also
    ``kolla_seed_inventory_pass_through_host_vars_map``. The default is:

    .. code-block:: yaml

       kolla_seed_inventory_pass_through_host_vars:
         - "ansible_host"
         - "ansible_port"
         - "ansible_ssh_private_key_file"
         - "kolla_api_interface"
         - "kolla_bifrost_network_interface"

``kolla_seed_inventory_pass_through_host_vars_map``
    Dict mapping names of variables in
    ``kolla_seed_inventory_pass_through_host_vars`` to the variable to use in
    Kolla Ansible. If a variable name is not in this mapping the kayobe name is
    used. The default is:

    .. code-block:: yaml

       kolla_seed_inventory_pass_through_host_vars_map:
         kolla_api_interface: "api_interface"
         kolla_bifrost_network_interface: "bifrost_network_interface"

``kolla_overcloud_inventory_pass_through_host_vars``
    List of names of host variables to pass through from Kayobe hosts to
    Kolla Ansible hosts, if set. See also
    ``kolla_overcloud_inventory_pass_through_host_vars_map``. The default is:

    .. code-block:: yaml

       kolla_overcloud_inventory_pass_through_host_vars:
         - "ansible_host"
         - "ansible_port"
         - "ansible_ssh_private_key_file"
         - "kolla_network_interface"
         - "kolla_api_interface"
         - "kolla_storage_interface"
         - "kolla_cluster_interface"
         - "kolla_swift_storage_interface"
         - "kolla_swift_replication_interface"
         - "kolla_provision_interface"
         - "kolla_inspector_dnsmasq_interface"
         - "kolla_dns_interface"
         - "kolla_tunnel_interface"
         - "kolla_external_vip_interface"
         - "kolla_neutron_external_interfaces"
         - "kolla_neutron_bridge_names"

``kolla_overcloud_inventory_pass_through_host_vars_map``
    Dict mapping names of variables in
    ``kolla_overcloud_inventory_pass_through_host_vars`` to the variable to use
    in Kolla Ansible. If a variable name is not in this mapping the Kayobe name
    is used. The default is:

    .. code-block:: yaml

       kolla_overcloud_inventory_pass_through_host_vars_map:
         kolla_network_interface: "network_interface"
         kolla_api_interface: "api_interface"
         kolla_storage_interface: "storage_interface"
         kolla_cluster_interface: "cluster_interface"
         kolla_swift_storage_interface: "swift_storage_interface"
         kolla_swift_replication_interface: "swift_replication_interface"
         kolla_provision_interface: "provision_interface"
         kolla_inspector_dnsmasq_interface: "ironic_dnsmasq_interface"
         kolla_dns_interface: "dns_interface"
         kolla_tunnel_interface: "tunnel_interface"
         kolla_neutron_external_interfaces: "neutron_external_interface"
         kolla_neutron_bridge_names: "neutron_bridge_name"

Custom Group Variables
----------------------

Group variables can be used to set configuration for all hosts in a group. They
can be set in Kolla Ansible by placing files in
``${KAYOBE_CONFIG_PATH}/kolla/inventory/group_vars/*``. Since this
directory is copied directly into the Kolla Ansible inventory, Kolla
Ansible group names should be used. It should be noted that
``extra-vars`` and ``host_vars`` take precedence over ``group_vars``. For
more information on variable precedence see the Ansible `documentation
<http://docs.ansible.com/ansible/playbooks_variables.html#variable-precedence-where-should-i-put-a-variable>`_.

Example: configure a Nova cell
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In Kolla Ansible, :kolla-ansible-doc:`Nova cells are configured
<reference/compute/nova-cells-guide>` via group variables. For example, to
configure ``cell0001`` the following file could be created:

.. code-block:: yaml
   :caption: ``$KAYOBE_CONFIG_PATH/kolla/inventory/group_vars/cell0001/all``

   ---
   nova_cell_name: cell0001
   nova_cell_novncproxy_group: cell0001-vnc
   nova_cell_conductor_group: cell0001-control
   nova_cell_compute_group: cell0001-compute

Passwords
---------

Kolla Ansible auto-generates passwords to a file, ``passwords.yml``. Kayobe
handles the orchestration of this, as well as encryption of the file using an
Ansible Vault password specified in the ``KAYOBE_VAULT_PASSWORD`` environment
variable, if present. The file is generated to
``$KAYOBE_CONFIG_PATH/kolla/passwords.yml``, and should be stored along with
other Kayobe configuration files. This file should not be manually modified.

``kolla_ansible_custom_passwords``
    Dictionary containing custom passwords to add or override in the Kolla
    passwords file. Default is ``{{ kolla_ansible_default_custom_passwords
    }}``, which contains SSH keys for use by Kolla Ansible and Bifrost.

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

Control Plane Services
======================

Kolla Ansible provides a flexible mechanism for configuring the services that
it deploys. Kayobe adds some commonly required configuration options to the
defaults provided by Kolla Ansible, but also allows for the free-form
configuration supported by Kolla Ansible. The :kolla-ansible-doc:`Kolla Ansible
documentation <>` should be used as a reference.

Enabling Services
-----------------

Services deployed by Kolla Ansible are enabled via flags.

``kolla_enable_<service or feature>``
    There are various flags that can be used to enable features. These map to
    variables named ``enable_<service or feature>`` in Kolla Ansible. The
    default set of enabled services and features is the same as in Kolla
    ansible, except that Ironic is enabled by default in Kayobe.

Example: enabling a service
^^^^^^^^^^^^^^^^^^^^^^^^^^^

A common task is enabling a new OpenStack service. This may be done via the
``kolla_enable_*`` flags, for example:

.. code-block:: yaml
   :caption: ``$KAYOBE_CONFIG_PATH/kolla.yml``

   ---
   kolla_enable_swift: true

Note that in some cases additional configuration may be required to
successfully deploy a service - check the :kolla-ansible-doc:`Kolla Ansible
configuration reference <reference>`.

Service Configuration
---------------------

Kolla-ansible's flexible configuration is described in the
:kolla-ansible-doc:`Kolla Ansible service configuration documentation
<admin/advanced-configuration.html#openstack-service-configuration-in-kolla>`.
We won't duplicate that here, but essentially it involves creating files under
a directory which for users of kayobe will be ``$KOLLA_CONFIG_PATH/config``. In
kayobe, files in this directory are auto-generated and managed by kayobe.
Instead, users should create files under ``$KAYOBE_CONFIG_PATH/kolla/config``
with the same directory structure.  These files will be templated using Jinja2,
merged with kayobe's own configuration, and written out to
``$KOLLA_CONFIG_PATH/config``.

The following files, if present, will be templated and provided to
Kolla Ansible.  All paths are relative to ``$KAYOBE_CONFIG_PATH/kolla/config``.
Note that typically Kolla Ansible does not use the same wildcard patterns, and
has a more restricted set of files that it will process.  In some cases, it may
be necessary to inspect the Kolla Ansible configuration tasks to determine
which files are supported.

.. table:: Kolla-ansible configuration files

   =============================== =======================================================
   File                            Purpose
   =============================== =======================================================
   ``backup.my.cnf``               Mariabackup configuration.
   ``barbican.conf``               Barbican configuration.
   ``barbican/*``                  Extended Barbican configuration.
   ``blazar.conf``                 Blazar configuration.
   ``blazar/*``                    Extended Blazar configuration.
   ``ceilometer.conf``             Ceilometer configuration.
   ``ceilometer/*``                Extended Ceilometer configuration.
   ``ceph.conf``                   Ceph configuration.
   ``ceph/*``                      Extended Ceph configuration.
   ``cinder.conf``                 Cinder configuration.
   ``cinder/*``                    Extended Cinder configuration.
   ``cloudkitty.conf``             CloudKitty configuration.
   ``cloudkitty/*``                Extended CloudKitty configuration.
   ``designate.conf``              Designate configuration.
   ``designate/*``                 Extended Designate configuration.
   ``fluentd/filter``              Fluentd filter configuration.
   ``fluentd/input``               Fluentd input configuration.
   ``fluentd/output``              Fluentd output configuration.
   ``galera.cnf``                  MariaDB configuration.
   ``glance.conf``                 Glance configuration.
   ``glance/*``                    Extended Glance configuration.
   ``global.conf``                 Global configuration for all OpenStack services.
   ``gnocchi.conf``                Gnocchi configuration.
   ``gnocchi/*``                   Extended Gnocchi configuration.
   ``grafana.ini``                 Grafana configuration.
   ``grafana/*``                   Extended Grafana configuration.
   ``haproxy/*``                   Main HAProxy configuration.
   ``haproxy-config/*``            Modular HAProxy configuration.
   ``heat.conf``                   Heat configuration.
   ``heat/*``                      Extended heat configuration.
   ``horizon/*``                   Extended horizon configuration.
   ``influx*``                     InfluxDB configuration.
   ``ironic-inspector.conf``       Ironic inspector configuration.
   ``ironic.conf``                 Ironic configuration.
   ``ironic/*``                    Extended ironic configuration.
   ``kafka.server.properties``     Kafka configuration.
   ``kafka/*``                     Extended Kafka configuration.
   ``keepalived/*``                Extended keepalived configuration.
   ``keystone.conf``               Keystone configuration.
   ``keystone/*``                  Extended keystone configuration.
   ``magnum.conf``                 Magnum configuration.
   ``magnum/*``                    Extended magnum configuration.
   ``manila.conf``                 Manila configuration.
   ``manila/*``                    Extended manila configuration.
   ``mariadb/*``                   Extended MariaDB configuration.
   ``monasca/*``                   Extended Monasca configuration.
   ``murano.conf``                 Murano configuration.
   ``murano/*``                    Extended murano configuration.
   ``neutron.conf``                Neutron configuration.
   ``neutron/ml2_conf.ini``        Neutron ML2 configuration.
   ``neutron/*``                   Extended neutron configuration.
   ``nova.conf``                   Nova configuration.
   ``nova/*``                      Extended nova configuration.
   ``octavia.conf``                Octavia configuration.
   ``octavia/*``                   Extended Octavia configuration.
   ``sahara.conf``                 Sahara configuration.
   ``sahara/*``                    Extended sahara configuration.
   ``storm/*``                     Extended Storm configuration.
   ``swift/*``                     Extended swift configuration.
   ``zookeeper.cfg``               Zookeeper configuration.
   ``zookeeper/*``                 Extended Zookeeper configuration.
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
