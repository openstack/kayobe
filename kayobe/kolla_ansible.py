import logging
import os
import os.path
import subprocess
import sys

from kayobe import utils


DEFAULT_CONFIG_PATH = "/etc/kolla"

CONFIG_PATH_ENV = "KOLLA_CONFIG_PATH"

DEFAULT_VENV_PATH = "ansible/kolla-venv"

VENV_PATH_ENV = "KOLLA_VENV"

LOG = logging.getLogger(__name__)


def add_args(parser):
    """Add arguments required for running Kolla Ansible to a parser."""
    default_config_path = os.getenv(CONFIG_PATH_ENV, DEFAULT_CONFIG_PATH)
    default_venv = os.getenv(VENV_PATH_ENV, DEFAULT_VENV_PATH)
    parser.add_argument("--kolla-config-path", default=default_config_path,
                        help="path to Kolla configuration. "
                             "(default=$%s or %s)" %
                             (CONFIG_PATH_ENV, DEFAULT_CONFIG_PATH))
    parser.add_argument("-ke", "--kolla-extra-vars", metavar="EXTRA_VARS",
                        action="append",
                        help="set additional variables as key=value or "
                             "YAML/JSON for Kolla Ansible")
    parser.add_argument("-ki", "--kolla-inventory", metavar="INVENTORY",
                        help="specify inventory host path "
                             "(default=$%s/inventory or %s/inventory) or "
                             "comma-separated host list for Kolla Ansible" %
                             (CONFIG_PATH_ENV, DEFAULT_CONFIG_PATH))
    parser.add_argument("-kt", "--kolla-tags", metavar="TAGS",
                        help="only run plays and tasks tagged with these "
                             "values in Kolla Ansible")
    parser.add_argument("--kolla-venv", metavar="VENV", default=default_venv,
                        help="path to virtualenv where Kolla Ansible is "
                             "installed")


def _get_inventory_path(parsed_args, inventory_filename):
    """Return the path to the Kolla inventory."""
    if parsed_args.kolla_inventory:
        return parsed_args.kolla_inventory
    else:
        return os.path.join(parsed_args.kolla_config_path, "inventory",
                            inventory_filename)


def _validate_args(parsed_args, inventory_filename):
    """Validate Kayobe Ansible arguments."""
    result = utils.is_readable_dir(parsed_args.kolla_config_path)
    if not result["result"]:
        LOG.error("Kolla configuration path %s is invalid: %s",
                  parsed_args.kolla_config_path, result["message"])
        sys.exit(1)

    inventory = _get_inventory_path(parsed_args, inventory_filename)
    result = utils.is_readable_file(inventory)
    if not result["result"]:
        LOG.error("Kolla inventory %s is invalid: %s",
                  inventory, result["message"])
        sys.exit(1)

    result = utils.is_readable_dir(parsed_args.kolla_venv)
    if not result["result"]:
        LOG.error("Kolla virtualenv %s is invalid: %s",
                  parsed_args.kolla_venv, result["message"])
        sys.exit(1)


def build_args(parsed_args, command, inventory_filename, extra_vars=None,
               tags=None):
    """Build arguments required for running Kolla Ansible."""
    venv_activate = os.path.join(parsed_args.kolla_venv, "bin", "activate")
    cmd = ["source", venv_activate, "&&"]
    cmd += ["kolla-ansible", command]
    inventory = _get_inventory_path(parsed_args, inventory_filename)
    cmd += ["--inventory", inventory]
    if parsed_args.kolla_config_path != DEFAULT_CONFIG_PATH:
        cmd += ["--configdir", parsed_args.kolla_config_path]
        cmd += ["--passwords",
                os.path.join(parsed_args.kolla_config_path, "passwords.yml")]
    if parsed_args.kolla_extra_vars:
        for extra_var in parsed_args.kolla_extra_vars:
            cmd += ["-e", extra_var]
    if extra_vars:
        for extra_var_name, extra_var_value in extra_vars.items():
            cmd += ["-e", "%s=%s" % (extra_var_name, extra_var_value)]
    if parsed_args.kolla_tags or tags:
        all_tags = [t for t in [parsed_args.kolla_tags, tags] if t]
        cmd += ["--tags", ",".join(all_tags)]
    return cmd


def run(parsed_args, command, inventory_filename, extra_vars=None,
        tags=None, quiet=False):
    """Run a Kolla Ansible command."""
    _validate_args(parsed_args, inventory_filename)
    cmd = build_args(parsed_args, command,
                     inventory_filename=inventory_filename,
                     extra_vars=extra_vars, tags=tags)
    try:
        utils.run_command(" ".join(cmd), quiet=quiet, shell=True)
    except subprocess.CalledProcessError as e:
        LOG.error("kolla-ansible %s exited %d", command, e.returncode)
        sys.exit(e.returncode)


def run_seed(*args, **kwargs):
    """Run a Kolla Ansible command using the seed inventory."""
    return run(*args, inventory_filename="seed", **kwargs)


def run_overcloud(*args, **kwargs):
    """Run a Kolla Ansible command using the overcloud inventory."""
    return run(*args, inventory_filename="overcloud", **kwargs)
