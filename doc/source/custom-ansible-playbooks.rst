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

    (kayobe) $ kayobe playbook run <playbook>[, <playbook>...]

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
``$KAYOBE_CONFIG_PATH/ansible/``.  Roles located in
``$KAYOBE_CONFIG_PATH/ansible/roles/`` will be automatically available to
playbooks in this directory.

With this directory layout, the following commands could be used to create
symlinks that allow access to Kayobe's filter plugins, group variables and test
plugins:

.. code-block:: console

   cd ${KAYOBE_CONFIG_PATH}/ansible/
   ln -s ../../../../kayobe/ansible/filter_plugins/ filter_plugins
   ln -s ../../../../kayobe/ansible/group_vars/ group_vars
   ln -s ../../../../kayobe/ansible/test_plugins/ test_plugins

These symlinks can even be committed to the kayobe-config Git repository.

Ansible Galaxy
--------------

Ansible Galaxy provides a means for sharing Ansible roles.  Kayobe
configuration may provide a Galaxy requirements file that defines roles to be
installed from Galaxy.  These roles may then be used by custom playbooks.

Galaxy role dependencies may be defined in
``$KAYOBE_CONFIG_PATH/ansible/requirements.yml``.  These roles will be
installed in ``$KAYOBE_CONFIG_PATH/ansible/roles/`` when bootstrapping the
Ansible control host::

    (kayobe) $ kayobe control host bootstrap

And updated when upgrading the Ansible control host::

    (kayobe) $ kayobe control host upgrade

Example
=======

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
    - bar.baz

We should first install the Galaxy role dependencies, to download the
``bar.baz`` role::

    (kayobe) $ kayobe control host bootstrap

Then, to run the ``foo.yml`` playbook::

    (kayobe) $ kayobe playbook run $KAYOBE_CONFIG_PATH/ansible/foo.yml
