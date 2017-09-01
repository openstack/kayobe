Inspection Store
================

Ironic inspector can make use of Swift to store introspection data. Not all
OpenStack deployments feature Swift, so it may be useful to provide a minimal
HTTP interface that emulates Swift for storing ironic inspector's introspection
data. This role deploys such an interface using nginx. Note that no
authentication mechanism is provided.

Requirements
------------

Docker engine should be running on the target system.

Role Variables
--------------

Dependencies
------------

The `docker-py` python package is required on the target system.

Example Playbook
----------------

The following playbook deploys an inspection store.

    ---
    - hosts: all

      roles:
        - role: inspection-store

Author Information
------------------

- Mark Goddard (<mark@stackhpc.com>)
