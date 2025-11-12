.. _os-distribution:

===============
OS Distribution
===============

As of the Wallaby 10.0.0 release, Kayobe supports multiple Operating System
(OS) distributions. See the :ref:`support matrix <support-matrix-supported-os>`
for a list of supported OS distributions. The same OS distribution should be
used throughout the system.

The ``os_distribution`` variable in ``etc/kayobe/globals.yml`` can be used to
set the OS distribution to use.  It may be set to either ``centos`` or
or ``rocky`` or ``ubuntu``, and defaults to ``rocky``.

The ``os_release`` variable in ``etc/kayobe/globals.yml`` can be used to set
the release of the OS. When ``os_distribution`` is set to ``centos`` it may be
set to ``10-stream``, and this is its default value. When ``os_distribution``
is set to ``rocky`` it may be set to ``10``, and this is its default value.
When ``os_distribution`` is set to ``ubuntu`` it may be set to ``noble``, and
this is its default value.

These variables are used to set various defaults, including:

* Bootstrap users
* Overcloud host root disk image build configuration
* Seed VM root disk image
* Kolla base container image

Example: using Ubuntu
=====================

In the following example, we set the OS distribution to ``ubuntu``:

.. code-block:: yaml
   :caption: ``globals.yml``

   os_distribution: "ubuntu"

Example: using Rocky
====================

In the following example, we set the OS distribution to ``rocky``:

.. code-block:: yaml
   :caption: ``globals.yml``

   os_distribution: "rocky"
