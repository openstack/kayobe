#!/usr/bin/python3

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

DOCUMENTATION = '''
---
module: kolla_passwords
short_description: Generates a kolla-ansible passwords file
'''

from ansible.module_utils.basic import *

import os.path
import shutil
import tempfile

IMPORT_ERRORS = []
try:
    import yaml
except ImportError as e:
    IMPORT_ERRORS.append(e)


def virtualenv_path_prefix(module):
    return "%s/bin" % module.params['virtualenv']


def kolla_genpwd(module, file_path):
    """Run the kolla-genpwd command."""
    cmd = ["kolla-genpwd", "--passwords", file_path]
    module.run_command(cmd, check_rc=True,
                       path_prefix=virtualenv_path_prefix(module))


def kolla_mergepwd(module, old_path, new_path, final_path):
    """Run the kolla-mergepwd command."""
    cmd = ["kolla-mergepwd",
           "--old", old_path,
           "--new", new_path,
           "--final", final_path]
    module.run_command(cmd, check_rc=True,
                       path_prefix=virtualenv_path_prefix(module))


def create_vault_password_file(module):
    """Create a vault password file."""
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(module.params['vault_password'].encode())
        return f.name


def vault_encrypt(module, file_path):
    """Encrypt a file using Ansible vault"""
    password_path = create_vault_password_file(module)
    try:
        cmd = ["ansible-vault", "encrypt",
               "--vault-password-file", password_path,
               file_path]
        module.run_command(cmd, check_rc=True,
                           path_prefix=virtualenv_path_prefix(module))
    finally:
        os.unlink(password_path)


def vault_decrypt(module, file_path):
    """Decrypt a file using Ansible vault"""
    password_path = create_vault_password_file(module)
    try:
        cmd = ["ansible-vault", "decrypt",
               "--vault-password-file", password_path,
               file_path]
        module.run_command(cmd, check_rc=True,
                           path_prefix=virtualenv_path_prefix(module))
    finally:
        os.unlink(password_path)


def create_named_tempfile():
    """Create a named temporary file and return its name."""
    with tempfile.NamedTemporaryFile(delete=False) as f:
        temp_file_path = f.name
        f.close()
    return temp_file_path


def kolla_passwords(module):
    """Generate a kolla-ansible passwords.yml file.

    We use the sample passwords.yml file as a base to determine which passwords
    to generate. This gets merged with an existing passwords file if one
    exists.  We then apply any custom password overrides. Finally, we generate
    any passwords that are missing.  If requested, the final file will be
    encrypted using ansible vault.
    """
    if not os.path.isfile(module.params['sample']):
        module.fail_json(msg="Sample passwords.yml file %s does not exist" %
                         module.params['sample'])

    temp_file_path = create_named_tempfile()
    try:
        # Start with kolla's sample password file.
        shutil.copyfile(module.params['sample'], temp_file_path)

        # If passwords exist, decrypt and merge these in.
        if module.params['src'] and os.path.isfile(module.params['src']):
            src_path = create_named_tempfile()
            try:
                shutil.copyfile(module.params['src'], src_path)
                if module.params['vault_password']:
                    vault_decrypt(module, src_path)
                kolla_mergepwd(module, src_path, temp_file_path, temp_file_path)
            finally:
                os.unlink(src_path)

        # Merge in overrides.
        if module.params['overrides']:
            with tempfile.NamedTemporaryFile(delete=False) as f:
                # NOTE(mgoddard): Temporary files are opened in binary mode, so
                # specify an encoding.
                yaml.dump(module.params['overrides'], f, encoding='utf-8')
                overrides_path = f.name
            try:
                kolla_mergepwd(module, overrides_path, temp_file_path, temp_file_path)
            finally:
                os.unlink(overrides_path)

        # Generate null passwords.
        kolla_genpwd(module, temp_file_path)

        # Compare with the decrypted destination file.
        if os.path.isfile(module.params['dest']):
            if module.params['vault_password']:
                dest_path = create_named_tempfile()
                try:
                    shutil.copyfile(module.params['dest'], dest_path)
                    vault_decrypt(module, dest_path)
                    checksum_dest = module.sha1(dest_path)
                finally:
                    os.unlink(dest_path)
            else:
                checksum_dest = module.sha1(module.params['dest'])
            checksum_temp_file = module.sha1(temp_file_path)
            changed = checksum_dest != checksum_temp_file
        else:
            changed = True

        # Encrypt the file.
        if changed and module.params['vault_password']:
            vault_encrypt(module, temp_file_path)

        # Move into place.
        if changed and not module.check_mode:
            module.atomic_move(temp_file_path, module.params['dest'])
    except Exception as e:
        module.fail_json(msg="Failed to generate kolla passwords: %s" % repr(e))
    finally:
        if os.path.isfile(temp_file_path):
            os.unlink(temp_file_path)

    if not module.check_mode:
        # Update the file's attributes.
        file_args = module.load_file_common_arguments(module.params)
        changed = module.set_fs_attributes_if_different(file_args, changed)

    return {'changed': changed}


def main():
    module = AnsibleModule(
        argument_spec = dict(
            dest=dict(default='/etc/kolla/passwords.yml', type='str'),
            overrides=dict(default={}, type='dict'),
            sample=dict(default='/usr/share/kolla-ansible/etc_examples/kolla/passwords.yml', type='str'),
            src=dict(default='/etc/kolla/passwords.yml', type='str'),
            vault_password=dict(type='str', no_log=True),
            virtualenv=dict(type='str'),
        ),
        add_file_common_args=True,
        supports_check_mode=True,
    )

    if IMPORT_ERRORS:
        errors = ", ".join([repr(e) for e in IMPORT_ERRORS])
        module.fail_json(msg="Failed to import modules: %s" % errors)

    result = kolla_passwords(module)
    module.exit_json(**result)

if __name__ == '__main__':
    main()
