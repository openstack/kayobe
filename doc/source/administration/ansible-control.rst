===================================
Ansible Control Host Administration
===================================

Updating Packages
=================

It is possible to update packages on the Ansible control host.

Package Repositories
--------------------

If using custom DNF package repositories on CentOS or Rocky, it may be
necessary to update these prior to running a package update. To do this, update
the configuration in ``${KAYOBE_CONFIG_PATH}/dnf.yml`` and run the following
command::

    (kayobe) $ kayobe control host configure --tags dnf

Package Update
--------------

To update one or more packages::

    (kayobe) $ kayobe control host package update --packages <package1>,<package2>

To update all eligible packages, use ``*``, escaping if necessary::

    (kayobe) $ kayobe control host package update --packages "*"

To only install updates that have been marked security related::

    (kayobe) $ kayobe control host package update --packages "*" --security

Note that these commands do not affect packages installed in containers, only
those installed on the host.

Kernel Updates
--------------

If the kernel has been updated, you will probably want to reboot the host
to boot into the new kernel. This can be done using a command such as the
following::

    (kayobe) $ kayobe control host command run --command "shutdown -r" --become

Running Commands
================

It is possible to run a command on the host::

    (kayobe) $ kayobe control host command run --command "<command>"

For example::

    (kayobe) $ kayobe control host command run --command "service docker restart"

To execute the command with root privileges, add the ``--become`` argument.
Adding the ``--verbose`` argument allows the output of the command to be seen.
