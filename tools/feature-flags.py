#!/usr/bin/env python3

# Usage: run this script and copy the output to etc/kayobe/kolla.yml

# See also: tools/kolla-feature-flags.sh

import os
import pathlib

import yaml

script_dir = pathlib.Path(__file__).parent.absolute()
path = os.path.join(script_dir, "../ansible/roles/kolla-ansible/vars/main.yml")

with open(path) as f:
    vars = yaml.safe_load(f)
    for key in vars["kolla_feature_flags"]:
        print("#kolla_enable_%s:" % key)
