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

import errno
import logging
import os
import os.path
import shutil
import subprocess
import sys
import tempfile

# TODO(dougszu): Backwards compatibility for Ansible 11. This exception
# handler can be removed in the G cycle.
try:
    from ansible.parsing.vault import EncryptedString
except ImportError:
    # Ansible 11
    from ansible.parsing.yaml.objects import AnsibleVaultEncryptedUnicode
    EncryptedString = AnsibleVaultEncryptedUnicode

from kayobe import exception
from kayobe import utils
from kayobe import vault


DEFAULT_CONFIG_PATH = "/etc/kayobe"

CONFIG_PATH_ENV = "KAYOBE_CONFIG_PATH"

ENVIRONMENT_ENV = "KAYOBE_ENVIRONMENT"

LOG = logging.getLogger(__name__)


def add_args(parser):
    """Add arguments required for running Ansible playbooks to a parser."""
    default_config_path = os.getenv(CONFIG_PATH_ENV, DEFAULT_CONFIG_PATH)
    default_environment = os.getenv(ENVIRONMENT_ENV)
    parser.add_argument("-b", "--become", action="store_true",
                        help="run operations with become (nopasswd implied)")
    parser.add_argument("-C", "--check", action="store_true",
                        help="don't make any changes; instead, try to predict "
                             "some of the changes that may occur")
    parser.add_argument("--config-path", default=default_config_path,
                        help="path to Kayobe configuration. "
                             "(default=$%s or %s)" %
                             (CONFIG_PATH_ENV, DEFAULT_CONFIG_PATH))
    parser.add_argument("-D", "--diff", action="store_true",
                        help="when changing (small) files and templates, show "
                             "the differences in those files; works great "
                             "with --check")
    parser.add_argument("--environment", default=default_environment,
                        help="specify environment name (default=$%s or None)" %
                             ENVIRONMENT_ENV)
    parser.add_argument("-e", "--extra-vars", metavar="EXTRA_VARS",
                        action="append",
                        help="set additional variables as key=value or "
                             "YAML/JSON")
    parser.add_argument("-i", "--inventory", metavar="INVENTORY",
                        action="append",
                        help="specify inventory host path "
                             "(default=$%s/inventory or %s/inventory) " %
                             (CONFIG_PATH_ENV, DEFAULT_CONFIG_PATH))
    parser.add_argument("-l", "--limit", metavar="SUBSET",
                        help="further limit selected hosts to an additional "
                             "pattern")
    parser.add_argument("--skip-tags", metavar="TAGS",
                        help="only run plays and tasks whose tags do not "
                             "match these values")
    parser.add_argument("-t", "--tags", metavar="TAGS",
                        help="only run plays and tasks tagged with these "
                             "values")
    parser.add_argument("-lt", "--list-tasks",
                        action="store_true",
                        help="only print names of tasks, don't run them.")
    parser.add_argument("-sh", "--skip-hooks", action="store", default=None,
                        help="disables hooks. Specify a pattern to skip "
                             "specific playbooks. \"all\" skips all playbooks")


def _get_inventories_paths(parsed_args, env_paths):
    """Return the paths to the Kayobe inventories."""
    default_inventory = utils.get_data_files_path("ansible", "inventory")
    inventories = [default_inventory]
    if parsed_args.inventory:
        inventories.extend(parsed_args.inventory)
        return inventories

    shared_inventory = os.path.join(parsed_args.config_path, "inventory")
    if env_paths:
        if os.path.exists(shared_inventory):
            inventories.append(shared_inventory)
    else:
        # Preserve existing behaviour: don't check if an inventory
        # directory exists when no environment is specified
        inventories.append(shared_inventory)
    for env_path in env_paths or []:
        env_inventory = os.path.join(env_path, "inventory")
        if os.path.exists(env_inventory):
            inventories.append(env_inventory)
    return inventories


def _validate_args(parsed_args, playbooks):
    """Validate Kayobe Ansible arguments."""
    vault.enforce_single_password_source(parsed_args)
    result = utils.is_readable_dir(parsed_args.config_path)
    if not result["result"]:
        LOG.error("Kayobe configuration path %s is invalid: %s",
                  parsed_args.config_path, result["message"])
        sys.exit(1)

    if parsed_args.environment and parsed_args.environment == "kayobe":
        LOG.error("The environment name 'kayobe' is reserved for internal "
                  "use.")
        sys.exit(1)

    environment_finder = utils.EnvironmentFinder(
        parsed_args.config_path, parsed_args.environment)
    env_paths = environment_finder.ordered_paths()
    for env_path in env_paths:
        if env_path:
            result = utils.is_readable_dir(env_path)
            if not result["result"]:
                LOG.error("Kayobe environment %s is invalid: %s",
                          env_path, result["message"])
                sys.exit(1)

    inventories = _get_inventories_paths(parsed_args, env_paths)
    for inventory in inventories:
        result = utils.is_readable_dir(inventory)
        if not result["result"]:
            LOG.error("Kayobe inventory %s is invalid: %s",
                      inventory, result["message"])
            sys.exit(1)

    for playbook in playbooks:
        result = utils.is_readable_file(playbook)
        if not result["result"]:
            LOG.error("Kayobe playbook %s is invalid: %s",
                      playbook, result["message"])
            sys.exit(1)


def _get_vars_files(vars_paths):
    """Return a list of Kayobe Ansible configuration variable files.

    The list of directories given as argument is searched to create the list of
    variable files. The files will be sorted alphabetically by name for each
    directory, but ordering of directories is kept to allow overrides.
    """
    vars_files = []
    for vars_path in vars_paths:
        path_vars_files = []
        for vars_file in os.listdir(vars_path):
            abs_path = os.path.join(vars_path, vars_file)
            if utils.is_readable_file(abs_path)["result"]:
                root, ext = os.path.splitext(vars_file)
                if ext in (".yml", ".yaml", ".json"):
                    path_vars_files.append(abs_path)
        vars_files += sorted(path_vars_files)

    return vars_files


def build_args(parsed_args, playbooks,
               extra_vars=None, limit=None, tags=None, verbose_level=None,
               check=None, ignore_limit=False, list_tasks=None, diff=None):
    """Build arguments required for running Ansible playbooks."""
    cmd = ["ansible-playbook"]
    if verbose_level:
        cmd += ["-" + "v" * verbose_level]
    if list_tasks or (parsed_args.list_tasks and list_tasks is None):
        cmd += ["--list-tasks"]
    cmd += vault.build_args(parsed_args, "--vault-password-file")
    environment_finder = utils.EnvironmentFinder(
        parsed_args.config_path, parsed_args.environment)
    env_paths = environment_finder.ordered_paths()
    inventories = _get_inventories_paths(parsed_args, env_paths)
    for inventory in inventories:
        cmd += ["--inventory", inventory]
    vars_paths = [parsed_args.config_path]
    for env_path in env_paths:
        vars_paths.append(env_path)
    vars_files = _get_vars_files(vars_paths)
    for vars_file in vars_files:
        cmd += ["-e", "@%s" % vars_file]
    if parsed_args.extra_vars:
        for extra_var in parsed_args.extra_vars:
            # Don't quote or escape variables passed via the kayobe -e CLI
            # argument, to match Ansible's behaviour.
            cmd += ["-e", extra_var]
    if extra_vars:
        for extra_var_name, extra_var_value in extra_vars.items():
            # Quote and escape variables originating within the python CLI.
            extra_var_value = utils.quote_and_escape(extra_var_value)
            cmd += ["-e", "%s=%s" % (extra_var_name, extra_var_value)]
    if parsed_args.become:
        cmd += ["--become"]
    if check or (parsed_args.check and check is None):
        cmd += ["--check"]
    if diff or (parsed_args.diff and diff is None):
        cmd += ["--diff"]
    if not ignore_limit and (parsed_args.limit or limit):
        limit_arg = utils.intersect_limits(parsed_args.limit, limit)
        cmd += ["--limit", limit_arg]
    if parsed_args.skip_tags:
        cmd += ["--skip-tags", parsed_args.skip_tags]
    if parsed_args.tags or tags:
        all_tags = [t for t in [parsed_args.tags, tags] if t]
        cmd += ["--tags", ",".join(all_tags)]
    cmd += playbooks
    return cmd


def _get_environment(parsed_args, external_playbook=False):
    """Return an environment dict for executing an Ansible playbook."""
    env = os.environ.copy()
    vault.update_environment(parsed_args, env)
    # TODO(wszusmki): Kayobe still uses broken conditions. Work on fixing these
    # and remove when that work is complete.
    env.setdefault("ANSIBLE_ALLOW_BROKEN_CONDITIONALS", "true")
    # If the configuration path has been specified via --config-path, ensure
    # the environment variable is set, so that it can be referenced by
    # playbooks.
    env.setdefault(CONFIG_PATH_ENV, parsed_args.config_path)
    # If an environment has been specified via --environment, ensure the
    # environment variable is set, so that it can be referenced by playbooks.
    if parsed_args.environment:
        env.setdefault(ENVIRONMENT_ENV, parsed_args.environment)
    # If a custom Ansible configuration file exists, use it.
    ansible_cfg_path = os.path.join(parsed_args.config_path, "ansible.cfg")
    if utils.is_readable_file(ansible_cfg_path)["result"]:
        env.setdefault("ANSIBLE_CONFIG", ansible_cfg_path)

    # Update various role, collection and plugin paths to include the Kayobe
    # roles, collections and plugins. This allows custom playbooks to use these
    # resources.
    if external_playbook:
        roles_paths = [
            os.path.join(parsed_args.config_path, "ansible", "roles"),
            utils.get_data_files_path("ansible", "roles"),
        ]
    else:
        roles_paths = [
            utils.get_data_files_path("ansible", "roles"),
            os.path.join(parsed_args.config_path, "ansible", "roles"),
        ]

    env.setdefault("ANSIBLE_ROLES_PATH", ":".join(roles_paths))

    if external_playbook:
        collections_paths = [
            os.path.join(parsed_args.config_path, "ansible", "collections"),
            utils.get_data_files_path("ansible", "collections"),
        ]
    else:
        collections_paths = [
            utils.get_data_files_path("ansible", "collections"),
            os.path.join(parsed_args.config_path, "ansible", "collections"),
        ]

    env.setdefault("ANSIBLE_COLLECTIONS_PATH", ":".join(collections_paths))

    if external_playbook:
        action_plugins = [
            os.path.join(parsed_args.config_path, "ansible", "action_plugins"),
            utils.get_data_files_path("ansible", "action_plugins"),
        ]
    else:
        action_plugins = [
            utils.get_data_files_path("ansible", "action_plugins"),
            os.path.join(parsed_args.config_path, "ansible", "action_plugins"),
        ]

    env.setdefault("ANSIBLE_ACTION_PLUGINS", ":".join(action_plugins))

    if external_playbook:
        filter_plugins = [
            os.path.join(parsed_args.config_path, "ansible", "filter_plugins"),
            utils.get_data_files_path("ansible", "filter_plugins"),
        ]
    else:
        filter_plugins = [
            utils.get_data_files_path("ansible", "filter_plugins"),
            os.path.join(parsed_args.config_path, "ansible", "filter_plugins"),
        ]

    env.setdefault("ANSIBLE_FILTER_PLUGINS", ":".join(filter_plugins))

    if external_playbook:
        test_plugins = [
            os.path.join(parsed_args.config_path, "ansible", "test_plugins"),
            utils.get_data_files_path("ansible", "test_plugins"),
        ]
    else:
        test_plugins = [
            utils.get_data_files_path("ansible", "test_plugins"),
            os.path.join(parsed_args.config_path, "ansible", "test_plugins"),
        ]

    env.setdefault("ANSIBLE_TEST_PLUGINS", ":".join(test_plugins))

    return env


def run_playbooks(parsed_args, playbooks,
                  extra_vars=None, limit=None, tags=None, quiet=False,
                  check_output=False, verbose_level=None, check=None,
                  ignore_limit=False, list_tasks=None, diff=None):
    """Run a Kayobe Ansible playbook."""
    _validate_args(parsed_args, playbooks)
    cmd = build_args(parsed_args, playbooks,
                     extra_vars=extra_vars, limit=limit, tags=tags,
                     verbose_level=verbose_level, check=check,
                     ignore_limit=ignore_limit, list_tasks=list_tasks,
                     diff=diff)
    first_playbook = os.path.realpath(playbooks[0])
    external_playbook = False
    if not first_playbook.startswith(os.path.realpath(
            utils.get_data_files_path("ansible"))):
        external_playbook = True
    env = _get_environment(parsed_args, external_playbook)
    try:
        utils.run_command(cmd, check_output=check_output, quiet=quiet, env=env)
    except subprocess.CalledProcessError as e:
        LOG.error("Kayobe playbook(s) %s exited %d",
                  ", ".join(playbooks), e.returncode)
        if check_output:
            LOG.error("The output was:\n%s", e.output)
        sys.exit(e.returncode)


def run_playbook(parsed_args, playbook, *args, **kwargs):
    """Run a Kayobe Ansible playbook."""
    return run_playbooks(parsed_args, [playbook], *args, **kwargs)


def _sanitise_hostvar(var):
    """Sanitise a host variable."""
    if isinstance(var, EncryptedString):
        return "******"
    # Recursively sanitise dicts and lists.
    if isinstance(var, dict):
        return {k: _sanitise_hostvar(v) for k, v in var.items()}
    if isinstance(var, list):
        return [_sanitise_hostvar(v) for v in var]
    return var


def config_dump(parsed_args, host=None, hosts=None, var_name=None,
                facts=None, extra_vars=None, tags=None, verbose_level=None):
    dump_dir = tempfile.mkdtemp()
    try:
        if not extra_vars:
            extra_vars = {}
        extra_vars["dump_path"] = dump_dir
        if host or hosts:
            extra_vars["dump_hosts"] = host or hosts
        if var_name:
            extra_vars["dump_var_name"] = var_name
        if facts is not None:
            extra_vars["dump_facts"] = facts
        # Don't use check mode or list tasks for configuration dumps as we
        # won't get any results back.
        playbook_path = utils.get_data_files_path("ansible", "dump-config.yml")
        run_playbook(parsed_args, playbook_path,
                     extra_vars=extra_vars, tags=tags, check_output=True,
                     verbose_level=verbose_level, check=False,
                     list_tasks=False, diff=False)
        hostvars = {}
        for path in os.listdir(dump_dir):
            LOG.debug("Found dump file %s", path)
            inventory_hostname, ext = os.path.splitext(path)
            if ext == ".yml":
                dump_file = os.path.join(dump_dir, path)
                hvars = utils.read_config_dump_yaml_file(dump_file)
                if host:
                    return hvars
                else:
                    hostvars[inventory_hostname] = hvars
            else:
                LOG.warning("Unexpected extension on config dump file %s",
                            path)
        return {k: _sanitise_hostvar(v) for k, v in hostvars.items()}
    finally:
        shutil.rmtree(dump_dir)


def install_galaxy_roles(parsed_args, force=False):
    """Install Ansible Galaxy role dependencies.

    Installs role dependencies specified in kayobe, and if present, in kayobe
    configuration.

    :param parsed_args: Parsed command line arguments.
    :param force: Whether to force reinstallation of roles.
    """
    LOG.info("Installing galaxy role dependencies from kayobe")
    requirements = utils.get_data_files_path("requirements.yml")
    roles_destination = utils.get_data_files_path('ansible', 'roles')
    utils.galaxy_role_install(requirements, roles_destination, force=force)

    # Check for requirements in kayobe configuration.
    kc_reqs_path = os.path.join(parsed_args.config_path,
                                "ansible", "requirements.yml")
    if not utils.is_readable_file(kc_reqs_path)["result"]:
        LOG.info("Not installing galaxy role dependencies from kayobe config "
                 "- requirements.yml not present")
        return

    LOG.info("Installing galaxy role dependencies from kayobe config")
    # Ensure a roles directory exists in kayobe-config.
    kc_roles_path = os.path.join(parsed_args.config_path,
                                 "ansible", "roles")
    try:
        os.makedirs(kc_roles_path)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise exception.Error("Failed to create directory ansible/roles/ "
                                  "in kayobe configuration at %s: %s" %
                                  (parsed_args.config_path, str(e)))

    # Install roles from kayobe-config.
    utils.galaxy_role_install(kc_reqs_path, kc_roles_path, force=force)


def install_galaxy_collections(parsed_args, force=False):
    """Install Ansible Galaxy collection dependencies.

    Installs collection dependencies specified in kayobe, and if present, in
    kayobe configuration.

    :param parsed_args: Parsed command line arguments.
    :param force: Whether to force reinstallation of roles.
    """
    LOG.info("Installing galaxy collection dependencies from kayobe")
    requirements = utils.get_data_files_path("requirements.yml")
    collections_destination = utils.get_data_files_path('ansible',
                                                        'collections')
    utils.galaxy_collection_install(requirements, collections_destination,
                                    force=force)

    # Check for requirements in kayobe configuration.
    kc_reqs_path = os.path.join(parsed_args.config_path,
                                "ansible", "requirements.yml")
    if not utils.is_readable_file(kc_reqs_path)["result"]:
        LOG.info("Not installing galaxy collection dependencies from kayobe "
                 "config - requirements.yml not present")
        return

    LOG.info("Installing galaxy collection dependencies from kayobe config")
    # Ensure a collections directory exists in kayobe-config.
    kc_collections_path = os.path.join(parsed_args.config_path,
                                       "ansible", "collections")
    try:
        os.makedirs(kc_collections_path)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise exception.Error("Failed to create directory "
                                  "ansible/collections/ "
                                  "in kayobe configuration at %s: %s" %
                                  (parsed_args.config_path, str(e)))

    # Install collections from kayobe-config.
    utils.galaxy_collection_install(kc_reqs_path, kc_collections_path,
                                    force=force)


def prune_galaxy_roles(parsed_args):
    """Prune galaxy roles that are no longer necessary.

    :param parsed_args: Parsed command line arguments.
    """
    LOG.info("Removing unnecessary galaxy roles from kayobe")
    roles_to_remove = [
        'resmo.ntp',
        'stackhpc.ntp',
        'stackhpc.os-shade',
        'yatesr.timezone',
    ]
    LOG.debug("Removing roles: %s", ",".join(roles_to_remove))
    utils.galaxy_remove(roles_to_remove, "ansible/roles")


def passwords_yml_exists(parsed_args):
    """Return whether passwords.yml exists in the kayobe configuration."""
    env_path = utils.get_kayobe_environment_path(
        parsed_args.config_path, parsed_args.environment)
    path = env_path if env_path else parsed_args.config_path
    passwords_path = os.path.join(path, 'kolla', 'passwords.yml')
    return utils.is_readable_file(passwords_path)["result"]
