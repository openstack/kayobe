===========
Development
===========

Source Code Orientation
=======================

There are a number of layers to Kayobe, so here we provide a few pointers to
the major parts.

CLI
---

The Command Line Interface (CLI) is built using the `cliff
<https://pypi.org/project/cliff/>`__ library. Commands are exposed as Python
entry points in `setup.cfg
<https://opendev.org/openstack/kayobe/src/branch/master/setup.cfg>`__. These
entry points map to classes in `kayobe/cli/commands.py
<https://opendev.org/openstack/kayobe/src/branch/master/kayobe/cli/commands.py>`__.
The helper modules `kayobe/ansible.py
<https://opendev.org/openstack/kayobe/src/branch/master/kayobe/ansible.py>`__
and `kayobe/kolla_ansible.py
<https://opendev.org/openstack/kayobe/src/branch/master/kayobe/kolla_ansible.py>`__
are used to execute Kayobe playbooks and Kolla Ansible commands respectively.

Ansible
-------

Kayobe's Ansible playbooks live in `ansible/*.yml
<https://opendev.org/openstack/kayobe/src/branch/master/ansible>`__, and these
typically execute roles in `ansible/roles/
<https://opendev.org/openstack/kayobe/src/branch/master/ansible/roles>`__.
Global variable defaults are defined in group variable files in
`ansible/inventory/group_vars/all/
<https://opendev.org/openstack/kayobe/src/branch/master/ansible/inventory/group_vars/all/>`__
and these typically map to commented out variables in the configuration files
in `etc/kayobe/*.yml
<https://opendev.org/openstack/kayobe/src/branch/master/etc/kayobe/>`__.
A number of custom Jinja filters exist in `ansible/filter_plugins/*.py
<https://opendev.org/openstack/kayobe/src/branch/master/ansible/filter_plugins>`__.
Kayobe depends on roles and collections hosted on Ansible Galaxy, and these and
their version requirements are defined in `requirements.yml
<https://opendev.org/openstack/kayobe/src/branch/master/requirements.yml>`__.

Ansible Galaxy
==============

Kayobe uses a number of Ansible roles and collections hosted on Ansible Galaxy.
The role dependencies are tracked in ``requirements.yml``, and specify required
versions. The process for changing a Galaxy role or collection is as follows:

#. If required, develop changes for the role or collection. This may be done
   outside of Kayobe, or by modifying the code in place during development. If
   upstream changes to the code have already been made, this step can be
   skipped.
#. Commit changes to the role or collection, typically via a Github pull
   request.
#. Request that a tagged release of the role or collection be made, or make one
   if you have the necessary privileges.
#. Ensure that automatic imports are configured for the repository using e.g. a
   webhook notification, or perform a manual import of the role on Ansible
   Galaxy.
#. Modify the version in ``requirements.yml`` to match the new release of the
   role or collection.
