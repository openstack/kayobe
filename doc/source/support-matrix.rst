==============
Support Matrix
==============

.. _support-matrix-supported-os:

Supported Operating Systems
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Kayobe supports the following host Operating Systems (OS):

* Rocky Linux 10 (since Flamingo 19.0.0 release)
* Ubuntu Noble 24.04 (since Dalmatian 17.0.0 release)

In addition to that CentOS Stream 10 host OS is functional, but not officially
supported. Kolla does not publish CentOS Stream 10 images to Docker Hub/Quay.io,
therefore users need to build them by themselves.

.. note::

   CentOS Stream 9 is no longer supported as a host OS. The 2025.1 Epoxy
   release will in future support both CentOS Stream 9 and 10 to provide a
   route for migration.

.. note::

   Rocky Linux 9 is no longer supported as a host OS. The 2025.1 Epoxy release
   will in future support both CentOS Stream 9 and 10 to provide a route for
   migration.

Supported container images
~~~~~~~~~~~~~~~~~~~~~~~~~~

For details of container image distributions supported by Kolla Ansible, see
the :kolla-ansible-doc:`support matrix <user/support-matrix.html>`.

For details of which images are supported on which distributions, see the
:kolla-doc:`Kolla support matrix <support_matrix>`.
