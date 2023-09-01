#!/bin/bash

# Run molecule tests. Any arguments passed to this script will be passed onto
# molecule.

set -e

molecules="$(find ansible/roles/ -name molecule -type d)"

PARENT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# FIXME: doesn't get passed through to linter.
export ANSIBLE_ACTION_PLUGINS="$PARENT/../kayobe/plugins/action:~/.ansible/plugins/action:/usr/share/ansible/plugins/action"
export ANSIBLE_FORCE_COLOR=True

failed=0
ran=0
for molecule in $molecules; do
    pushd $(dirname $molecule)
    # Don't run molecule tests from Galaxy roles.
    if [[ -f meta/.galaxy_install_info ]]; then
        echo "Skipping $(basename $(pwd)) as it is a Galaxy role"
        popd
        continue
    fi
    if ! molecule test --all $*; then
        failed=$((failed + 1))
    fi
    ran=$((ran + 1))
    popd
done

if [[ $failed -ne 0 ]]; then
    echo "Failed $failed / $ran molecule tests"
    exit 1
fi
echo "Ran $ran molecule tests successfully"
