.. _configuration-seed-custom-containers:

======================
Seed custom containers
======================

This section covers configuration of the user-defined containers deployment
functionality that runs on the seed host.

Configuration
=============

For example, to deploy a squid container image:

.. code-block:: yaml
   :caption: ``seed.yml``

   seed_containers:
     squid:
       image: "stackhpc/squid:3.5.20-1"
       pre: "{{ kayobe_env_config_path }}/containers/squid/pre.yml"
       post: "{{ kayobe_env_config_path }}/containers/squid/post.yml"

Please notice the *optional* pre and post Ansible task files - those need to
be created in ``kayobe-config`` path and will be run before and after
particular container deployment.

Possible options for container deployment:

.. code-block:: yaml

   seed_containers:
     containerA:
       capabilities:
       command:
       comparisons:
       detach:
       env:
       network_mode:
       image:
       init:
       ipc_mode:
       pid_mode:
       ports:
       privileged:
       restart_policy:
       shm_size:
       sysctls:
       tag:
       ulimits:
       user:
       volumes:

For a detailed explanation of each option - please see `Ansible
docker_container <https://docs.ansible.com/ansible/latest/modules/docker_container_module.html>`_
module page.

List of Kayobe applied defaults to required docker_container variables:

.. literalinclude:: ../../../../ansible/roles/deploy-containers/defaults/main.yml
    :language: yaml

