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
(e.g. ``ansible_user_uid`` and ``ansible_python``) differing.

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
