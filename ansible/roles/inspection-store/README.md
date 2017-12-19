Inspection Store
================

Ironic inspector can make use of Swift to store introspection data. Not all
OpenStack deployments feature Swift, so it may be useful to provide a minimal
HTTP interface that emulates Swift for storing ironic inspector's introspection
data. This role deploys such an interface using nginx. Note that no
authentication mechanism is provided.

Requirements
------------

The host executing the role has the following requirements:

* Docker engine
* Python ``docker >= 2.0.0``

Role Variables
--------------

Dependencies
------------

None

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
