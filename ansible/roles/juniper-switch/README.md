Juniper Switch
==============

This role configures Juniper switches using the `junos` Ansible modules.  It
provides a fairly minimal abstraction of the configuration interface provided
by the `junos` modules, allowing for application of arbitrary switch
configuration options.

Requirements
------------

The switches should be configured to allow SSH access.

Role Variables
--------------

`juniper_switch_delegate_to` is the host on which to execute the `junos` Ansible
modules.

`juniper_switch_provider` is authentication provider information passed as the
`provider` argument to the `junos` modules.

`juniper_switch_config` is a list of configuration lines to apply to the switch,
and defaults to an empty list.

`juniper_switch_interface_config` contains interface configuration. It is a dict
mapping switch interface names to configuration dicts. Each dict may contain
the following items:

- `description` - a description to apply to the interface.
- `config` - a list of per-interface configuration.

Dependencies
------------

None

Example Playbook
----------------

The following playbook configures hosts in the `junos-switches` group.
It assumes host variables for each switch holding the host, username and
passwords.  It applies global configuration for LLDP, and enables two
10G ethernet interfaces.

    ---
    - name: Ensure Junos switches are configured
      hosts: junos-switches
      gather_facts: no
      roles:
        - role: juniper-switch
          juniper_switch_delegate_to: localhost
          juniper_switch_provider:
            host: "{{ switch_host }}"
            username: "{{ switch_user }}"
            password: "{{ switch_password }}"
          juniper_switch_config:
            - "protocols {"
            - "    lldp {"
            - "        interface all;"
            - "    }"
            - "}"
          juniper_switch_interface_config:
            xe-1/1/1:
              description: server-1
              config:
                - "enable"
            xe-1/1/2:
              description: server-2
              config:
                - "enable"

Author Information
------------------

- Mark Goddard (<mark@stackhpc.com>)
