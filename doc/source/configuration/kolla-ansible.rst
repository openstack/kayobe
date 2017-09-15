===========================
Kolla-ansible Configuration
===========================

Kayobe relies heavily on kolla-ansible for deployment of the OpenStack control
plane. Kolla-ansible is installed locally on the ansible control host (the host
from which kayobe commands are executed), and kolla-ansible commands are
executed from there.

Local Environment
=================

Environment variables are used to configure the environment in which
kolla-ansible is installed and executed.

.. table:: Kolla-ansible environment variables

   ====================== ================================================== ============================
   Variable               Purpose                                            Default
   ====================== ================================================== ============================
   ``$KOLLA_CONFIG_PATH`` Path on the ansible control host in which          ``/etc/kolla``
                          the kolla-ansible configuration will be generated.
   ``$KOLLA_SOURCE_PATH`` Path on the ansible control host in which          ``$PWD/src/kolla-ansible``
                          the kolla-ansible source code will be cloned.
   ``$KOLLA_VENV_PATH``   Path on the ansible control host in which          ``$PWD/venvs/kolla-ansible``
                          the kolla-ansible virtualenv will be created.
   ====================== ================================================== ============================
