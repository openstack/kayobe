cAdvisor
========

This role can be used to configure cAdvisor running in a Docker container.

Requirements
------------

The host executing the role has the following requirements:

* Docker engine
* Python ``docker >= 2.0.0``

Role Variables
--------------

``cadvisor_enabled``: Whether the cAdvisor is enabled. Defaults to ``false``.
``cadvisor_namespace``: Docker image namespace. Defaults to ``cadvisor``.
``cadvisor_image``: Docker image name.
``cadvisor_tag``: Docker image tag. Defaults to ``v0.28.3``.
``cadvisor_image_full``: Full docker image specification.
``cadvisor_restart_policy``: Docker restart policy for cAdvisor container. Defaults
to ``unless-stopped``.
``cadvisor_restart_retries``: Number of Docker restarts. Defaults to 10.

Dependencies
------------

None

Example Playbook
----------------

The following playbook configures cAdvisor.

    ---
    - hosts: cadvisor
      roles:
        - role: cadvisor

Author Information
------------------

- Jonathan Davies (<jpds@protonmail.com>)
