# AGENTS.md

Guidance for coding agents working in this repository.

## Scope

These instructions apply to the whole repository.

## Repository Overview

Kayobe is an OpenStack project for deploying containerised OpenStack to bare metal. The repository combines:

- Python application code in `kayobe/`
- Ansible playbooks, plugins, and inventory defaults in `ansible/`
- Ansible roles used by Kayobe in `ansible/roles/`
- Top-level CI-oriented roles in `roles/`, used by Zuul jobs
- Example operator configuration in `etc/kayobe/`
- Documentation in `doc/source/`

When changing behavior, prefer to preserve the existing split between code, default inventory values, and operator-facing example configuration.

## Core Conventions

### Python

- Follow PEP 8 style for Python, along with the OpenStack Style Commandments referenced in `HACKING.rst`.
- Use the existing Apache 2.0 file header for new Python files.
- Keep imports grouped as standard library, third-party, then local imports.
- Use module-level logging with `LOG = logging.getLogger(__name__)`.
- Raise project exceptions from `kayobe.exception.KayobeException` or a specific subclass.
- Follow existing Cliff command patterns in `kayobe/cli/commands.py`:
  - mixins provide shared parser and execution behavior
  - command classes implement `get_parser()` and `take_action()` or `run()` consistently with nearby code
  - CLI naming is driven by `setup.cfg` entry points

### Ansible

- Keep top-level playbooks in `ansible/` minimal. Put reusable logic in roles.
- Use kebab-case names for playbooks in `ansible/`.
- Preserve the current YAML style and comment formatting in inventory defaults and example config.
- Custom Ansible plugins live in `ansible/action_plugins/`, `ansible/filter_plugins/`, `ansible/lookup_plugins/`, and `ansible/test_plugins/`.
- For **filter and lookup plugins**, implementations live in `kayobe/plugins/` with thin re-export wrappers in the `ansible/*_plugins/` directories. Put new filter/lookup logic in `kayobe/plugins/` and add a wrapper under `ansible/*_plugins/` if following this pattern.
- For **action plugins**, implementations are typically full standalone modules directly in `ansible/action_plugins/` with no counterpart in `kayobe/plugins/`. Follow the nearest existing plugin of the same kind.
- Roles use standard Ansible layout such as `defaults/main.yml`, `tasks/main.yml`, and `vars/main.yml`.
- Put roles used by Kayobe playbooks under `ansible/roles/`.
- Treat the top-level `roles/` directory as Zuul/CI-focused content rather than the main home for Kayobe runtime roles.
- For list-type variables, follow the three-tier composition pattern where applicable: `<var>_default` + `<var>_extra` combined into `<var>`. This lets operators extend defaults without replacing them.

### Inventory Defaults And Example Config

- Inventory defaults in `ansible/inventory/group_vars/` are commonly stored in extensionless files, for example `ansible/inventory/group_vars/all/kolla`.
- Operator-facing example configuration lives in `etc/kayobe/*.yml` and typically contains commented-out variables with explanatory text.
- If you add or rename a variable in `ansible/inventory/group_vars/<group>/<file>` or `ansible/inventory/group_vars/all/<file>`, also add or update the corresponding commented example in `etc/kayobe/<file>.yml` when that file represents the same component.
- The component file name should usually stay aligned across these locations, for example inventory defaults in `.../kolla` and example configuration in `etc/kayobe/kolla.yml`.
- Keep user-overridable values documented in `etc/kayobe/` rather than only discoverable from inventory defaults.

### Testing

- Unit tests live in `kayobe/tests/unit/`, mirroring the module structure.
- Use `unittest.TestCase` with `self.maxDiff = None`.
- Mock external calls with `@mock.patch.object(..., autospec=True)`.
- CLI command tests instantiate the command class with a test app, parse arguments, call `run()`, and assert the expected playbook calls via `mock_run.call_args_list`.
- Molecule tests for roles live in `ansible/roles/<role>/molecule/` and use testinfra for verification.
- Shared molecule helpers are in `kayobe/tests/molecule/utils.py`.

### Documentation

- Update documentation when behavior, configuration, or workflows change.
- For any non-trivial change, add or update the relevant documentation in `doc/source/`.
- Prefer `doc/source/` for contributor or user-facing changes, and keep wording consistent with the existing docs.

### Commit Messages

- Use the 50/72 rule: subject line ≤ 50 characters, body lines wrapped at 72 characters.
- Write the subject in the imperative mood (e.g. "Fix broken conditional" not "Fixed broken conditional").
- Separate the subject from the body with a blank line.
- Use the body to explain *what* and *why*, not *how*.
- A `Change-Id` trailer is added automatically by a git hook. Always preserve it when amending a commit.
- Reference bugs with a `Closes-Bug: #<id>` trailer (Launchpad) or `Related-Bug: #<id>` if the commit does not fully fix the bug.

### Release Notes

- Kayobe uses `reno` for release notes, stored in `releasenotes/notes/`.
- Default to adding a release note for code, behavior, configuration, and other user-visible changes.
- Docs-only, CI-only, and `TrivialFix` changes generally should not add a release note.
- Create new release notes with `tox -e venv -- reno new <summary-line-with-dashes>`.
- Use an appropriate section such as `features`, `fixes`, `upgrade`, or `deprecations`, following the templates in `releasenotes/templates/`.

## Validation

Use the narrowest relevant validation for the change you make.
Follow the validation workflow defined in `tox.ini`, and treat issues reported by the tools run via `tox` as authoritative for the checks they perform.

- Python tests: `tox -e py3`
- Python style, lint, and static checks: `tox -e pep8`
- Ansible checks: `tox -e ansible-lint`
- Ansible syntax checks: `tox -e ansible-syntax`
- Role/integration checks: `tox -e molecule`

If a change touches Ansible inventory defaults or example config, at minimum run the relevant lint or syntax validation when feasible.
For Python changes, run `tox -e pep8` as a mandatory local style check when the environment permits running repository validation.

## Working Rules For Agents

- Do not modify any files not tracked by git unless explicitly instructed to or when creating a new file.
- When skills need temporary files or external checkouts, always source `source .agents/scripts/agent-environment.sh` before running shell commands.
- `KAYOBE_AGENT_WORKDIR` is set by `.agents/scripts/agent-environment.sh` and defaults to `.agents/workdir/` under the Kayobe checkout root.
- Override it by setting `KAYOBE_AGENT_WORKDIR` explicitly.
- Read nearby files before making structural changes; patterns in this repo are deliberate and often repeated.
- If repository tooling does not fully determine style or structure, follow nearby files and existing project patterns.
- Prefer focused changes over refactors.
- Do not remove comments from `etc/kayobe/*.yml` unless they are being replaced with better operator guidance.
- Do not put secrets or site-specific values into repository defaults.
- Respect existing user changes in the worktree and avoid reverting unrelated files.
- When adding new configuration knobs, check all three places as applicable:
  - inventory defaults in `ansible/inventory/group_vars/`
  - operator example config in `etc/kayobe/`
  - documentation in `doc/source/`

## Useful References

- `README.rst`
- `HACKING.rst`
- `CONTRIBUTING.rst`
- `setup.cfg`
- `tox.ini`
- `kayobe/cli/commands.py`
- `ansible/inventory/group_vars/all/`
- `etc/kayobe/`
