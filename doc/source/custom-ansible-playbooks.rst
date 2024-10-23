========================
Custom Ansible Playbooks
========================

Kayobe supports running custom Ansible playbooks located outside of the kayobe
project.  This provides a flexible mechanism for customising a control plane.
Access to the kayobe variables is possible, ensuring configuration does not
need to be repeated.

Kayobe Custom Playbook API
==========================

Explicitly allowing users to run custom playbooks with access to the kayobe
variables elevates the variable namespace and inventory to become an interface.
This raises questions about the stability of this interface, and the guarantees
it provides.

The following guidelines apply to the custom playbook API:

* Only variables defined in the kayobe configuration files under ``etc/kayobe``
  are supported.
* The groups defined in ``etc/kayobe/inventory/groups`` are supported.
* Any change to a supported variable (rename, schema change, default value
  change, or removal) or supported group (rename or removal) will follow a
  deprecation period of one release cycle.
* Kayobe's internal roles may not be used.

Note that these are guidelines, and exceptions may be made where appropriate.

Running Custom Ansible Playbooks
================================

Run one or more custom ansible playbooks::

    (kayobe) $ kayobe playbook run <playbook>[ <playbook>...]

Playbooks do not by default have access to the Kayobe playbook group variables,
filter plugins, and test plugins, since these are relative to the current
playbook's directory.  This can be worked around by creating symbolic links to
the Kayobe repository from the Kayobe configuration.

Packaging Custom Playbooks With Configuration
=============================================

The kayobe project encourages its users to manage configuration for a cloud
using version control, based on the `kayobe-config repository
<https://opendev.org/openstack/kayobe-config>`_.  Storing custom Ansible
playbooks in this repository makes a lot of sense, and kayobe has special
support for this.

It is recommended to store custom playbooks in
``$KAYOBE_CONFIG_PATH/ansible/``.  It is also possible to use the following
subdirectories, and since the Zed 13.0.0 release these will be available to all
Kayobe playbook executions.

* ``roles``
* ``collections``
* ``action_plugins``
* ``filter_plugins``
* ``test_plugins``

Note that since the Zed 13.0.0 release, it is no longer necessary to create
symlinks in order to use Kayobe's roles, collections or plugins. Existing
symlinks may be removed.

Ansible Galaxy
--------------

Ansible Galaxy provides a means for sharing Ansible roles and collections.
Kayobe configuration may provide a Galaxy requirements file that defines roles
and collections to be installed from Galaxy.  These roles and collections may
then be used by custom playbooks.

Galaxy dependencies may be defined in
``$KAYOBE_CONFIG_PATH/ansible/requirements.yml``.  These roles and collections
will be installed in ``$KAYOBE_CONFIG_PATH/ansible/roles/`` and
``$KAYOBE_CONFIG_PATH/ansible/collections`` when bootstrapping the Ansible
control host::

    (kayobe) $ kayobe control host bootstrap

And updated when upgrading the Ansible control host::

    (kayobe) $ kayobe control host upgrade

Example: roles
==============

The following example adds a ``foo.yml`` playbook to a set of kayobe
configuration.  The playbook uses a Galaxy role, ``bar.baz``.

Here is the kayobe configuration repository structure::

    etc/kayobe/
        ansible/
            foo.yml
            requirements.yml
            roles/
        bifrost.yml
    ...

Here is the playbook, ``ansible/foo.yml``::

    ---
    - hosts: controllers
      roles:
        - name: bar.baz

Here is the Galaxy requirements file, ``ansible/requirements.yml``::

    ---
    roles:
      - bar.baz

We should first install the Galaxy role dependencies, to download the
``bar.baz`` role::

    (kayobe) $ kayobe control host bootstrap

Then, to run the ``foo.yml`` playbook::

    (kayobe) $ kayobe playbook run $KAYOBE_CONFIG_PATH/ansible/foo.yml

Example: collections
====================

The following example adds a ``foo.yml`` playbook to a set of kayobe
configuration.  The playbook uses a role from a Galaxy collection,
``bar.baz.qux``.

Here is the kayobe configuration repository structure::

    etc/kayobe/
        ansible/
            collections/
            foo.yml
            requirements.yml
        bifrost.yml
    ...

Here is the playbook, ``ansible/foo.yml``::

    ---
    - hosts: controllers
      roles:
        - name: bar.baz.qux

Here is the Galaxy requirements file, ``ansible/requirements.yml``::

    ---
    collections:
      - bar.baz

We should first install the Galaxy dependencies, to download the ``bar.baz``
collection::

    (kayobe) $ kayobe control host bootstrap

Then, to run the ``foo.yml`` playbook::

    (kayobe) $ kayobe playbook run $KAYOBE_CONFIG_PATH/ansible/foo.yml

.. _custom-playbooks-hooks:

Hooks
=====

.. warning::
    Hooks are an experimental feature and the design could change in the future.
    You may have to update your config if there are any changes to the design.
    This warning will be removed when the design has been stabilised.

Hooks allow you to automatically execute custom playbooks at certain points during
the execution of a kayobe command. The point at which a hook is run is referred to
as a ``target``. Please see the :ref:`list of available targets<Hook Targets>`.

Hooks are created by symlinking an existing playbook into the relevant directory under
``$KAYOBE_CONFIG_PATH/hooks``. Kayobe will search the hooks directory for sub-directories
matching ``<command>.<target>.d``, where ``command`` is the name of a kayobe command
with any spaces replaced with dashes, and ``target`` is one of the supported targets for
the command.

For example, when using the command::

    (kayobe) $ kayobe control host bootstrap

kayobe will search the paths:

- ``$KAYOBE_CONFIG_PATH/hooks/control-host-bootstrap/pre.d``
- ``$KAYOBE_CONFIG_PATH/hooks/control-host-bootstrap/post.d``

Any playbooks listed under the ``pre.d`` directory will be run before kayobe executes
its own playbooks and any playbooks under ``post.d`` will be run after. You can affect
the order of the playbooks by prefixing the symlink with a sequence number. The sequence
number must be separated from the hook name with a dash. Playbooks with smaller sequence
numbers are run before playbooks with larger ones. Any ties are broken by alphabetical
ordering.

For example to run the playbook ``foo.yml`` after ``kayobe overcloud host configure``,
you could do the following::

    (kayobe) $ mkdir -p ${KAYOBE_CONFIG_PATH}/hooks/overcloud-host-configure/post.d
    (kayobe) $ cd ${KAYOBE_CONFIG_PATH}/hooks/overcloud-host-configure/post.d
    (kayobe) $ ln -s ../../../ansible/foo.yml 10-foo.yml

The sequence number for the ``foo.yml`` playbook is ``10``.

Hook execution can be disabled with ``--skip-hooks``. ``--skip-hooks all`` will halt hook execution altogether.
``--skip-hooks <pattern>`` will skip playbooks matching the ``<pattern>``.

For example, if the following playbooks exist:

- ``$KAYOBE_CONFIG_PATH/hooks/control-host-bootstrap/pre.d/example1.yml``
- ``$KAYOBE_CONFIG_PATH/hooks/control-host-bootstrap/pre.d/example2.yml``
- ``$KAYOBE_CONFIG_PATH/hooks/control-host-bootstrap/post.d/example1.yml``

And the following command is used::

    (kayobe) $ kayobe control host bootstrap --skip-hooks example1

Only ``$KAYOBE_CONFIG_PATH/hooks/control-host-bootstrap/pre.d/example2.yml`` will be executed.

This example assumes that the term ``example1`` does not appear in
``$KAYOBE_CONFIG_PATH``. If it did, all hooks would be skipped.

Failure handling
----------------

If the exit status of any playbook, including built-in playbooks and custom hooks,
is non-zero, kayobe will not run any subsequent hooks or built-in kayobe playbooks.
Ansible provides several methods for preventing a task from producing a failure. Please
see the `Ansible documentation <https://docs.ansible.com/ansible/latest/user_guide/playbooks_error_handling.html>`_
for more details. Below is an example showing how you can use the ``ignore_errors`` option
to prevent a task from causing the playbook to report a failure::

  ---
  - name: Failure example
    hosts: localhost
    tasks:
      - name: Deliberately fail
        fail:
        ignore_errors: true

A failure in the ``Deliberately fail`` task would not prevent subsequent tasks, hooks,
and playbooks from running.

.. _Hook Targets:

Targets
-------
The following targets are available for all commands:

.. list-table:: all commands
   :widths: 10 500
   :header-rows: 1

   * - Target
     - Description
   * - pre
     - Runs before a kayobe command has start executing
   * - post
     - Runs after a kayobe command has finished executing
