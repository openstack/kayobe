===================
Seed Administration
===================

Deprovisioning The Seed VM
==========================

.. note::

   This step will destroy the seed VM and its data volumes.

To deprovision the seed VM::

    (kayobe) $ kayobe seed vm deprovision

Updating Packages
=================

It is possible to update packages on the seed host. To update one or more
packages::

    (kayobe) $ kayobe seed host package update --packages <package1>,<package2>

To update all eligible packages, use ``*``, escaping if necessary::

    (kayobe) $ kayobe seed host package update --packages *

To only install updates that have been marked security related::

    (kayobe) $ kayobe seed host package update --packages <packages> --security

Note that these commands do not affect packages installed in containers, only
those installed on the host.
