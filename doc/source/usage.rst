=====
Usage
=====

Command Line Interface
======================

.. note::

   Where a prompt starts with ``(kayobe)`` it is implied that the user has
   activated the Kayobe virtualenv. This can be done as follows::

       $ source /path/to/venv/bin/activate

   To deactivate the virtualenv::

       (kayobe) $ deactivate

To see information on how to use the ``kayobe`` CLI and the commands it
provides::

    (kayobe) $ kayobe help

As the ``kayobe`` CLI is based on the ``cliff`` package (as used by the
``openstack`` client), it supports tab auto-completion of subcommands.  This
can be activated by generating and then sourcing the bash completion script::

    (kayobe) $ kayobe complete > kayobe-complete
    (kayobe) $ source kayobe-complete

Working with Ansible Vault
--------------------------

If Ansible Vault has been used to encrypt Kayobe configuration files, it will
be necessary to provide the ``kayobe`` command with access to vault password.
There are four options for doing this:

Prompt
    Use ``kayobe --ask-vault-pass`` to prompt for the password.
File
    Use ``kayobe --vault-password-file <file>`` to read the password from a
    (plain text) file.
Environment variable: ``KAYOBE_VAULT_PASSWORD``
    Export the environment variable ``KAYOBE_VAULT_PASSWORD`` to read the
    password from the environment.
Environment variable: ``ANSIBLE_VAULT_PASSWORD_FILE``
    Export the environment variable ``ANSIBLE_VAULT_PASSWORD_FILE`` to read the
    password from a (plain text) file, with the path to that file being read
    from the environment.

Limiting Hosts
--------------

Sometimes it may be necessary to limit execution of kayobe or kolla-ansible
plays to a subset of the hosts.  The ``--limit <SUBSET>`` argument allows the
kayobe ansible hosts to be limited.  The ``--kolla-limit <SUBSET>`` argument
allows the kolla-ansible hosts to be limited.  These two options may be
combined in a single command.  In both cases, the argument provided should be
an `Ansible host pattern
<http://docs.ansible.com/ansible/latest/intro_patterns.html>`_, and will
ultimately be passed to ``ansible-playbook`` as a ``--limit`` argument.

.. _usage-tags:

Tags
----

`Ansible tags <http://docs.ansible.com/ansible/latest/playbooks_tags.html>`_
provide a useful mechanism for executing a subset of the plays or tasks in a
playbook.  The ``--tags <TAGS>`` argument allows execution of kayobe ansible
playbooks to be limited to matching plays and tasks.  The ``--kolla-tags
<TAGS>`` argument allows execution of kolla-ansible ansible playbooks to be
limited to matching plays and tasks.  The ``--skip-tags <TAGS>`` and
``--kolla-skip-tags <TAGS>`` arguments allow for avoiding execution of matching
plays and tasks.

Check and diff mode
-------------------

Ansible supports `check and diff modes
<https://docs.ansible.com/ansible/latest/user_guide/playbooks_checkmode.html>`_,
which can be used to improve visibility into changes that would be made on
target systems. The Kayobe CLI supports the ``--check`` argument, and since
11.0.0, the ``--diff`` argument. Note that these modes are not always
guaranteed to work, when some tasks are dependent on earlier ones.

Avoiding privilege escalation on the control host
-------------------------------------------------

.. note::

    This means that kayobe will not be able to install OS packages or use paths
    that are not writable for your user.

It is possible to avoid privilege escalation on the control host. To use this feature set
the following config option:

.. code-block:: yaml
   :caption: ``$KAYOBE_CONFIG_PATH/globals.yml``

   kayobe_control_host_become: false
