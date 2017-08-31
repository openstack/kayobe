Sysctl
======

This role configures sysctl parameters.

Requirements
------------

None

Role Variables
--------------

`sysctl_file` is the name of a file in which to persist sysctl parameters.

`sysctl_set` is whether to verify token value with the sysctl command and set
with -w if necessary.

`sysctl_parameters` is a dict of sysctl parameters to set.

Dependencies
------------

None

Example Playbook
----------------

This playbook will set the `net.ipv4.ip_forward` parameter to `1`.

    ---
    - hosts: all
      roles:
        - role: sysctl
          sysctl_set: yes
          sysctl_parameters:
            net.ipv4.ip_forward: 1

Author Information
------------------

- Mark Goddard (<mark@stackhpc.com>)
