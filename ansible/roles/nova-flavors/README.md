Nova Flavors
============

This role can be used to register flavors in nova using the
os\_nova\_flavor module.

Requirements
------------

The OpenStack nova API should be accessible from the target host.

Role Variables
--------------

`nova_flavors_venv` is a path to a directory in which to create a
virtualenv.

`nova_flavors_auth_type` is an authentication type compatible with
the `auth_type` argument of `os_*` Ansible modules.

`nova_flavors_auth` is a dict containing authentication information
compatible with the `auth` argument of `os_*` Ansible modules.

`nova_flavors` is a list of nova flavors to register. Each item should be a
dict containing the items 'name', 'ram', 'disk', and 'vcpus'. Optionally, the
dict may contain 'ephemeral' and 'swap' items.

Dependencies
------------

This role depends on the Kayobe `shade` role.

Example Playbook
----------------

The following playbook registers a nova flavor.

    ---
    - name: Ensure nova flavors are registered
      hosts: nova-api
      roles:
        - role: nova-flavors
          nova_flavors_venv: "~/nova-flavors-venv"
          nova_flavors_auth_type: "password"
          nova_flavors_auth:
            project_name: <keystone project>
            username: <keystone user>
            password: <keystone password>
            auth_url: <keystone auth URL>
          nova_flavors:
            name: flavor-1
            ram: 1024
            disk: 1024
            vcpus: 2

Author Information
------------------

- Mark Goddard (<mark@stackhpc.com>)
