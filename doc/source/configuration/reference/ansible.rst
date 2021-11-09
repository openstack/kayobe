=======
Ansible
=======

Ansible configuration is described in detail in the `Ansible documentation
<https://docs.ansible.com/ansible/latest/reference_appendices/config.html>`__.
It is explained elsewhere in this guide how to configure Ansible for
:ref:`Kayobe <configuration-kayobe-ansible>` and :ref:`Kolla Ansible
<configuration-kolla-ansible-ansible>`.

In this section we cover some options for tuning Ansible for performance and
scale.

SSH pipelining
==============

SSH pipelining is disabled in Ansible by default, but is generally safe to
enable, and provides a reasonable performance improvement.

.. code-block:: ini
   :caption: ``$KAYOBE_CONFIG_PATH/ansible.cfg``

   [ssh_connection]
   pipelining = True

Forks
=====

By default Ansible executes tasks using a fairly conservative 5 process forks.
This limits the parallelism that allows Ansible to scale. Most Ansible control
hosts will be able to handle far more forks than this. You will need to
experiment to find out the CPU, memory and IO limits of your machine.

For example, to increase the number of forks to 20:

.. code-block:: ini
   :caption: ``$KAYOBE_CONFIG_PATH/ansible.cfg``

   [defaults]
   forks = 20

Fact caching
============

.. note::

   Fact caching will not work correctly in Kayobe prior to the Ussuri release.

By default, Ansible gathers facts for each host at the beginning of every play,
unless ``gather_facts`` is set to ``false``. With a large number of hosts this
can result in a significant amount of time spent gathering facts.

One way to improve this is through Ansible's support for `fact caching
<https://docs.ansible.com/ansible/latest/user_guide/playbooks_variables.html#caching-facts>`__.
In order to make this work with Kayobe, it is necessary to change Ansible's
`gathering
<https://docs.ansible.com/ansible/latest/reference_appendices/config.html#default-gathering>`__
configuration option to ``smart``. Additionally, it is necessary to use
separate fact caches for Kayobe and Kolla Ansible due to some of the facts
(e.g. ``ansible_facts.user_uid`` and ``ansible_facts.python``) differing.

Example
-------

In the following example we configure Kayobe and Kolla Ansible to use fact
caching using the `jsonfile cache plugin
<https://docs.ansible.com/ansible/latest/plugins/cache/jsonfile.html>`__.

.. code-block:: ini
   :caption: ``$KAYOBE_CONFIG_PATH/ansible.cfg``

   [defaults]
   gathering = smart
   fact_caching = jsonfile
   fact_caching_connection = /tmp/kayobe-facts

.. code-block:: ini
   :caption: ``$KAYOBE_CONFIG_PATH/kolla/ansible.cfg``

   [defaults]
   gathering = smart
   fact_caching = jsonfile
   fact_caching_connection = /tmp/kolla-ansible-facts

You may also wish to set the expiration timeout for the cache via ``[defaults]
fact_caching_timeout``.

Fact gathering
==============

Fact filtering
--------------

Filtering of facts can be used to speed up Ansible.  Environments with
many network interfaces on the network and compute nodes can experience very
slow processing with Kayobe and Kolla Ansible. This happens due to the
processing of the large per-interface facts with each task.  To avoid storing
certain facts, we can use the ``kayobe_ansible_setup_filter`` variable, which
is used as the ``filter`` argument to the ``setup`` module.

One case where this is particularly useful is to avoid collecting facts for
virtual tap (beginning with t) and bridge (beginning with q) interfaces
created by Neutron. These facts are large map values which can consume a lot
of resources on the Ansible control host. Kayobe and Kolla Ansible typically
do not need to reference them, so they may be filtered. For example, to
avoid collecting facts beginning with q or t:

.. code-block:: yaml
   :caption: ``$KAYOBE_CONFIG_PATH/globals.yml``

   kayobe_ansible_setup_filter: "ansible_[!qt]*"

Similarly, for Kolla Ansible (notice the similar but different file names):

.. code-block:: yaml
   :caption: ``$KAYOBE_CONFIG_PATH/kolla/globals.yml``

   kolla_ansible_setup_filter: "ansible_[!qt]*"

This causes Ansible to collect but not store facts matching that pattern, which
includes the virtual interface facts. Currently we are not referencing other
facts matching the pattern within Kolla Ansible.  Note that including the
'ansible_' prefix causes meta facts ``module_setup`` and ``gather_subset`` to
be filtered, but this seems to be the only way to get a good match on the
interface facts.

The exact improvement will vary, but has been reported to be as large as 18x on
systems with many virtual interfaces.

Fact gathering subsets
----------------------

It is also possible to configure which subsets of facts are gathered, via
``kayobe_ansible_setup_gather_subset``, which is used as the ``gather_subset``
argument to the ``setup`` module. For example, if one wants to avoid collecting
facts via facter:

.. code-block:: yaml
   :caption: ``$KAYOBE_CONFIG_PATH/globals.yml``

   kayobe_ansible_setup_gather_subset: "all,!facter"

Similarly, for Kolla Ansible (notice the similar but different file names):

.. code-block:: yaml
   :caption: ``$KAYOBE_CONFIG_PATH/kolla/globals.yml``

   kolla_ansible_setup_gather_subset: "all,!facter"

Max failure percentage
======================

It is possible to specify a `maximum failure percentage
<https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_error_handling.html#setting-a-maximum-failure-percentage>`__
using ``kayobe_max_fail_percentage``. By default this is undefined, which is
equivalent to a value of 100, meaning that Ansible will continue execution
until all hosts have failed or completed. For example:

.. code-block:: yaml
   :caption: ``$KAYOBE_CONFIG_PATH/globals.yml``

   kayobe_max_fail_percentage: 50

A max fail percentage may be set for the ``kayobe * host configure`` commands
using ``host_configure_max_fail_percentage``, or for a specific playbook using
``<playbook>_max_fail_percentage`` where ``<playbook>`` is the playbook name
with dashes replaced with underscores and without the ``.yml`` extension. For
example:

.. code-block:: yaml
   :caption: ``$KAYOBE_CONFIG_PATH/globals.yml``

   kayobe_max_fail_percentage: 50
   host_configure_max_fail_percentage: 25
   time_max_fail_percentage: 100
