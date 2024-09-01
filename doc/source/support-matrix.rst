==============
Support Matrix
==============

.. _support-matrix-supported-os:

Supported Operating Systems
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Kayobe supports the following host Operating Systems (OS):

* CentOS Stream 8 (untested since EOL of CentOS Stream 8)
* Rocky Linux 8 (since Yoga 12.0.0 release)
* Rocky Linux 9 (since Yoga 12.8.0 release)
* Ubuntu Focal 20.04 (since Wallaby 10.0.0 release)
* Ubuntu Jammy 22.04 (since Yoga 12.8.0 release)

.. note::

   CentOS 7 is no longer supported as a host OS. The Train release supports
   both CentOS 7 and 8, and provides a route for migration. See the `Kayobe
   Train documentation <https://docs.openstack.org/kayobe/train/centos8.html>`_
   for information on migrating to CentOS 8.

.. note::

   CentOS Linux 8 (as opposed to CentOS Stream 8) is no longer supported as a
   host OS. The Victoria release supports both CentOS Linux 8 and CentOS Stream
   8, and provides a route for migration.

.. note::

   Ubuntu Jammy support requires setting ``os_release`` in
   ``etc/kayobe/globals.yml`` to ``jammy``.

.. note::

   Rocky Linux 9 support requires setting ``os_release`` in
   ``etc/kayobe/globals.yml`` to ``9``.

Supported container images
~~~~~~~~~~~~~~~~~~~~~~~~~~

For details of container image distributions supported by Kolla Ansible, see
the :kolla-ansible-doc:`support matrix <user/support-matrix.html>`.

For details of which images are supported on which distributions, see the
:kolla-doc:`Kolla support matrix <support_matrix>`.
