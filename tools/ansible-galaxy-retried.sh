#!/bin/bash

set -e

GALAXY_RETRIES=${GALAXY_RETRIES:-3}

for i in $(seq 1 $GALAXY_RETRIES); do
    if ansible-galaxy "${@}"; then
        exit 0
    fi
    echo "Ansible Galaxy command failed. Retrying"
done

echo "Failed to execute: ansible-galaxy ${@}"
exit 1
