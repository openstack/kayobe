Prometheus Node Exporter
========================

This role can be used to configure a Prometheus node exporter running
in a Docker container.

Requirements
------------

The host executing the role has the following requirements:

* Docker engine
* Python ``docker >= 2.0.0``

Role Variables
--------------

``nodeexporter_enabled``: Whether the Node Exporter is enabled. Defaults to ``true``.
``nodeexporter_namespace``: Docker image namespace. Defaults to ``prom``.
``nodeexporter_image``: Docker image name.
``nodeexporter_tag``: Docker image tag. Defaults to ``latest``.
``nodeexporter_image_full``: Full docker image specification.
``nodeexporter_restart_policy``: Docker restart policy for Node Exporter container. Defaults
to ``unless-stopped``.
``nodeexporter_restart_retries``: Number of Docker restarts. Defaults to 10.

Dependencies
------------

None

Example Playbook
----------------

The following playbook configures Node Exporter.

    ---
    - hosts: node-exporter
      roles:
        - role: node-exporter

Author Information
------------------

- Jonathan Davies (<jpds@protonmail.com>)
