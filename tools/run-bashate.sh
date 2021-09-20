#!/bin/bash

# Ignore E006 -- line length greater than 80 char

ROOT=$(readlink -fn $(dirname $0)/.. )
# NOTE(priteau): ignore E010 because it fails on one-liner bash loops:
# https://bugs.launchpad.net/bash8/+bug/1895102
find $ROOT -not -wholename \*.tox/\* -and -not -wholename \*.test/\* \
    -and -name \*.sh -print0 | xargs -0 bashate -v --ignore E006,E010
