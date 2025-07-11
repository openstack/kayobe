JunOS Switch
============

This role configures Juniper switches using the `junipernetworks.junos` Ansible
collection. It provides a fairly minimal abstraction of the configuration
interface provided by the collection, allowing for application of arbitrary
switch configuration options.

Requirements
------------

The switches should be configured to allow access to NETCONF via SSH.

Role Variables
--------------

`junos_switch_config_format` is the format of configuration in
`junos_switch_config` and `junos_switch_interface_config`. May be one of `set`,
`text` or `json`.

`junos_switch_config` is a list of configuration lines to apply to the switch,
and defaults to an empty list.

`junos_switch_interface_config` contains interface configuration. It is a dict
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
        - role: junos-switch
          junos_switch_config:
            - "protocols {"
            - "    lldp {"
            - "        interface all;"
            - "    }"
            - "}"
          junos_switch_interface_config:
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
