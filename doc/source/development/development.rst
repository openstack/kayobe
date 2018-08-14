===========
Development
===========

Ansible Galaxy
==============

Kayobe uses a number of Ansible roles hosted on Ansible Galaxy. The role
dependencies are tracked in ``requirements.yml``, and specify required
versions. The process for changing a Galaxy role is as follows:

#. If required, develop changes for the role. This may be done outside of
   Kayobe, or by modifying the role in place during development. If upstream
   changes to the role have already been made, this step can be skipped.
#. Commit changes to the role, typically via a Github pull request.
#. Request that a tagged release of the role be made, or make one if you have
   the necessary privileges.
#. Ensure that automatic imports are configured for the role using e.g. a
   TravisCI webhook notification, or perform a manual import of the role on
   Ansible Galaxy.
#. Modify the version in ``requirements.yml`` to match the new release of the
   role.
