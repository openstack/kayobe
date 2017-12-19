OpenSM Infiniband Subnet Manager
================================

This role can be used to configure an OpenSM Infiniband subnet manager running
in a Docker container.

Requirements
------------

The host executing the role has the following requirements:

* Docker engine
* Python ``docker >= 2.0.0``

Role Variables
--------------

``opensm_enabled``: Whether OpenSM is enabled. Defaults to ``true``.
``opensm_namespace``: Docker image namespace. Defaults to ``jumanjiman``.
``opensm_image``: Docker image name.
``opensm_tag``: Docker image tag. Defaults to ``latest``.
``opensm_image_full``: Full docker image specification.
``opensm_restart_policy``: Docker restart policy for OpenSM container. Defaults
to ``unless-stopped``.
``opensm_restart_retries``: Number of Docker restarts. Defaults to 10.

Dependencies
------------

None

Example Playbook
----------------

The following playbook configures OpenSM.

    ---
    - hosts: opensm
      roles:
        - role: opensm

Author Information
------------------

- Mark Goddard (<mark@stackhpc.com>)
