AlliedWare Plus Switch
======================

This role configures AlliedWare Plus switches using the
`alliedtelesis.awplus.awplus_config` Ansible module. It provides a fairly
minimal abstraction of the configuration interface provided by the
`awplus_config` module, allowing for application of arbitrary switch
configuration options.

Requirements
------------

The switches should be configured to allow SSH access.

The `alliedtelesis.awplus` Ansible collection must be installed.

Role Variables
--------------

`alliedware_plus_switch_config` is a list of configuration lines to apply to
the switch, and defaults to an empty list.

`alliedware_plus_switch_interface_config` contains interface configuration. It
is a dict mapping switch interface names to configuration dicts, and defaults
to an empty dict. Each dict may contain the following items:

- `description` - an optional description to apply to the interface.
- `config` - a list of per-interface configuration commands.

`alliedware_plus_switch_save` controls whether the running configuration is
saved to the startup configuration when they differ, including any previously
unsaved changes. Defaults to `false`.

Dependencies
------------

None

Example Playbook
----------------

The following playbook configures hosts in the `alliedware-plus-switches`
group. It assumes host variables for each switch holding the host and SSH
credentials.

    ---
    - name: Ensure AlliedWare Plus switches are configured
      hosts: alliedware-plus-switches
      gather_facts: no
      vars:
        ansible_connection: ansible.netcommon.network_cli
        ansible_network_os: alliedtelesis.awplus.awplus
      roles:
        - role: alliedware-plus-switch
          alliedware_plus_switch_config:
            - "vlan database"
            - " vlan 1000,1001 state enable"
          alliedware_plus_switch_interface_config:
            port1.0.1:
              description: server-1
              config:
                - "no shutdown"
                - "switchport"
                - "switchport mode trunk"
                - "switchport trunk native vlan 1000"
                - "switchport trunk allowed vlan add 1001"
            port1.0.2:
              description: server-2
              config:
                - "no shutdown"
                - "switchport"
                - "switchport mode trunk"
                - "switchport trunk native vlan 1000"
                - "switchport trunk allowed vlan add 1001"

Author Information
------------------

- Pierre Riteau (<pierre@stackhpc.com>)
