============================
So You Want to Contribute...
============================

For general information on contributing to OpenStack, please check out the
`contributor guide <https://docs.openstack.org/contributors/>`_ to get started.
It covers all the basics that are common to all OpenStack projects: the
accounts you need, the basics of interacting with our Gerrit review system,
how we communicate as a community, etc.

Below will cover the more project specific information you need to get started
with Kayobe.

Basics
~~~~~~

The source repository for this project can be found at:

   https://opendev.org/openstack/kayobe

Communication
~~~~~~~~~~~~~

Kayobe shares communication channels with Kolla.

IRC Channel
    ``#openstack-kolla`` (`channel logs`_) on `OFTC <http://oftc.net>`_

Weekly Meetings
    On Wednesdays at 15:00 UTC in the IRC channel (`meetings logs`_)

Mailing list (prefix subjects with ``[kolla]``)
    http://lists.openstack.org/pipermail/openstack-discuss/

Meeting Agenda
    https://wiki.openstack.org/wiki/Meetings/Kolla

Whiteboard (etherpad)
    Keeping track of CI gate status, release status, stable backports,
    planning and feature development status.
    https://etherpad.openstack.org/p/KollaWhiteBoard

.. _channel logs: http://eavesdrop.openstack.org/irclogs/%23openstack-kolla/
.. _meetings logs:  http://eavesdrop.openstack.org/meetings/kolla/

Contacting the Core Team
~~~~~~~~~~~~~~~~~~~~~~~~

The list in alphabetical order (on first name):

+-----------------------+---------------+------------------------------------+
| Name                  | IRC nick      | Email address                      |
+=======================+===============+====================================+
| Doug Szumski          | dougsz        | doug@stackhpc.com                  |
+-----------------------+---------------+------------------------------------+
| John Garbutt          | johnthetubaguy| john@johngarbutt.com               |
+-----------------------+---------------+------------------------------------+
| Kevin Tibi            | ktibi         | kevintibi@hotmail.com              |
+-----------------------+---------------+------------------------------------+
| Mark Goddard          | mgoddard      | mark@stackhpc.com                  |
+-----------------------+---------------+------------------------------------+
| Pierre Riteau         | priteau       | pierre@stackhpc.com                |
+-----------------------+---------------+------------------------------------+
| Will Szumski          | jovial        | will@stackhpc.com                  |
+-----------------------+---------------+------------------------------------+

The current effective list is also available from Gerrit:
https://review.opendev.org/#/admin/groups/1875,members

New Feature Planning
~~~~~~~~~~~~~~~~~~~~

New features are discussed via IRC or mailing list (with [kolla] prefix).
Kayobe project keeps RFEs in `Storyboard
<https://storyboard.openstack.org/#!/project/openstack/kayobe>`__.  Specs are
welcome but not strictly required.

Task Tracking
~~~~~~~~~~~~~

Kolla project tracks tasks in `Storyboard
<https://storyboard.openstack.org/#!/project/openstack/kayobe>`__.  Note this
is the same place as for bugs.

A more lightweight task tracking is done via etherpad - `Whiteboard
<https://etherpad.openstack.org/p/KollaWhiteBoard>`__.

Reporting a Bug
~~~~~~~~~~~~~~~

You found an issue and want to make sure we are aware of it? You can do so
on `Storyboard <https://storyboard.openstack.org/#!/project/openstack/kayobe>`__.
Note this is the same place as for tasks.

Getting Your Patch Merged
~~~~~~~~~~~~~~~~~~~~~~~~~

Most changes proposed to Kayobe require two +2 votes from core reviewers
before +W. A release note is required on most changes as well. Release notes
policy is described in :ref:`its own section <release-notes>`.

Significant changes should have documentation and testing provided with them.

Project Team Lead Duties
~~~~~~~~~~~~~~~~~~~~~~~~

All common PTL duties are enumerated in the `PTL guide <https://docs.openstack.org/project-team-guide/ptl.html>`_.
Release tasks are described in the :doc:`Kayobe releases guide <releases>`.
