Arista Switch
=============

This role configures Arista switches using the `eos` Ansible
modules.  It provides a fairly minimal abstraction of the configuration
interface provided by the `eos` modules, allowing for application of
arbitrary switch configuration options.

Requirements
------------

The Ansible network modules for Arista require EOS 4.15 or later.

The switches should be configured to allow SSH access.

Role Variables
--------------

`arista_switch_provider` is authentication provider information passed as the
`provider` argument to the `eos` modules.

`arista_switch_config` is a list of configuration lines to apply to the switch,
and defaults to an empty list.

`arista_switch_interface_config` contains interface configuration. It is a dict
mapping switch interface names to configuration dicts. Each dict may contain
the following items:

- `description` - a description to apply to the interface.
- `config` - a list of per-interface configuration.

Dependencies
------------

None

Example Playbook
----------------

The following playbook configures hosts in the `arista-switches` group.
It assumes host variables for each switch holding the host, username and
passwords.  It applies global configuration for LLDP, and enables two
10G ethernet interfaces as switchports.

    ---
    - name: Ensure Arista switches are configured
      hosts: arista-switches
      gather_facts: no
      roles:
        - role: arista-switch
          arista_switch_provider:
            host: "{{ switch_host }}"
            username: "{{ switch_user }}"
            password: "{{ switch_password }}"
            transport: cli
            authorize: yes
            auth_pass: "{{ switch_auth_pass }}"
            timeout: 60
          arista_switch_config:
            - "lldp run"
            - "lldp tlv-select system-name"
            - "lldp tlv-select management-address"
            - "lldp tlv-select port-description"
          arista_switch_interface_config:
            Et4/5:
              description: server-1
              config:
                - "no shutdown"
                - "switchport"
            Et4/7:
              description: server-2
              config:
                - "no shutdown"
                - "switchport"

Author Information
------------------

- Stig Telfer (<stig@stackhpc.com>)

Based on the dell-switch role by Mark Goddard (<mark@stackhpc.com>)
