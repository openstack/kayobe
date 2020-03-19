Docker Registry
===============

This role can be used to configure a Docker registry running in a Docker
container.

Requirements
------------

The host executing the role has the following requirements:

* Docker engine
* Python ``docker >= 2.0.0``

Role Variables
--------------

``docker_registry_enabled``: Whether the Docker registry is enabled. Defaults
to ``true``.
``docker_registry_namespace``: Docker image namespace. Defaults to
``library``.
``docker_registry_image``: Docker image name.
``docker_registry_tag``: Docker image tag. Defaults to ``latest``.
``docker_registry_image_full``: Full docker image specification.
``docker_registry_restart_policy``: Docker restart policy for
``docker_registry`` container. Defaults to ``unless-stopped``.
``docker_registry_restart_retries``: Number of Docker restarts. Defaults to 10.
``docker_registry_datadir_volume``: The name or path to use for the docker
volume that backs the registry. Defaults to ``docker_registry``.

Dependencies
------------

None

Example Playbook
----------------

The following playbook configures a Docker registry.

    ---
    - hosts: docker-registry
      roles:
        - role: stackhpc.docker-registry

Author Information
------------------

- Mark Goddard (<mark@stackhpc.com>)
