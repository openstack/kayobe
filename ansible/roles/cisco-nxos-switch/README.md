Cisco NX-OS Switch
==================

This role configures Cisco NX-OS switches using the `cisco.nxos.nxos_config`
Ansible module. It allows global and per-interface configuration commands to
be applied to the switch.

Requirements
------------

The switches should be configured to allow SSH access.

The `cisco.nxos` Ansible collection must be installed.

Role Variables
--------------

`cisco_nxos_switch_config` is a list of configuration lines to apply to the
switch, and defaults to an empty list.

`cisco_nxos_switch_interface_config` is a dict mapping switch interface names
to configuration dicts, and defaults to an empty dict. Each dict contains:

- `description` - an optional description to apply to the interface.
- `config` - a list of per-interface configuration commands.

`cisco_nxos_switch_save` controls whether the running configuration is saved
to the startup configuration when they differ, including any previously unsaved
changes. Defaults to `false`.

Dependencies
------------

None

Example Playbook
----------------

The following playbook configures hosts in the `cisco-nxos-switches` group.
It assumes host variables for each switch holding the host and SSH credentials.
It enables LLDP and configures an Ethernet interface as a switchport.

    ---
    - name: Ensure Cisco NX-OS switches are configured
      hosts: cisco-nxos-switches
      gather_facts: no
      vars:
        ansible_connection: ansible.netcommon.network_cli
        ansible_network_os: cisco.nxos.nxos
      roles:
        - role: cisco-nxos-switch
          cisco_nxos_switch_config:
            - "feature lldp"
          cisco_nxos_switch_interface_config:
            Ethernet1/1:
              description: server-1
              config:
                - "switchport"
                - "switchport mode access"
