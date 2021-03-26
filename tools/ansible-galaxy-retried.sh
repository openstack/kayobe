#!/bin/bash

set -e

GALAXY_RETRIES=${GALAXY_RETRIES:-10}
GALAXY_INTERVAL=${GALAXY_INTERVAL:-5}

for i in $(seq 1 $GALAXY_RETRIES); do
    if ansible-galaxy "${@}"; then
        exit 0
    fi
    echo "Ansible Galaxy command failed. Sleeping $GALAXY_INTERVAL seconds before retry"
    sleep $GALAXY_INTERVAL
done

echo "Failed to execute: ansible-galaxy ${@}"
exit 1
