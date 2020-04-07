# Configuration for kayobe development environment.

# Path to the kayobe source code repository. Typically this will be the Vagrant
# shared directory.
#export KAYOBE_SOURCE_PATH=/vagrant

# Path to the kayobe-config repository checkout.
#export KAYOBE_CONFIG_SOURCE_PATH=${KAYOBE_SOURCE_PATH}/config/src/kayobe-config

# Path to the kayobe virtual environment.
#export KAYOBE_VENV_PATH=~/kayobe-venv

# Whether to provision a VM for the seed host.
#export KAYOBE_SEED_VM_PROVISION=1

# Whether to build container images for the seed services. If 0, they will be
# pulled.
#export KAYOBE_SEED_CONTAINER_IMAGE_BUILD=0

# Whether to build container images for the overcloud services. If 0, they will
# be pulled.
#export KAYOBE_OVERCLOUD_CONTAINER_IMAGE_BUILD=0

# Additional arguments to pass to kayobe commands.
#export KAYOBE_EXTRA_ARGS=

# Upper constraints to use when installing Python packages.
#export UPPER_CONSTRAINTS_FILE=
