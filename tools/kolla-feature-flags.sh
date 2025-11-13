#!/bin/bash

# This script generates a list of Kolla Ansible feature flags to use as the
# kolla_feature_flags variable in ansible/roles/kolla-ansible/vars/main.yml.
# It should be run periodically and before a release.

# See also: tools/feature-flags.py

set -e
set -o pipefail

KOLLA_ANSIBLE_SRC=$1
KOLLA_GROUP_VARS_ALL=${KOLLA_ANSIBLE_SRC}/ansible/group_vars/all

if [[ ! -d $KOLLA_GROUP_VARS_ALL ]]; then
    echo "Usage: $0 <path to kolla-ansible source>"
    exit 1
fi

# Find all feature flags, strip the enable_ prefix and value, sort.
cat ${KOLLA_GROUP_VARS_ALL}/*.yml | grep '^enable_'| sed -e 's/enable_\(.*\):.*/  - \1/' | sort
