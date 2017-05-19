# Copyright (c) 2017 StackHPC Ltd.
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

import os
import subprocess

from kayobe import utils


VAULT_PASSWORD_ENV = "KAYOBE_VAULT_PASSWORD"


def _get_default_vault_password_file():
    """Return the default value for the vault password file argument.

    It is possible to use an environment variable to avoid typing the vault
    password.
    """
    if not os.getenv(VAULT_PASSWORD_ENV):
        return None
    cmd = ["which", "kayobe-vault-password-helper"]
    try:
        output = utils.run_command(cmd, check_output=True)
    except subprocess.CalledProcessError:
        return None
    return output.strip()


def add_args(parser):
    """Add arguments required for running Ansible playbooks to a parser."""
    default_vault_password_file = _get_default_vault_password_file()
    vault = parser.add_mutually_exclusive_group()
    vault.add_argument("--ask-vault-pass", action="store_true",
                       help="ask for vault password")
    vault.add_argument("--vault-password-file", metavar="VAULT_PASSWORD_FILE",
                       default=default_vault_password_file,
                       help="vault password file")


def build_args(parsed_args):
    """Build a list of command line arguments for use with ansible-playbook."""
    cmd = []
    if parsed_args.ask_vault_pass:
        cmd += ["--ask-vault-pass"]
    elif parsed_args.vault_password_file:
        cmd += ["--vault-password-file", parsed_args.vault_password_file]
    return cmd
