# Copyright (c) 2018 StackHPC Ltd.
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

import re

import configparser
from io import StringIO


def test_file(host, path, owner='root', group='root'):
    """Test an expected file.

    Validate that the file exists and has the correct ownership.
    """
    f = host.file(path)

    assert f.exists
    assert f.is_file
    assert owner == f.user
    assert group == f.group


def test_ini_file(host, path, owner='root', group='root', expected=None):
    """Test an expected INI file.

    Validate that the file exists, has the correct ownership, format and
    expected contents.

    :param expected: a dict of dicts providing config that should be present.
    """
    test_file(host, path, owner, group)

    sio = StringIO(host.file(path).content_string)
    parser = configparser.RawConfigParser()
    parser.read_file(sio)

    if expected is None:
        return

    for exp_section_name, exp_section in expected.items():
        assert parser.has_section(exp_section_name)
        for exp_key, exp_value in exp_section.items():
            assert parser.has_option(exp_section_name, exp_key)
            assert parser.get(exp_section_name, exp_key) == exp_value


def test_regex_in_file(host, path, owner='root', group='root', regex=None):
    """Test that a regex exists in file

    Validate that the file exists, has the correct ownership, format and
    expected contents.

    :param regex to search for in file
    """
    test_file(host, path, owner, group)

    matches = re.findall(regex, host.file(path).content_string)

    assert len(matches) > 0


def test_directory(host, path, owner='root', group='root'):
    """Test an expected directory.

    Validate that the directory exists and has the correct ownership.
    """
    d = host.file(path)

    assert d.exists
    assert d.is_directory
    assert owner == d.user
    assert group == d.group


def test_path_absent(host, path):
    """Test a path expected to not exist."""
    p = host.file(path)

    assert not p.exists
