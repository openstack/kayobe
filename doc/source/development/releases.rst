========
Releases
========

The `project creator's guide
<https://docs.openstack.org/infra/manual/drivers.html#release-management>`__
provides information on release management. As Kayobe is not an official
project, it cannot use the official release tooling in the
``openstack/releases`` repository.

There are various `useful files
<http://opendev.org/openstack-infra/project-config/src/branch/master/roles/copy-release-tools-scripts/files/release-tools/>`__
in the ``openstack-infra/project-config`` repository. In particular, see the
``release.sh`` and ``make_branch.sh`` scripts.

.. _releases-preparing-for-a-release:

Preparing for a release
=======================

Update dependencies to upcoming release
---------------------------------------

Prior to the release, we update the dependencies and upper constraints on the
master branch to use the upcoming release. This is now quite easy to do,
following the introduction of the ``openstack_release`` variable. This is done
prior to creating a release candidate. For example, see
https://review.opendev.org/#/c/652091.

Synchronise kayobe-config
-------------------------

Ensure that configuration defaults in ``kayobe-config`` are in sync with those
under ``etc/kayobe`` in ``kayobe``. This can be done via:

.. code-block:: console

   cp -aR kayobe/etc/kayobe/* kayobe-config/etc/kayobe

Commit the changes and submit for review.

Synchronise kayobe-config-dev
-----------------------------

Ensure that configuration defaults in ``kayobe-config-dev`` are in sync with
those in ``kayobe-config``. This requires a little more care, since some
configuration options have been changed from the defaults. Choose a method to
suit you and be careful not to lose any configuration.

Commit the changes and submit for review.

Add a prelude to release notes
------------------------------

It's possible to add a prelude to the release notes for a particular release
using a ``prelude`` section in a ``reno`` note.

Creating a release candidate
============================

Prior to cutting a stable branch, the ``master`` branch should be tagged as a
release candidate.  This allows the ``reno`` tool to determine where to stop
searching for release notes for the next release.  The tag should take the
following form: ``<release tag>.0rc$n``, where ``$n`` is the release candidate
number.

The ``tools/release.sh`` script in the ``kayobe`` repository can be used to tag
a release and push it to Gerrit. For example, to tag and release the ``kayobe``
deliverable release candidate ``4.0.0.0rc1`` in the Queens series from the base
of the ``stable/queens`` branch:

.. code-block:: console

   ./tools/release.sh kayobe 4.0.0.0rc1 origin/master queens

Creating a stable branch
========================

Stable branches should be cut for each Kayobe deliverable (``kayobe``,
``kayobe-config``,  ``kayobe-config-dev``).

To create a branch ``<new branch>`` at commit ``<ref>``:

.. code-block:: console

   cd /path/to/repo
   git checkout -b <new branch> <ref>
   git review -s
   git push gerrit <new branch>

After creating the branch, on the new branch:

* update the ``.gitreview`` file on the new branch, for example:
  https://review.openstack.org/609735

For the kayobe repo only, on the master branch:

* update the release notes for the new release series:
  https://review.openstack.org/609742

Creating a release
==================

Prerequisites
-------------

Creating a signed tagged release requires a GPG key to be used. There are
various resources for how to set this up, including
https://help.ubuntu.com/community/GnuPrivacyGuardHowto. Your default Gerrit
email should be added to the key, and the key should be trusted ultimately, see
https://wiki.openstack.org/wiki/Oslo/ReleaseProcess#Setting_Up_GPG for
information.

Tagging a release
-----------------

Tags should be created for each deliverable (``kayobe``, ``kayobe-config``,
``kayobe-config-dev``). Currently the same version is used for each.

The ``tools/release.sh`` script in the ``kayobe`` repository can be used to tag
a release and push it to Gerrit. For example, to tag and release the ``kayobe``
deliverable version ``4.0.0`` in the Queens series from the tip of the
``stable/queens`` branch:

.. code-block:: console

   ./tools/release.sh kayobe 4.0.0 origin/stable/queens queens

Post-release activites
----------------------

An email will be sent to the release-announce mailing list about the new
release.

Continuing Development
======================

After the stable branch has been cut, the master branch can be unfrozen and
development on features for the next release can begin. At this point it will
still be using dependencies and upper constraints from the release branch, so
revert the patch created in :ref:`releases-preparing-for-a-release`. For
example, see https://review.opendev.org/676941.
