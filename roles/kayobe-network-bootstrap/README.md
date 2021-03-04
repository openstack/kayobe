# Kayobe network bootstrap

Ansible role to bootstrap network configuration in CI.

The role creates a bridge interface and a dummy interface, and adds the dummy
interface as a port in the bridge. The bridge is assigned an IP address.

## Role variables

* `bridge_interface`: name of the bridge interface
* `bridge_ip`: IP address to assign to the bridge
* `bridge_prefix`: CIDR prefix to assign to the bridge
* `bridge_port_interface`: name of the bridge port dummy interface
