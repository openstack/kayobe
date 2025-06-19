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
       image: "docker.io/stackhpc/squid"
       pre: "{{ kayobe_env_config_path }}/containers/squid/pre.yml"
       post: "{{ kayobe_env_config_path }}/containers/squid/post.yml"
       pre_destroy: "{{ kayobe_env_config_path }}/containers/squid/pre_destroy.yml"
       post_destroy: "{{ kayobe_env_config_path }}/containers/squid/post_destroy.yml"
       tag: "3.5.20-1"

Please notice the *optional* pre, post, pre_destroy, and post_destroy Ansible task
files - those need to be created in ``kayobe-config`` path. The table below describes
when they will run:

.. list-table:: Container hooks
   :widths: 25 75
   :header-rows: 1

   * - Hook
     - Trigger point
   * - pre
     - Before container deployment
   * - post
     - After container deployment
   * - pre_destroy
     - Before container is destroyed
   * - post_destroy
     - After container is destroyed

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

.. literalinclude:: ../../../../ansible/roles/manage-containers/defaults/main.yml
    :language: yaml


Docker registry
===============

Seed containers can be pulled from a docker registry deployed on the seed,
since the docker registry deployment step precedes the custom container
deployment step.

It is also possible to deploy a custom containerised docker registry as a
custom seed container. In this case, basic authentication login attempts can be
disabled by setting

.. code-block:: yaml
   :caption: ``seed.yml``

   seed_deploy_containers_registry_attempt_login: false

Without this setting, the login will fail because the registry has not yet been
deployed.

More information on deploying a docker registry can be found :ref:`here
<configuration-docker-registry>`.

