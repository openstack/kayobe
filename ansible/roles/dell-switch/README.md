Dell Switch
===========

This role configures Dell switches using the `dellemc.os6`, `dellemc.os9`, or
`dellemc.os10` Ansible collections. It provides a fairly minimal abstraction of
the configuration interface provided by the collections, allowing for
application of arbitrary switch configuration options.

Requirements
------------

The switches should be configured to allow SSH access.

Role Variables
--------------

`dell_switch_type` is the type of Dell switch. One of `dellos6`, `dellos9`, or
`dellos10`.

`dell_switch_config` is a list of configuration lines to apply to the switch,
and defaults to an empty list.

`dell_switch_interface_config` contains interface configuration. It is a dict
mapping switch interface names to configuration dicts. Each dict may contain
the following items:

- `description` - a description to apply to the interface.
- `config` - a list of per-interface configuration.

Dependencies
------------

None

Example Playbook
----------------

The following playbook configures hosts in the `dellos9-switches` group.
It assumes host variables for each switch holding the host, username and
passwords.  It applies global configuration for LLDP, and enables two
10G ethernet interfaces as switchports.

    ---
    - name: Ensure DellOS switches are configured
      hosts: dellos9-switches
      gather_facts: no
      roles:
        - role: dell-switch
          dell_switch_type: "dellos9"
          dell_switch_config:
            - "protocol lldp"
            - " advertise dot3-tlv max-frame-size"
            - " advertise management-tlv management-address system-description system-name"
            - " advertise interface-port-desc"
            - " no disable"
            - " exit"
          dell_switch_interface_config:
            Te1/1/1:
              description: server-1
              config:
                - "no shutdown"
                - "switchport"
            Te1/1/2:
              description: server-2
              config:
                - "no shutdown"
                - "switchport"

Author Information
------------------

- Mark Goddard (<mark@stackhpc.com>)
