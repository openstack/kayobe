==============
Support Matrix
==============

.. _support-matrix-supported-os:

Supported Operating Systems
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Kayobe supports the following host Operating Systems (OS):

* Rocky Linux 9 (since Zed 13.0.0 release)
* Ubuntu Jammy 22.04 (since Zed 13.0.0 release)

In addition to that CentOS Stream 9 host OS is functional, but not officially
supported. Kolla does not publish CentOS Stream 9 images to Docker Hub/Quay.io,
therefore users need to build them by themselves.

.. note::

   CentOS Stream 8 is no longer supported as a host OS. The Yoga release
   supports both CentOS Stream 8 and 9, and provides a route for migration.

.. note::

   Rocky Linux 8 is no longer supported as a host OS. The Yoga release supports
   both Rocky Linux 8 and 9, and provides a route for migration.

Supported container images
~~~~~~~~~~~~~~~~~~~~~~~~~~

For details of container image distributions supported by Kolla Ansible, see
the :kolla-ansible-doc:`support matrix <user/support-matrix.html>`.

For details of which images are supported on which distributions, see the
:kolla-doc:`Kolla support matrix <support_matrix>`.
