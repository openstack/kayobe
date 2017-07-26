Libvirt Host
============

This role configures a host as a Libvirt/KVM hypervisor. It can also configure
storage pools and networks on the host.

Requirements
------------

The host should have Virtualization Technology (VT) enabled.

Role Variables
--------------

`libvirt_host_networks` is a list of pools to define and start. Each item
should be a dict containing the following items:
- `name` The name of the pool.
- `type` The type of the pool, currently only `dir` is supported.
- `capacity`  The capacity, in bytes, of the pool.
- `path` The absolute path to the pool's backing directory.
- `mode` The access mode of the pool.
- `owner` The owner of the pool.
- `group` The group of the pool.

`libvirt_host_networks` is a list of networks to define and start. Each item
should be a dict containing the following items:
- `name` The name of the network.
- `mode` The forwarding mode of the network, currently only `bridge` is
  supported.
- bridge` The name of the bridge interface for this network.

Dependencies
------------

None

Example Playbook
----------------

    ---
    - name: Ensure that Libvirt is configured
      hosts: all
      roles:
        - role: libvirt-host
          libvirt_host_pools:
            - name: my-pool
              type: dir
              capacity: 1024
              path: /path/to/pool
              mode: 0755
              owner: my-user
              group: my-group
          libvirt_host_networks:
            - name: br-example
              mode: bridge
              bridge: br-example

Author Information
------------------

- Mark Goddard (<mark@stackhpc.com>)
