import logging
import os
import subprocess
import sys
import yaml


LOG = logging.getLogger(__name__)


def yum_install(packages):
    """Install a list of packages via Yum."""
    cmd = ["sudo", "yum", "-y", "install"]
    cmd += packages
    try:
        subprocess.check_call(cmd)
    except subprocess.CalledProcessError as e:
        print ("Failed to install packages %s via Yum: returncode %d" %
               (", ".join(packages), e.returncode))
        sys.exit(e.returncode)


def read_yaml_file(path):
    """Read and decode a YAML file."""
    try:
        with open(path, "r") as f:
            content = f.read()
    except IOError as e:
        print ("Failed to open config dump file %s: %s" %
               (path, repr(e)))
        sys.exit(1)
    try:
        return yaml.load(content)
    except ValueError as e:
        print ("Failed to decode config dump YAML file %s: %s" %
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


def run_command(cmd, quiet=False, **kwargs):
    """Run a command, checking the output."""
    if quiet:
        kwargs["stdout"] = subprocess.PIPE
        kwargs["stderr"] = subprocess.PIPE
    LOG.debug("Running command: %s", " ".join(cmd))
    subprocess.check_call(cmd, **kwargs)
