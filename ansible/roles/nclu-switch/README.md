NCLU Switch
===========

This role configures Cumulus switches using the `nclu` Ansible module. It
provides a fairly minimal abstraction of the configuration interface provided
by the `nclu` module, allowing for application of arbitrary switch
configuration options.

Requirements
------------

The switches should be configured to allow SSH access.

Role Variables
--------------

`nclu_switch_config` is a list of NCLU commands to apply to the switch, and
defaults to an empty list. Commands must be formatted without the `net` prefix,
which is added by the `nclu` module before execution on the switch.

`nclu_switch_interface_config` contains interface configuration. It is a dict
mapping switch interface names to configuration dicts. Interfaces can be switch
physical interfaces, but also special interfaces such as bridges or bonds. Each
dict may contain the following items:

- `description` - a description to apply to the interface.
- `config` - a list of per-interface configuration, each applied with a `net
  add <type> <interface-name>` prefix.
- `type` - type of interface, e.g. `bond` or `bridge`. If this field is absent,
  the `interface` keyword is used.

Dependencies
------------

None

Example Playbook
----------------

The following playbook configures hosts in the `nclu-switches` group. It
applies global configuration to configure a BGP AS and add two EBGP neighbors
using BGP Unnumbered, enables two host interfaces with jumbo frames, and
attaches them to a traditional bridge called `bridge1` configured with an IP
address.

    ---
    - name: Ensure Cumulus switches are configured with NCLU
      hosts: nclu-switches
      gather_facts: no
      roles:
        - role: nclu-switch
          nclu_switch_config:
            - "add bgp autonomous-system 65000"
            - "add bgp neighbor swp51 interface remote-as external"
            - "add bgp neighbor swp52 interface remote-as external"
          nclu_switch_interface_config:
            swp1:
              description: server1
              config:
                - "mtu 9000"
            swp2:
              description: server2
              config:
                - "mtu 9000"
            bridge1:
              type: bridge
              config:
                - "ip address 10.100.100.1/24"
                - "ports swp1"
                - "ports swp2"

Author Information
------------------

- Pierre Riteau (<pierre@stackhpc.com>)
