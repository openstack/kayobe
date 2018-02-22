#!/bin/bash

# Run ansible tests. Any arguments passed to this script will be passed onto
# ansible-playbook.

set -e

failed=0
for playbook in ansible/roles/*/tests/main.yml; do
    if ! ansible-playbook --connection=local $playbook $*; then
        failed=$((failed + 1))
    fi
done
if [[ $failed -ne 0 ]]; then
    echo "Failed $failed test cases"
    exit 1
fi
