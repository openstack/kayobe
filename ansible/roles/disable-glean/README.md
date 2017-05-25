Disable Glean
=============

Ansible role to disable services and remove artifacts left after using
[Glean](https://github.com/openstack-infra/glean>).

Glean enables DHCP on all network interfaces that are not explicitly
configured.  If no DHCP server is configured to make an offer to these
interfaces, they will time out on boot and cause the network service to fail.

Requirements
------------

None

Role Variables
--------------

None

Dependencies
------------

None

Example Playbook
----------------

    ---
    - hosts: all
      roles:
        - role: disable-glean

Author Information
------------------

- Mark Goddard (<mark@stackhpc.com>)
