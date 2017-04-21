Ironic Python Agent (IPA) Image Build
=====================================

This role can be used to build kernel and ramdisk images for OpenStack Ironic
Python Agent (IPA).

Requirements
------------

None

Role Variables
--------------

`ipa_build_venv` is a path to a directory in which to create a virtualenv.

`ipa_build_install_epel`: Whether to install EPEL repository package.

`ipa_build_install_package_dependencies`: Whether to install package
dependencies.

`ipa_build_cache_path`: Path to directory in which to store built images.

`ipa_build_source_url`: URL of IPA source repository.

`ipa_build_source_version`: Version of IPA source repository.

`ipa_build_upper_constraints_file_url`: URL of IPA upper constraints file.

`ipa_build_custom_upper_constraints`: Custom python package version constraints
for IPA. Dict mapping package name to upper version constraint.

`ipa_build_kernel_name`: Name of kernel image to save.

`ipa_build_ramdisk_name`: Name of ramdisk image to save.

`ipa_build_force`: Whether to force rebuilding images when they already exist.

Dependencies
------------

None

Example Playbook
----------------

The following playbook installs openstackclient in a virtualenv.

    ---
    - name: Ensure Ironic Python Agent (IPA) images are built
      hosts: localhost
      roles:
        - role: ipa-build
          ipa_build_venv: "~/ipa-build-venv"
          ipa_build_cache_path: "~/ipa-build-cache"
          ipa_build_source_url: "https://github.com/openstack/ironic-python-agent"
          ipa_build_source_version: "master"
          ipa_build_kernel_name: "ipa.vmlinuz"
          ipa_build_ramdisk_name: "ipa.initramfs"

Author Information
------------------

- Mark Goddard (<mark@stackhpc.com>)
