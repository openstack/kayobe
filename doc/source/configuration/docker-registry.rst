.. _configuration-docker-registry:

===============
Docker registry
===============

This section covers configuration of the Docker registry that may be deployed,
by default on the seed host. Docker registry configuration is typically applied
in ``${KAYOBE_CONFIG_PATH}/docker-registry.yml``. Consult the `Docker registry
documentation <https://docs.docker.com/registry/>`__ for further details of
registry usage and configuration.

The registry is deployed during the ``kayobe seed host configure`` command.

Configuring the registry
========================

``docker_registry_enabled``
    Whether a docker registry is enabled. Default is ``false``. When set to
    ``true``, the Docker registry is deployed on all hosts in the
    ``docker-registry`` group. By default this includes the seed host.
``docker_registry_env``
    Dict of environment variables to provide to the docker registry container.
    This allows to configure the registry by overriding specific configuration
    options, as described at https://docs.docker.com/registry/configuration/
    For example, the registry can be configured as a pull through cache to
    Docker Hub by setting REGISTRY_PROXY_REMOTEURL to
    "https://registry-1.docker.io".  Note that it is not possible to push to a
    registry configured as a pull through cache. Default is ``{}``.
``docker_registry_port``
    The port on which the docker registry server should listen. Default is
    4000.
``docker_registry_datadir_volume``
    Name or path to use as the volume for the docker registry. Default is
    ``docker_registry``.

TLS
---

It is recommended to enable TLS for the registry.

``docker_registry_enable_tls``
    Whether to enable TLS for the registry. Default is ``false``.

``docker_registry_cert_path``
    Path to a TLS certificate to use when TLS is enabled. Default is none.

``docker_registry_key_path``
    Path to a TLS key to use when TLS is enabled. Default is none.

For example, the certificate and key could be stored with the Kayobe
configuration, under ``${KAYOBE_CONFIG_PATH}/docker-registry/``. These files
may be encrypted via Ansible Vault.

.. code-block:: yaml
   :caption: ``docker-registry.yml``

   docker_registry_enable_tls: true
   docker_registry_cert_path: "{{ kayobe_config_path }}/docker-registry/cert.pem
   docker_registry_key_path: "{{ kayobe_config_path }}/docker-registry/key.pem

Using the registry
==================

Enabling the registry does not automatically set the configuration for Docker
engine to use it. This should be done via the :ref:`docker_registry variable
<configuration-hosts-docker>`.

TLS
---

If the registry is using a privately signed TLS certificate, it is necessary to
:ref:`configure Docker engine with the CA certificate
<configuration-hosts-docker>`.

If TLS is enabled, Docker engine should be configured to use HTTPS to
communicate with it:

.. code-block:: yaml
   :caption: ``kolla/globals.yml``

   docker_registry_insecure: false
