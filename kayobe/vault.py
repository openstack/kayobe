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

import getpass
import logging
import os
import subprocess
import sys

from kayobe import utils


LOG = logging.getLogger(__name__)

VAULT_PASSWORD_ENV = "KAYOBE_VAULT_PASSWORD"


def _get_vault_password_helper():
    """Return the path to the kayobe-vault-password-helper executable."""
    cmd = ["which", "kayobe-vault-password-helper"]
    try:
        # NOTE(mgoddard): universal_newlines ensures stdout is opened in text
        # mode, and we get a string rather than bytes.
        output = utils.run_command(cmd, check_output=True,
                                   universal_newlines=True)
    except subprocess.CalledProcessError:
        return None
    return output.strip()


def _get_default_vault_password_file():
    """Return the default value for the vault password file argument.

    It is possible to use an environment variable to avoid typing the vault
    password.
    """
    if not os.getenv(VAULT_PASSWORD_ENV):
        return None
    return _get_vault_password_helper()


def add_args(parser):
    """Add arguments required for running Ansible playbooks to a parser."""
    default_vault_password_file = _get_default_vault_password_file()
    vault = parser.add_mutually_exclusive_group()
    vault.add_argument("--ask-vault-pass", action="store_true",
                       help="ask for vault password")
    vault.add_argument("--vault-password-file", metavar="VAULT_PASSWORD_FILE",
                       default=default_vault_password_file,
                       help="vault password file")


def build_args(parsed_args, password_file_arg_name):
    """Build a list of command line arguments for use with ansible-playbook."""
    vault_password_file = None
    if parsed_args.ask_vault_pass:
        vault_password_file = _get_vault_password_helper()
    elif parsed_args.vault_password_file:
        vault_password_file = parsed_args.vault_password_file

    cmd = []
    if vault_password_file:
        cmd += [password_file_arg_name, vault_password_file]
    return cmd


def validate_args(parsed_args):
    """Validate command line arguments."""
    # Ensure that a password prompt or file has not been requested if the
    # password environment variable is set.
    if VAULT_PASSWORD_ENV not in os.environ:
        return

    helper = _get_vault_password_helper()
    invalid_arg = None
    if parsed_args.ask_vault_pass:
        invalid_arg = "--ask-vault-pass"
    elif parsed_args.vault_password_file != helper:
        invalid_arg = "--vault-password-file"

    if invalid_arg:
        LOG.error("Cannot specify %s when $%s is specified" %
                  (invalid_arg, VAULT_PASSWORD_ENV))
        sys.exit(1)


def _ask_vault_pass():
    """Prompt the user for a Vault password.

    The first time this function is called, the user is prompted for a
    password. To avoid prompting the user multiple times per invocation of
    kayobe, we cache the password and return it without prompting on subsequent
    calls.

    :return: The password entered by the user.
    """
    if not hasattr(_ask_vault_pass, "password"):
        password = getpass.getpass("Vault password: ")
        setattr(_ask_vault_pass, "password", password)
    return getattr(_ask_vault_pass, "password")


def _read_vault_password_file(vault_password_file):
    """Return the password from a vault password file."""
    vault_password = utils.read_file(vault_password_file)
    vault_password = vault_password.strip()
    return vault_password


def update_environment(parsed_args, env):
    """Update environment variables with the vault password if necessary.

    :param parsed_args: Parsed command line arguments.
    :params env: Dict of environment variables to update.
    """
    # If the Vault password has been specified via --vault-password-file, or a
    # prompt has been requested via --ask-vault-pass, ensure the environment
    # variable is set, so that it can be referenced by playbooks to generate
    # the kolla-ansible passwords.yml file.
    if VAULT_PASSWORD_ENV in env:
        return

    vault_password = None
    if parsed_args.ask_vault_pass:
        vault_password = _ask_vault_pass()
    elif parsed_args.vault_password_file:
        vault_password = _read_vault_password_file(
            parsed_args.vault_password_file)

    if vault_password is not None:
        env[VAULT_PASSWORD_ENV] = vault_password
