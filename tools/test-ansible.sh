#!/bin/bash

# Run ansible tests. Any arguments passed to this script will be passed onto
# ansible-playbook.

set -e

failed=0
for playbook in ansible/roles/*/tests/main.yml; do
    # We declare extra variables to install the {{ openstack_branch }} version
    # of kolla-ansible. We should use {{ kolla_ansible_source_version }}, but
    # adding ansible/group_vars/all/kolla would in turn require other
    # extra-vars files (like pip) and may cause unintended side effects.
    if ! ansible-playbook --connection=local $playbook $* -e @ansible/group_vars/all/openstack; then
        failed=$((failed + 1))
    fi
done
if [[ $failed -ne 0 ]]; then
    echo "Failed $failed test cases"
    exit 1
fi
