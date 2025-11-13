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

import base64
from collections import defaultdict
import configparser
import glob
import graphlib
from importlib.metadata import Distribution
import json
import logging
import os
import shutil
import subprocess
import sys
from urllib.parse import unquote
from urllib.parse import urlparse

from ansible.parsing.yaml.loader import AnsibleLoader
import yaml

from kayobe import exception


LOG = logging.getLogger(__name__)


def get_data_files_path(*relative_path):
    """Given a relative path to a data file, return the absolute path"""
    # Detect editable pip install / python setup.py develop and use a path
    # relative to the source directory
    return os.path.join(_get_base_path(), *relative_path)


def _detect_install_prefix(path):
    script_path = os.path.realpath(path)
    script_path = os.path.normpath(script_path)
    components = script_path.split(os.sep)
    # use heuristic: anything before the last 'lib' in path is the prefix
    if 'lib' not in components:
        return None
    last_lib = len(components) - 1 - components[::-1].index('lib')
    prefix = components[:last_lib]
    prefix_path = os.sep.join(prefix)
    return prefix_path


def _get_direct_url_if_editable(dist):
    direct_url = os.path.join(dist._path, 'direct_url.json')
    editable = None
    if os.path.isfile(direct_url):
        with open(direct_url, 'r') as f:
            direct_url_content = json.loads(f.readline().strip())
            dir_info = direct_url_content.get('dir_info')
            if dir_info is not None:
                editable = dir_info.get('editable')
            if editable:
                url = direct_url_content['url']
                prefix = 'file://'
                if url.startswith(prefix):
                    return unquote(urlparse(url).path)

    return None


def _get_base_path():
    override = os.environ.get("KAYOBE_DATA_FILES_PATH")
    if override:
        return os.path.join(override)

    kayobe_dist = list(Distribution.discover(name="kayobe"))
    if kayobe_dist:
        direct_url = _get_direct_url_if_editable(kayobe_dist[0])
        if direct_url:
            return direct_url

    egg_glob = os.path.join(
        sys.prefix, 'lib*', 'python*', '*-packages', 'kayobe.egg-link'
    )
    egg_link = glob.glob(egg_glob)
    if egg_link:
        with open(egg_link[0], "r") as f:
            realpath = f.readline().strip()
        return os.path.join(realpath)

    prefix = _detect_install_prefix(__file__)
    if prefix:
        return os.path.join(prefix, "share", "kayobe")

    # Assume uninstalled
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), "..")


def galaxy_role_install(role_file, roles_path, force=False):
    """Install Ansible roles via Ansible Galaxy."""
    cmd = ["ansible-galaxy", "role", "install"]
    cmd += ["--roles-path", roles_path]
    cmd += ["--role-file", role_file]
    if force:
        cmd += ["--force"]
    try:
        run_command(cmd)
    except subprocess.CalledProcessError as e:
        LOG.error("Failed to install Ansible roles from %s via Ansible "
                  "Galaxy: returncode %d", role_file, e.returncode)
        sys.exit(e.returncode)


def galaxy_collection_install(requirements_file, collections_path,
                              force=False):
    requirements = read_yaml_file(requirements_file)
    if not isinstance(requirements, dict):
        # Handle legacy role list format, which causes the command to fail.
        return
    cmd = ["ansible-galaxy", "collection", "install"]
    cmd += ["--collections-path", collections_path]
    cmd += ["--requirements-file", requirements_file]
    env_defaults = {
        # NOTE(wszumski): Allow overriding of ansible builtin collections in
        # kayobe requirements.yml.
        "ANSIBLE_COLLECTIONS_SCAN_SYS_PATH": "False",
    }
    env = env_defaults | os.environ
    if force:
        cmd += ["--force"]
    try:
        run_command(cmd, env=env)
    except subprocess.CalledProcessError as e:
        LOG.error("Failed to install Ansible collections from %s via Ansible "
                  "Galaxy: returncode %d", requirements_file, e.returncode)
        sys.exit(e.returncode)


def galaxy_remove(roles_to_remove, roles_path):

    """Remove Ansible roles via Ansible Galaxy."""
    cmd = ["ansible-galaxy", "role", "remove"]
    cmd += ["--roles-path", roles_path]
    cmd += roles_to_remove
    try:
        run_command(cmd)
    except subprocess.CalledProcessError as e:
        LOG.error("Failed to remove Ansible roles %s via Ansible "
                  "Galaxy: returncode %d",
                  ",".join(roles_to_remove), e.returncode)
        sys.exit(e.returncode)


def read_file(path, mode="r"):
    """Read the content of a file."""
    with open(path, mode) as f:
        return f.read()


def read_yaml_file(path):
    """Read and decode a YAML file."""
    try:
        content = read_file(path)
    except IOError as e:
        print("Failed to open YAML file %s: %s" %
              (path, repr(e)))
        sys.exit(1)
    try:
        return yaml.safe_load(content)
    except yaml.YAMLError as e:
        print("Failed to decode YAML file %s: %s" %
              (path, repr(e)))
        sys.exit(1)


def read_config_dump_yaml_file(path):
    """Read and decode a configuration dump YAML file."""
    try:
        content = read_file(path)
    except IOError as e:
        print("Failed to open config dump file %s: %s" %
              (path, repr(e)))
        sys.exit(1)
    try:
        # AnsibleLoader supports loading vault encrypted variables.
        data = AnsibleLoader(content).get_single_data()
        return data
    except yaml.YAMLError as e:
        print("Failed to decode config dump YAML file %s: %s" %
              (path, repr(e)))
        sys.exit(1)


def is_readable_dir(path):
    """Check whether a path references a readable directory."""
    if not os.path.exists(path):
        return {"result": False, "message": "Path does not exist"}
    if not os.path.isdir(path):
        return {"result": False, "message": "Path is not a directory"}
    if not os.access(path, os.R_OK):
        return {"result": False, "message": "Directory is not readable"}
    return {"result": True}


def is_readable_file(path):
    """Check whether a path references a readable file."""
    if not os.path.exists(path):
        return {"result": False, "message": "Path does not exist"}
    if not os.path.isfile(path):
        return {"result": False, "message": "Path is not a file"}
    if not os.access(path, os.R_OK):
        return {"result": False, "message": "File is not readable"}
    return {"result": True}


def run_command(cmd, quiet=False, check_output=False, **kwargs):
    """Run a command, checking the output.

    :param quiet: Redirect output to /dev/null
    :param check_output: Whether to return the output of the command
    :returns: The output of the command if check_output is true
    """
    if isinstance(cmd, str):
        cmd_string = cmd
    else:
        cmd_string = " ".join(cmd)
    LOG.debug("Running command: %s", cmd_string)
    if quiet:
        kwargs["stderr"] = subprocess.DEVNULL
        if not check_output:
            kwargs["stdout"] = subprocess.DEVNULL
    if check_output:
        return subprocess.check_output(cmd, **kwargs)
    else:
        subprocess.check_call(cmd, **kwargs)


def quote_and_escape(value):
    """Quote and escape a string.

    Adds enclosing single quotes to the string passed, and escapes single
    quotes within the string using backslashes. This is useful for passing
    'extra vars' to Ansible. Without this, Ansible only uses the part of the
    string up to the first whitespace.

    :param value: the string to quote and escape.
    :returns: the quoted and escaped string.
    """
    if not isinstance(value, str):
        return value
    return "'" + value.replace("'", "'\\''") + "'"


def escape_jinja(string):
    """Escapes a string so that jinja template variables are not expanded

    :param string: the string to escape
    :return: the escaped string
    """
    # We base64 encode the string to avoid the need to escape characters.
    # This is because ansible has some parsing quirks that makes it fairly
    # hard to escape stuff in generic way.
    # See: https://github.com/ansible/ansible/issues/10464

    b64_value = base64.b64encode(string.encode())
    return ''.join(('{{', "'", b64_value.decode(), "' | b64decode ", '}}'))


def intersect_limits(args_limit, cli_limit):
    """Create an Ansible host pattern of the intersection of two patterns.

    :param args_limit: user-specified limit, or None.
    :param cli_limit: limit originating from this CLI, or None.
    :returns: a string representing an intersection of the two patterns.
    """
    # NOTE(mgoddard): Ansible uses either commas (,) or colons (:) to separate
    # parts of a host pattern. An intersection is specified using a separator
    # followed by an ampersand (&). If a mix of comma and colon separators is
    # used, Ansible picks one and treats the other as part of the host pattern.
    # This leads to hard to diagnose errors. Try to determine which separator
    # the user has specified, and be consistent. Error if both are used.
    if args_limit and ',' in args_limit:
        if ':' in args_limit:
            raise exception.Error("Invalid format for host limit argument. "
                                  "Cannot mix commas and colons to separate "
                                  "hosts")
        separator = ',&'
    else:
        separator = ':&'
    limits = [limit for limit in [args_limit, cli_limit] if limit]
    return separator.join(limits)


def copy_dir(src, dest, exclude=None):
    """Copy recursively a directory.

    :param src: path of the source directory
    :param dest: destination path, will be created if it does not exist
    :param exclude: names of files or directories at the root of the source
                    directory to exclude during copy
    """
    if exclude is None:
        exclude = []

    if not os.path.isdir(dest):
        os.mkdir(dest)

    for file in os.listdir(src):
        if file in exclude:
            continue

        src_path = os.path.join(src, file)
        dest_path = os.path.join(dest, file)
        if os.path.isdir(src_path):
            copy_dir(src_path, dest_path)
        else:
            shutil.copy2(src_path, dest_path)


def get_kayobe_environment_path(base_path, environment):
    """Return the path to the Kayobe environment or None if not specified."""
    env_path = None
    if environment:
        # Specified via --environment or KAYOBE_ENVIRONMENT.
        kc_environments = os.path.join(base_path, "environments")
        env_path = os.path.join(kc_environments, environment)
    return env_path


class EnvironmentFinder(object):
    """Dependency resolver for kayobe environments

    The constraints are specified via a .kayobe-environment file.
    """

    def __new__(cls, base_path, environment):
        # Singleton instance so we don't have to resolve dependencies multiple
        # times or pass round a single instance.
        it = cls.__dict__.get("__it__")
        if it is None:
            it = {}
        if (base_path, environment) in it:
            return it[(base_path, environment)]
        singleton = object.__new__(cls)
        singleton._init(base_path, environment)
        it[(base_path, environment)] = singleton
        return singleton

    def _init(self, base_path, environment):
        self._base_path = base_path
        self._environment = environment
        self._ordering = None

    @staticmethod
    def _read_metadata(path):
        if os.path.exists(path) and os.path.isfile(path):
            metadata = read_yaml_file(path)
            return metadata
        return {}

    def _collect(self, environment, result, visited):
        # Updates result to contain dependency graph
        base = self._base_path
        env_path = os.path.join(base, 'environments', environment)
        dot_environment_path = os.path.join(env_path, '.kayobe-environment')
        if dot_environment_path in visited:
            return
        visited.add(dot_environment_path)
        metadata = EnvironmentFinder._read_metadata(dot_environment_path)
        dependencies = metadata.get("dependencies", [])
        if not isinstance(dependencies, list):
            raise exception.Error(".kayobe-environment: dependencies field "
                                  "should be a list")
        result[environment] |= set(dependencies)
        for dependency in dependencies:
            if not isinstance(dependency, str):
                raise exception.Error("Kayobe environment dependency items "
                                      "should be strings")
            self._collect(dependency, result, visited)

    def ordered(self):
        """List of environments ordered by the constraints"""
        environment = self._environment
        if not environment:
            return []
        if self._ordering is not None:
            return self._ordering.copy()
        graph = defaultdict(set)
        self._collect(environment, graph, set())
        ts = graphlib.TopologicalSorter(graph)
        try:
            ordering = list(ts.static_order())
        except graphlib.CycleError as e:
            # https://docs.python.org/3/library/graphlib.html#graphlib.CycleError
            cycle = e.args[1]
            raise exception.Error("You have created a cycle with your "
                                  "environment dependencies. Please break "
                                  "this cycle and try again. The cycle is: %s"
                                  % cycle)
        self._ordering = ordering if ordering else [environment]
        return self._ordering.copy()

    def ordered_paths(self):
        """Paths to each environment ordered by the constraints"""
        result = []
        environments = self.ordered()
        for environment in environments:
            full_path = get_kayobe_environment_path(
                self._base_path,
                environment
            )
            result.append(full_path)
        return result


def _gitreview_is_kayobe_config(gitreview_path):
    """Return whether a .gitreview file is for kayobe-config."""
    config = configparser.ConfigParser()
    config_string = read_file(gitreview_path)
    config.read_string(config_string)
    gerrit_project = config.get('gerrit', 'project')
    if not gerrit_project:
        return False
    gerrit_project = os.path.basename(gerrit_project)
    gerrit_project = os.path.splitext(gerrit_project)[0]
    if gerrit_project == 'kayobe-config':
        return True


def validate_config_path(config_path):
    """Validate the Kayobe configuration path.

    Check whether we are executing from inside a Kayobe configuration
    repository, and if so, assert that matches the Kayobe configuration path
    defined in CLI args or environment variables.

    Exit 1 if validation fails.

    :param config_path: Kayobe configuration path or None.
    """
    assert config_path

    try:
        cmd = ["git", "rev-parse", "--show-toplevel"]
        repo_root = run_command(cmd, quiet=True, check_output=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        # FileNotFoundError: git probably not installed.
        # CalledProcessError: probably not in a git repository.
        return

    repo_root = repo_root.decode().strip()
    if config_path:
        repo_config_path = os.path.join(repo_root, "etc", "kayobe")
        if repo_config_path == os.path.realpath(config_path):
            return

    # Paths did not match. Check that repo_root does not look like a Kayobe
    # configuration repo.
    gitreview_path = os.path.join(repo_root, ".gitreview")
    result = is_readable_file(gitreview_path)
    if result["result"]:
        if _gitreview_is_kayobe_config(gitreview_path):
            LOG.error("Executing from within a different Kayobe configuration "
                      "repository is not allowed")
            sys.exit(1)
