Dell Switch BMP
===============

This role configures a network boot environment for Dell switches with Bare
Metal Provisioning (BMP) functionality.

Requirements
------------

The use of an OpenStack Bifrost container deployed using OpenStack
Kolla-ansible is assumed, with the dnsmasq service providing DHCP and nginx
serving the switch OS images.

Role Variables
--------------

`dell_switch_bmp_images` is a list of images to provide a BMP configuration
for, and defaults to an empty list.  Each item should be a dict with the
following items:

- `url` - URL of the image to download.
- `dest`- name of the file to download the image to.
- `match` - dnsmasq match rule to match hosts against.
- `tag` - dnsmasq tag to apply to matching hosts.
- `checksum` - optional checksum of image, in format required for Ansible's
  `get_url` module.

`dell_switch_bmp_http_base_url` is the base URL of HTTP server.

`dell_switch_bmp_httpboot_path` is the path to the HTTP server base directory,
and defaults to `/httpboot`.

Dependencies
------------

None

Example Playbook
----------------

The following playbook configures a network boot environment in the Bifrost
container for s6010-ON switches with the `ONIE-FTOS-9.10.0.1P25.bin` image.

    ---
    # This playbook will configure a Bare Metal Provisioning (BMP) environment for
    # Dell switches on the Bifrost node so that they can be network booted.

    - name: Ensure that a Bare Metal Provisioning (BMP) environment is configured for Dell switches
      hosts: bifrost
      roles:
        - role: dell-switch-bmp
          dell_switch_bmp_images:
            # ONIE installer image for S6010-ON.
            - url: "ftp://ftp.force10networks.com/releases/FTOS_Release/E9.10.0.1P25/S6010/ONIE-FTOS-S6010-9.10.0.1P25.bin"
              checksum: "md5:f94fdfa50dc23f87bf2871ae96b6cff3"
              dest: "onie-installer-x86_64-dell_s6010_c2538-r0"
              match: "option:vendor-class,onie_vendor:x86_64-dell_s6010_c2538-r0"
              tag: "onie"
          # This is the base URL of the Nginx web server on the Bifrost node.
          dell_switch_bmp_http_base_url: "http://10.0.0.1:8080"

Author Information
------------------

- Mark Goddard (<mark@stackhpc.com>)
