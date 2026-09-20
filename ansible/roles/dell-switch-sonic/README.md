Dell Switch - SONiC
===================

This role configures Dell switches using the `dellemc.enterprise_sonic`
Ansible collections. It provides a fairly minimal abstraction of
the configuration interface provided by the collections, allowing for
application of arbitrary switch configuration options.

Requirements
------------

The switches should be configured to allow SSH access.

Role Variables
--------------

`dell_switch_sonic_config` is a list of configuration lines to apply to the switch,
and defaults to an empty list.

`dell_switch_sonic_interface_config` contains interface configuration. It is a dict
mapping switch interface names to configuration dicts. Each dict may contain
the following items:

- `description` - a description to apply to the interface.
- `config` - a list of per-interface configuration.

Dependencies
------------

None

Example Playbook
----------------

The following playbook configures hosts in the `dell-switches-sonic` group.
It assumes host variables for each switch holding the host, username and
passwords.  It applies global configuration for LLDP, and enables two
10G ethernet interfaces as switchports.

    ---
    - name: Ensure Dell SONiC switches are configured
      hosts: dell-switches-sonic
      gather_facts: no
      roles:
        - role: dell-switch-sonic
          dell_switch_sonic_config:
            - "lldp enable"
            - "ntp server 10.0.12.34"
          dell_switch_sonic_interface_config:
            Ethernet1:
              description: server-1
              config:
                - "no shutdown"
                - "switchport"
            Ethernet2:
              description: server-2
              config:
                - "no shutdown"

Author Information
------------------

- Matt Crees (<mattc@stackhpc.com>)
