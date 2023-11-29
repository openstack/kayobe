# Copyright (c) 2023 StackHPC Ltd.
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

from ansible.plugins.action import ActionBase
import os
from collections import defaultdict
import pathlib

from wcmatch import glob

def _dedup(xs):
    # Deduplicate a list whilst maintaining order
    seen = set()
    result = []
    for x in xs:
        if x not in seen:
            seen.add(x)
            result.append(x)
    return result

class ConfigCollector(object):
    def __init__(self, include_globs, ignore_globs, destination, search_paths,
                 rules):
        # This variable groups together files in the search paths with
        # the same relative path, for example if the search paths were:
        # - {{ kayobe_config_env_path }}/
        # - {{ kayobe_config_path }}/
        # - {{ role_path }}/templates/
        # and one of the include_globs matched nova.conf. You'd end up
        # with the following files grouped together:
        # - {{ kayobe_env_path }}/etc/kolla/nova.conf
        # - {{ kayobe_config_path }}/etc/kolla/nova.conf
        # - {{ role_path }}/templates/etc/kolla/nova.conf
        # The key in the dictionary is the relative path of the file. The
        # value is a list of absolute paths. This gets populated by the
        # collect() method.
        self.files_in_source = defaultdict(list)
        # Set of files in destination. This is used to cleanup up files
        # from a previous run that are no longer templated. Before any templating
        # this variable is populated with all the files in the output directory.
        # Each file that would be templated in the current run will be removed
        # from this set as they are discovered.
        self.files_in_destination = set()
        # Determines which files are candidates for templating
        self.include_globs = include_globs
        # Some files are templated by external tasks. This is a list of files
        # to not clean up.
        self.ignore_globs = ignore_globs
        # Where the files are being templated to
        self.destination = destination
        # Where to search for the source files
        self.search_paths = search_paths

        # Rules to determine merging strategy when multiple files are found
        # with the same relative path. Lower priority numbers win.
        self.rules = sorted(rules, key=lambda d: d['priority'])

    def filter_files_in_destination(self):
        ignored = set()
        for f in self.files_in_destination:
            for item in self.ignore_globs:
                if not item["enabled"]:
                    continue
                if glob.globmatch(f, item["glob"], flags=glob.GLOBSTAR):
                    ignored.add(f)
        result = set(self.files_in_destination) - ignored
        return list(result)

    def _find_matching_rule(self, relative_path, sources):
        # First match wins
        for rule in self.rules:
            if not rule.get('enabled', True):
                continue
            glob_ = rule["glob"]
            if glob.globmatch(relative_path, glob_, flags=glob.GLOBSTAR):
                requires_merge = (rule["strategy"] in
                    ["merge_configs", "merge_yaml"])
                # Fallback to templating when there is only one source. This
                # allows you to have config files that template to invalid
                # yaml/ini. This was allowed prior to config merging so
                # improves backwards compatibility.
                if requires_merge and len(sources) == 1:
                    # The rule can be used again to match a different file
                    # so don't modify in place.
                    rule = rule.copy()
                    rule["strategy"] = 'template'
                    # Strip parameters as they may not be compatible with
                    # template module.
                    rule['params'] = {}
                return rule

    def partition_into_actions(self):
        actions = {
            "merge_yaml": [],
            "merge_configs": [],
            "template": [],
            "copy": [],
            "concat": [],
            "create_dir": [],
            "delete": []
        }
        missing_directories = set()
        files_to_delete = self.filter_files_in_destination()

        # Convert to absolute paths
        files_to_delete = {
            os.path.join(self.destination, x) for x in files_to_delete
        }

        for relative_path, sources in self.files_in_source.items():
            found_match = False
            destination = os.path.join(self.destination, relative_path)
            # Don't delete any files we are templating
            files_to_delete.discard(destination)

            dirname = os.path.dirname(destination)
            if not os.path.exists(dirname):
                missing_directories.add(dirname)

            sources = map(os.path.realpath, sources)
            sources = _dedup(sources)

            rule = self._find_matching_rule(relative_path, sources)

            if not rule:
                continue

            if rule["strategy"] == 'copy':
                copy = {
                    "src": sources[-1],
                    "dest": destination,
                    "params": rule.get('params', [])
                }
                actions["copy"].append(copy)
                continue

            if rule["strategy"] == "merge_yaml":
                merge_yaml = {
                    "sources": sources,
                    "dest": destination,
                    "params": rule.get('params', [])
                }
                actions["merge_yaml"].append(merge_yaml)
                continue

            if rule["strategy"] == "merge_configs":
                merge_configs = {
                    "sources": sources,
                    "dest": destination,
                    "params": rule.get('params', [])
                }
                actions["merge_configs"].append(merge_configs)
                continue

            if rule["strategy"] == "concat":
                concat = {
                    "sources": sources,
                    "dest": destination,
                    "params": rule.get('params', [])
                }
                actions["concat"].append(concat)
                continue

            if rule["strategy"] == "template":
                template = {
                    "src": sources[-1],
                    "dest": destination,
                    "params": rule.get('params', [])
                }
                actions["template"].append(template)
                continue

        actions["create_dir"] = list(missing_directories)
        # Sort by length so that subdirectories are created after the parent
        actions["create_dir"].sort(key=len)

        actions["delete"] = list(files_to_delete)
        return actions

    def collect(self):
        for item in self.include_globs:
            self._collect_source(item)
            self._collect_destination(item)

    def _collect_source(self, item):
        enabled = item.get("enabled", False)
        if not isinstance(enabled, bool):
            raise ValueError("Expecting a boolean: %s" % item)
        if not enabled:
            return
        for search_path in self.search_paths:
            abs_glob = os.path.join(search_path, item["glob"])
            files = glob.glob(abs_glob, flags=glob.GLOBSTAR)
            for abs_path in files:
                if not os.path.isfile(abs_path):
                    continue
                relative_path = os.path.relpath(abs_path, search_path)
                self.files_in_source[relative_path].append(abs_path)

    def _collect_destination(self, item):
        abs_glob = os.path.join(self.destination, item["glob"])
        files = glob.glob(abs_glob, flags=glob.GLOBSTAR)
        for abs_path in files:
            if not os.path.isfile(abs_path):
                continue
            relative_path = os.path.relpath(abs_path, self.destination)
            self.files_in_destination.add(relative_path)

class ActionModule(ActionBase):

    def run(self, tmp=None, task_vars=None):
        if task_vars is None:
            task_vars = dict()

        result = super(ActionModule, self).run(tmp, task_vars)

        # This class never changes anything. We only collect the extra config
        # files and group by action.
        result['changed'] = False

        args = self._task.args

        collector = ConfigCollector(
            destination=args.get("destination"),
            ignore_globs=args.get("ignore_globs"),
            include_globs=args.get("include_globs"),
            rules=args.get("rules"),
            search_paths=_dedup(args["search_paths"])
        )

        collector.collect()

        result.update(collector.partition_into_actions())

        return result
