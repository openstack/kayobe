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
    On Wednesdays in the IRC channel (`meeting information`_)

Mailing list (prefix subjects with ``[kolla]``)
    http://lists.openstack.org/pipermail/openstack-discuss/

Meeting Agenda
    https://wiki.openstack.org/wiki/Meetings/Kolla

Whiteboard (etherpad)
    Keeping track of CI gate status, release status, stable backports,
    planning and feature development status.
    https://etherpad.openstack.org/p/KollaWhiteBoard

.. _channel logs: http://eavesdrop.openstack.org/irclogs/%23openstack-kolla/
.. _meeting information: https://meetings.opendev.org/#Kolla_Team_Meeting

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
Kayobe project keeps RFEs in `Launchpad
<https://bugs.launchpad.net/kayobe>`__.
Please use [RFE] prefix in the bug subject.
Note this is the same place as for bugs.
Specs are welcome but not strictly required.

Task Tracking
~~~~~~~~~~~~~

Kayobe project tracks tasks in `Launchpad
<https://bugs.launchpad.net/kayobe>`__.  Note this
is the same place as for bugs.

A more lightweight task tracking is done via etherpad - `Whiteboard
<https://etherpad.openstack.org/p/KollaWhiteBoard>`__.

To see an overview of in-progress patches, sorted into useful sections, you can
view the `Kayobe Review Dashboard <https://review.opendev.org/dashboard/?title=Kayobe+Review+Dashboard&foreach=%28project%3Aopenstack%2Fkayobe+OR+project%3Aopenstack%2Fkayobe%2Dconfig+OR+project%3Aopenstack%2Fkayobe%2Dconfig%2Ddev%29+status%3Aopen+NOT+label%3ACode%2DReview%3C%3D%2D2+NOT+label%3AWorkflow%3C%3D%2D1&High+priority+changes=label%3AReview%2DPriority%3D2&Priority+changes=label%3AReview%2DPriority%3D1&Feature+freeze=label%3AReview%2DPriority%3D%2D1&Stable+branch+backports=branch%3A%5Estable%2F.%2A+status%3Aopen+NOT+label%3AReview%2DPriority%3D%2D1&Small+things+%28%3C25+LOC%2C+limit+25%29+on+master+branch=delta%3A%3C%3D25+limit%3A25+NOT+label%3ACode%2DReview%2D1+label%3AVerified%3E%3D1%2Czuul+NOT+label%3AReview%2DPriority%3D%2D1+branch%3Amaster&Needs+Final+Approval+%28to+land+on+master+branch%29=NOT+label%3AWorkflow%3E%3D1+NOT+label%3AWorkflow%3C%3D%2D1+NOT+owner%3Aself+label%3ACode%2DReview%3E%3D2+label%3AVerified%3E%3D1%2Czuul+NOT+label%3AReview%2DPriority%3D%2D1+branch%3Amaster&Needs+revisit+%28You+were+a+reviewer+but+haven%27t+voted+in+the+current+revision%29=reviewer%3Aself+limit%3A50&Newer+%28%3C1wk%29+Open+Patches+%28limit+25%29+on+master+branch=%2Dage%3A1week+limit%3A25+NOT+label%3AWorkflow%3E%3D1+label%3AVerified%3E%3D1%2Czuul+NOT+label%3ACode%2DReview%3E%3D2+NOT+label%3AReview%2DPriority%3D%2D1+branch%3Amaster&Older+%28%3E1wk%29+Open+Patches+Passing+Zuul+Tests+%28limit+50%29+on+master+branch=age%3A1week+limit%3A50+NOT+label%3AWorkflow%3E%3D1+NOT+label%3ACode%2DReview%3C%3D%2D1+NOT+label%3ACode%2DReview%3E%3D1+label%3AVerified%3E%3D1%2Czuul+NOT+label%3AReview%2DPriority%3D%2D1+branch%3Amaster>`__.

Reporting a Bug
~~~~~~~~~~~~~~~

You found an issue and want to make sure we are aware of it? You can do so
on `Launchpad <https://bugs.launchpad.net/kayobe>`__.
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
