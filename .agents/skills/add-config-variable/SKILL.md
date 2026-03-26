---
name: add-config-variable
description: "Add a new Kayobe configuration variable with proper inventory defaults, operator examples, and docs. Use when: adding a config knob, introducing a new setting, creating a new component config file. Touches group_vars, etc/kayobe, and doc/source."
---

# Add a Kayobe Configuration Variable

## When to Use

- Adding a new user-configurable setting
- Introducing a variable for a new or existing component
- Renaming or restructuring existing configuration

## Procedure

### 1. Add the inventory default

Add the variable to the appropriate file under `ansible/inventory/group_vars/`.

- Global defaults go in `ansible/inventory/group_vars/all/<component>` (extensionless file).
- Group-specific defaults go in `ansible/inventory/group_vars/<group>/<component>`.

**For scalar variables:**

```yaml
# Description of what this variable controls. Default is <value>.
my_component_setting: "default_value"
```

**For list variables, use the three-tier pattern:**

```yaml
# Combined list of items (do not override directly).
my_component_items: >
  {{ my_component_items_default +
     my_component_items_extra }}

# List of default items.
my_component_items_default:
  - item1
  - item2

# List of extra items added by the operator.
my_component_items_extra: []
```

This lets operators extend defaults via `_extra` without replacing the whole list.

### 2. Add the commented example in `etc/kayobe/`

**Only do this for variables that operators are expected to override directly.**
Skip this step for internal defaults — those should remain inventory-only.

Add a commented-out version in the appropriate `etc/kayobe/` file:

```yaml
# Description of what this variable controls. Default is <value>.
#my_component_setting:
```

For three-tier lists, document all three variables:

```yaml
# Combined list of items.
#my_component_items:

# List of default items.
#my_component_items_default:

# List of extra items added by the operator.
#my_component_items_extra:
```

Rules:
- Keep the same comment text as the inventory default (adjusted for operator audience).
- Preserve the `###` section dividers and comment style used in the rest of the file.
- The file name in `etc/kayobe/` should follow the file alignment reference.

### 3. Update documentation

Add or update the variable description in the existing authoritative doc page
for the component. Search `doc/source/` to find the right file — do not assume
a filename from the component name. For example:

- Kolla-ansible settings → `doc/source/configuration/reference/kolla-ansible.rst`
- Kolla settings → `kolla.rst`
- OpenStack/kayobe settings → `doc/source/configuration/reference/kayobe.rst`
- Host-group settings (firewall, sysctl, etc.) → `doc/source/configuration/reference/hosts.rst`
- IPA → `doc/source/configuration/reference/ironic-python-agent.rst`

When in doubt, `grep -r 'nearby_variable_name' doc/source/` to locate the right page.

### 4. Add a release note

```bash
tox -e venv -- reno new add-my-component-setting
```

Use the `features` section for new variables, `upgrade` if existing behavior changes.

### 5. Validate

```bash
tox -e pep8           # yamllint checks etc/kayobe/
tox -e ansible-lint   # lint the inventory and playbooks
```

## File Alignment Reference

| Inventory defaults | Operator examples | Docs |
|---|---|---|
| `ansible/inventory/group_vars/all/<component>` | `etc/kayobe/<component>.yml` | Find by searching `doc/source/` |
| `ansible/inventory/group_vars/<group>/<component>` | `etc/kayobe/<group>.yml` | Same docs file |

Note: for group-scoped variables the `etc/kayobe/` file is named after the
**group** (e.g. `compute`, `controllers`), not the component file inside
that group. For example `ansible/inventory/group_vars/compute/firewall`
corresponds to `etc/kayobe/compute.yml`.

## Naming Conventions

- Prefix variables with the component name: `kolla_`, `compute_`, `seed_`, `dns_`, etc.
- Use `snake_case` for all variable names.
- Use `_default` and `_extra` suffixes for the three-tier list pattern.
- Use `_enabled` (bool) for feature toggles.

## Checklist

- [ ] Variable added in `ansible/inventory/group_vars/` with comment and default value
- [ ] Commented example added in `etc/kayobe/<component>.yml`
- [ ] Documentation updated in `doc/source/`
- [ ] Release note via reno
- [ ] `tox -e pep8` passes (yamllint)
- [ ] `tox -e ansible-lint` passes (if touching playbooks or roles)
