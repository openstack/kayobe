=====
Usage
=====

Command Line Interface
======================

.. note::

   Where a prompt starts with ``(kayobe)`` it is implied that the user has
   activated the Kayobe virtualenv. This can be done as follows::

       $ source kayobe/bin/activate

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

If Ansible vault has been used to encrypt Kayobe configuration files, it will
be necessary to provide the ``kayobe`` command with access to vault password.
There are three options for doing this:

Prompt
    Use ``kayobe --ask-vault-pass`` to prompt for the password.
File
    Use ``kayobe --vault-password-file <file>`` to read the password from a
    (plain text) file.
Environment variable
    Export the environment variable ``KAYOBE_VAULT_PASSWORD`` to read the
    password from the environment.

