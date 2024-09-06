NVUE Switch
===========

This role configures Cumulus switches using the `nvidia.nvue.command` Ansible
module. It provides a fairly minimal abstraction of the configuration interface
provided by the `nvidia.nvue.command` module, allowing for application of
arbitrary switch configuration options.

Requirements
------------

The switches should be configured to allow SSH access.

Role Variables
--------------

`nvue_switch_config` is a list of NVUE commands to apply to the switch, and
defaults to an empty list. Commands must be formatted without the `nv` prefix,
which is added by the `nvidia.nvue.command` module before execution on the
switch.

`nvue_switch_interface_config` contains interface configuration. It is a dict
mapping switch interface names to configuration dicts. Interfaces can be switch
physical interfaces, but also special interfaces such as bridges or bonds. Each
dict may contain the following items:

- `description` - a description to apply to the interface.
- `config` - a list of per-interface configuration, each applied with a `nv
  set interface <interface-name>` prefix.

Dependencies
------------

None

Example Playbook
----------------

The following playbook configures hosts in the `nvue-switches` group. It
applies global configuration to configure a BGP AS and add two EBGP neighbors
using BGP Unnumbered, enables two host interfaces with jumbo frames, and
attaches them to a traditional bridge called `bridge1` configured with an IP
address.

    ---
    - name: Ensure Cumulus switches are configured with NVUE
      hosts: nvue-switches
      gather_facts: no
      roles:
        - role: nvue-switch
          nvue_switch_config:
            - "set router bgp autonomous-system 65000"
            - "set router bgp neighbor swp51 interface remote-as external"
            - "set router bgp neighbor swp52 interface remote-as external"
          nvue_switch_interface_config:
            swp1:
              description: server1
              config:
                - "link mtu 9000"
            swp2:
              description: server2
              config:
                - "link mtu 9000"
            bridge1:
              config:
                - "ip address 10.100.100.1/24"
                - "ports swp1"
                - "ports swp2"

Author Information
------------------

- Michal Nasiadka (<mnasiadka@gmail.com>)
