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

Whilst the kolla passwords file ``kolla/passwords.yml`` should remain encrypted
at all times it can be useful to view the contents of this file to acquire a
password for a given service.
This can be done with ``ansible-vault view`` however if an absolute path is not
provided it will cause the command to fail.
Therefore, to make reading the contents of this file easier for administrators
it is possible to use ``kayobe overcloud service passwords view`` which will
temporarily decrypt and display the contents of ``kolla/passwords.yml`` for the
active kayobe environment.

Limiting Hosts
--------------

Sometimes it may be necessary to limit execution of kayobe or kolla-ansible
plays to a subset of the hosts.  The ``--limit <SUBSET>`` argument allows the
kayobe and kolla-ansible hosts to be limited.  The argument provided should be
an `Ansible host pattern
<http://docs.ansible.com/ansible/latest/intro_patterns.html>`_, and will
ultimately be passed to ``ansible-playbook`` for both kayobe and kolla-ansible
as a ``--limit`` argument.

.. _usage-tags:

Tags
----

`Ansible tags <http://docs.ansible.com/ansible/latest/playbooks_tags.html>`_
provide a useful mechanism for executing a subset of the plays or tasks in a
playbook.  The ``--tags <TAGS>`` argument allows execution of kayobe and
kolla-ansible playbooks to be limited to matching plays and tasks.  The
``--skip-tags <TAGS>`` argument allows for avoiding execution of matching plays
and tasks.

.. note::

    Using tags is not tested in either Kayobe or Kolla-Ansible CI, and as such
    should only be used if you know what you're doing. Proceed with caution.

Kolla Ansible Playbook
----------------------

Some commands that invoke Kolla Ansible support replacing the default
``site.yml`` playbook with a custom one via ``--kolla-playbook``.  This may be
used to specify a playbook that replaces or extends the default playbook, and
needs to execute in the Kolla Ansible context.  For example::

    (kayobe) $ kayobe overcloud service deploy --kolla-playbook /path/to/playbook.yml

The playbook can be called multiple times with different ``kolla_action`` values. You must make the playbook resistant to this, for example by using the ``kolla_action`` variable to conditionally execute tasks. Examples of kolla_action values include:

- ``backup``
- ``bootstrap-servers``
- ``check``
- ``certificates``
- ``config``
- ``config_validate``
- ``deploy``
- ``deploy-containers``
- ``deploy-servers``
- ``destroy``
- ``gather-facts``
- ``migrate-container-engine``
- ``nova-libvirt-cleanup``
- ``octavia-certificates``
- ``post-deploy``
- ``precheck``
- ``prune-images``
- ``pull``
- ``rabbitmq-reset-state``
- ``reconfigure``
- ``stop``
- ``upgrade``

For example, when running ``kayobe overcloud service deploy`` the playbook will be run with ``kolla_action`` set to

- ``precheck``
- ``deploy``
- ``post-deploy``

An example of a task only running against a specific kolla_action value is shown below:

.. code-block:: yaml

    ---
    - name: Example custom playbook with precheck and deploy tasks
      hosts: all
      tasks:
        - name: Assert something during precheck
          assert:
            that:
              - some_variable is defined
          when: kolla_action == 'precheck'

        - name: Do something during deploy
          debug:
            msg: "This will only run during deploy"
          when: kolla_action == 'deploy'

Alternatively, you can make the playbook exit if the kolla_action value is not one that the playbook is designed to handle, removing the need for ``when`` conditions on individual tasks:

.. code-block:: yaml

    ---
    - name: Example guarded custom playbook
      hosts: all
      tasks:
        - name: End play if not deploying
          meta: end_play
          when: kolla_action != 'deploy'

        - name: Do something during deploy
          debug:
            msg: "This will only run during deploy"

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
