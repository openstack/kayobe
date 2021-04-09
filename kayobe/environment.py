# Copyright (c) 2021 StackHPC Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import logging
import os
import os.path
import sys

from kayobe import utils


LOG = logging.getLogger(__name__)


def add_args(parser):
    """Add arguments required for managing Kayobe environments to a parser."""
    parser.add_argument("--source-config-path",
                        help="Kayobe configuration to import")


def create_kayobe_environment(parsed_args):
    """Create a new Kayobe environment."""
    if not parsed_args.environment:
        LOG.error("You must specify an environment to create")
        sys.exit(1)

    # Ensure environments directory exists and is readable inside config path
    kc_environments = os.path.join(parsed_args.config_path, "environments")
    result = utils.is_readable_dir(kc_environments)
    if not result["result"]:
        if result["message"] == "Path does not exist":
            os.mkdir(kc_environments)
        else:
            LOG.error("Kayobe global environments directory %s is invalid: %s",
                      kc_environments, result["message"])
            sys.exit(1)

    env_path = os.path.join(kc_environments, parsed_args.environment)
    result = utils.is_readable_dir(env_path)
    if result["result"]:
        LOG.error("Kayobe environment directory %s already exists", env_path)
        sys.exit(1)
    else:
        if result["message"] == "Path does not exist":
            os.mkdir(env_path)
        else:
            LOG.error("Kayobe environment directory %s is invalid: %s",
                      env_path, result["message"])
            sys.exit(1)

    source_config_path = parsed_args.source_config_path
    if source_config_path:
        utils.copy_dir(source_config_path, env_path, exclude=["environments"])
