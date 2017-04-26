DRAC Boot Mode
==============

Ansible role to set the BIOS boot mode for a Dell server with a DRAC.

Requirements
------------

None

Role Variables
--------------

`drac_boot_mode`: Set this to the required boot mode.

`drac_retries`: Number of times to attempt to perform write operations.

`drac_delay`: Delay between successive write operations.

Example Playbook
----------------

The following playbook sets the boot mode of a host to 'BIOS'.

    ---
    - name: Ensure DRAC boot mode is BIOS
      hosts: dracs
      roles:
        - role: drac-boot-mode
          drac_boot_mode: bios

Author Information
------------------

- Mark Goddard (<mark@stackhpc.com>)
