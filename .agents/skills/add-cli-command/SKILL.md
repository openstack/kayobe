---
name: add-cli-command
description: "Add a new Kayobe CLI command end-to-end. Use when: adding a CLI subcommand, creating a new kayobe command, wiring up a playbook to the CLI. Touches commands.py, setup.cfg, playbook, and unit test."
---

# Add a Kayobe CLI Command

## When to Use

- Adding a new `kayobe <noun> <verb>` command
- Wiring an existing or new Ansible playbook into the CLI

## Procedure

### 1. Define the command class in `kayobe/cli/commands.py`

Choose the right mixin combination:

| If the command runs... | Inherit from |
|---|---|
| Only Kayobe playbooks | `KayobeAnsibleMixin, VaultMixin, Command` |
| Kayobe + Kolla Ansible | `KollaAnsibleMixin, KayobeAnsibleMixin, VaultMixin, Command` |

Pattern for Kayobe-only commands:

```python
class MyNewCommand(KayobeAnsibleMixin, VaultMixin, Command):
    """Short description of the command."""

    def get_parser(self, prog_name):
        parser = super(MyNewCommand, self).get_parser(prog_name)
        # Add command-specific arguments here if needed
        return parser

    def take_action(self, parsed_args):
        self.app.LOG.debug("Running my new command")
        playbooks = _build_playbook_list("my-new-playbook")
        self.run_kayobe_playbooks(parsed_args, playbooks,
                                  limit="target-group")
```

Pattern for commands that also invoke Kolla Ansible (inherit `KollaAnsibleMixin`):

```python
class MyNewKollaCommand(KollaAnsibleMixin, KayobeAnsibleMixin, VaultMixin, Command):
    """Short description of the command."""

    def get_parser(self, prog_name):
        parser = super(MyNewKollaCommand, self).get_parser(prog_name)
        return parser

    def take_action(self, parsed_args):
        self.app.LOG.debug("Running my new kolla command")
        self.handle_kolla_tags_limits_deprecation(parsed_args)
        playbooks = _build_playbook_list("my-new-playbook")
        self.run_kayobe_playbooks(parsed_args, playbooks)
        # Run kolla-ansible steps as needed, e.g.:
        # self.run_kolla_ansible_overcloud(parsed_args, "deploy")
```

`handle_kolla_tags_limits_deprecation(parsed_args)` **must** be called first in
every `KollaAnsibleMixin` command. It enforces warnings and mutual-exclusion
checks for `--kolla-limit`, `--kolla-tags`, and `--kolla-skip-tags`.

Key helpers:
- `_build_playbook_list("name1", "name2")` builds absolute paths to `ansible/<name>.yml`
- `_get_playbook_path("name")` returns a single playbook path
- Use `ignore_limit=True` for plays that must always run against all hosts (e.g. localhost config generation)
- Use `extra_vars={}` for runtime overrides
- Use `tags=` and `check=False` when needed

### 2. Register entry points in `setup.cfg`

Add **two** entries:

```ini
# Under [entry_points] > kayobe.cli=
my_new_command = kayobe.cli.commands:MyNewCommand

# Under kayobe.cli.my_new_command =
kayobe.cli.my_new_command =
    hooks = kayobe.cli.commands:HookDispatcher
```

The entry point name uses underscores and maps to the CLI as `kayobe my new command`.

### 3. Create the Ansible playbook

Create `ansible/my-new-playbook.yml` using kebab-case:

```yaml
---
- name: Description of what this play does
  hosts: target-group
  tags:
    - my-new-playbook
  roles:
    - role: my-role
```

Keep the playbook minimal. Put logic in a role under `ansible/roles/`.

### 4. Add a unit test in `kayobe/tests/unit/cli/test_commands.py`

```python
@mock.patch.object(commands.KayobeAnsibleMixin,
                   "run_kayobe_playbooks")
def test_my_new_command(self, mock_run):
    command = commands.MyNewCommand(TestApp(), [])
    parser = command.get_parser("test")
    parsed_args = parser.parse_args([])
    result = command.run(parsed_args)
    self.assertEqual(0, result)
    expected_calls = [
        mock.call(
            mock.ANY,
            [utils.get_data_files_path("ansible", "my-new-playbook.yml")],
            limit="target-group",
        ),
    ]
    self.assertListEqual(expected_calls, mock_run.call_args_list)
```

### 5. Add a release note

```bash
tox -e venv -- reno new add-my-new-command
```

Use the `features` section.

### 6. Update documentation

Add or update the relevant section in `doc/source/`.

### 7. Validate

```bash
tox -e py3    # unit tests pass
tox -e pep8   # style checks pass
```

## Checklist

- [ ] Command class in `kayobe/cli/commands.py` with correct mixins
- [ ] Two `setup.cfg` entry points (command + hook dispatcher)
- [ ] Ansible playbook in `ansible/` (kebab-case)
- [ ] Unit test in `kayobe/tests/unit/cli/test_commands.py`
- [ ] Release note via reno
- [ ] Documentation updated
- [ ] `tox -e py3` and `tox -e pep8` pass
