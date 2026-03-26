---
name: sync-kolla-feature-flags
description: "Synchronise Kayobe Kolla feature flags with a target kolla-ansible tree. Use when: updating for a new OpenStack/Kolla release, refreshing kolla_feature_flags, regenerating etc/kayobe kolla_enable_* examples, and checking removed services in overcloud image regex maps."
---

# Sync Kolla Feature Flags

## When to Use

- Preparing Kayobe for a new Kolla Ansible release
- Refreshing the canonical `kolla_feature_flags` list
- Regenerating the `kolla_enable_*` commented flags in `etc/kayobe/kolla.yml`
- Verifying removed services are not left behind in inventory defaults

Last validated for `2026.1`.

## Procedure

### 1. Generate the canonical flag list from Kolla Ansible

Prompt for the target `<release>` (for example `2026.1`), then ensure the
kolla-ansible checkout exists under `${KAYOBE_AGENT_WORKDIR}` in
`kolla-ansible/`.

Before cloning or reusing the checkout, source `.agents/scripts/agent-environment.sh` to
set `KAYOBE_AGENT_WORKDIR`.

If `kolla-ansible/` does not exist, clone with:

```bash
source .agents/scripts/agent-environment.sh
git clone https://github.com/openstack/kolla-ansible -b stable/<release> "${KAYOBE_AGENT_WORKDIR}/kolla-ansible"
```

If `kolla-ansible/` already exists, checkout the correct branch:

```bash
source .agents/scripts/agent-environment.sh
git -C "${KAYOBE_AGENT_WORKDIR}/kolla-ansible" status --porcelain
```

If this command returns any output, stop and ask the user to clean, commit, or
stash changes before continuing. Abort all sync checks until the checkout is
clean.

Then run:

```bash
source .agents/scripts/agent-environment.sh
git -C "${KAYOBE_AGENT_WORKDIR}/kolla-ansible" fetch origin
git -C "${KAYOBE_AGENT_WORKDIR}/kolla-ansible" checkout stable/<release>
git -C "${KAYOBE_AGENT_WORKDIR}/kolla-ansible" pull --ff-only origin stable/<release>
```

Then run:

```bash
source .agents/scripts/agent-environment.sh
tools/kolla-feature-flags.sh "${KAYOBE_AGENT_WORKDIR}/kolla-ansible"
```

The script output is the canonical sorted list for
`ansible/roles/kolla-ansible/vars/main.yml`.

### 2. Update `kolla_feature_flags`

Replace the `kolla_feature_flags` list in
`ansible/roles/kolla-ansible/vars/main.yml` with the script output from step 1.

### 3. Regenerate `kolla_enable_*` examples

Run:

```bash
tools/feature-flags.py
```

Copy the script output and replace the `kolla_enable_*` commented flag block in
`etc/kayobe/kolla.yml`.

### 4. Apply repository guardrails learned from prior syncs

After syncing, verify that removed services are consistently absent from all
Kayobe-owned locations. Run `git grep <service>` to find any stragglers.

#### `ansible/inventory/group_vars/all/kolla`

- No removed-service entries in `overcloud_container_image_regex_map`.
- No removed-service `kolla_enable_*` defaults.
- No stale dependencies on a removed service (e.g. `kolla_enable_placement`
  previously depended on `kolla_enable_zun`; remove such references).

#### `etc/kayobe/kolla.yml`

- No commented `#kolla_enable_<service>:` or `#kolla_enable_horizon_<service>:`
  entries for removed services.

#### `ansible/roles/kolla-openstack/defaults/main.yml`

- No removed-service include globs in
  `kolla_openstack_custom_config_include_globs_default`.
- No removed-service template override rules in
  `kolla_openstack_custom_config_rules_default`.
- No `kolla_enable_<service>` default variable block for removed services.

#### `doc/source/configuration/reference/kolla-ansible.rst`

- No removed-service rows in the custom config path table.

#### `ansible/roles/kolla-ansible/defaults/main.yml`

- No commented `#kolla_enable_<service>:` entries for removed services.

#### `ansible/roles/kolla-ansible/templates/kolla/globals.yml`

- No commented or active removed-service-specific globals
  (e.g. `#docker_configure_for_zun`).

#### `ansible/roles/kolla-ansible/templates/overcloud-components.j2`

- No `[<service>:children]` group entries for removed services.
- New top-level services (not sub-exporters/sub-services of an existing
  component) need a `[<service>:children]` entry here. Check the kolla-ansible
  source inventory for guidance on whether a new flag warrants a component
  group.

#### `ansible/roles/kolla-ansible/templates/overcloud-services.j2`

- No `[<service>-*:children]` group entries or `<service>` child group
  references for removed services.
- New services need appropriate `[<service>-*:children]` entries here. Each
  container defined by kolla-ansible for the service typically needs one.
  Sub-exporters/sub-services of an existing component (e.g.
  `prometheus-openstack-network-exporter`, `prometheus-valkey-exporter`) go
  here only, not in `overcloud-components.j2`.

#### `ansible/container-engine.yml`

- No playbook vars that reference removed-service feature flags
  (e.g. `docker_configure_for_zun: "{{ kolla_enable_zun | bool }}"`).

#### `ansible/roles/kolla-ansible/tests/test-extras.yml`

- No `kolla_enable_<service>: True` entries in the "enable everything" block.
- No `#enable_<service>: True` entries in the commented expected-variables
  block.

Known removed-service examples include: `influxdb`, `kuryr`, `telegraf`, `zun`.

### 5. Optional template sanity check

A prior scan found no removable removed-service-specific files under:

- `ansible/roles/kolla-openstack/templates/kolla/config`

Use this as a reference point when deciding whether template deletions are
needed during future syncs.

## Checklist

- [ ] Prompted for target `<release>`
- [ ] Ensured `kolla-ansible/` exists in repo root on `stable/<release>`
- [ ] Confirmed `kolla-ansible/` has no uncommitted changes before checkout
- [ ] Aborted all sync checks if `kolla-ansible/` was dirty
- [ ] Ran `tools/kolla-feature-flags.sh <path to kolla-ansible source>`
- [ ] Updated `ansible/roles/kolla-ansible/vars/main.yml`
- [ ] Ran `tools/feature-flags.py`
- [ ] Updated `etc/kayobe/kolla.yml` `kolla_enable_*` block
- [ ] Confirmed removed services absent from `ansible/inventory/group_vars/all/kolla`
- [ ] Confirmed removed services absent from `ansible/roles/kolla-ansible/defaults/main.yml`
- [ ] Confirmed removed services absent from `ansible/roles/kolla-ansible/templates/kolla/globals.yml`
- [ ] Confirmed removed services absent from `ansible/roles/kolla-ansible/templates/overcloud-components.j2`
- [ ] Confirmed removed services absent from `ansible/roles/kolla-ansible/templates/overcloud-services.j2`
- [ ] Confirmed removed services absent from `ansible/container-engine.yml`
- [ ] Confirmed removed services absent from `ansible/roles/kolla-ansible/tests/test-extras.yml`
- [ ] Confirmed removed services absent from `ansible/roles/kolla-openstack/defaults/main.yml`
- [ ] Confirmed removed services absent from `doc/source/configuration/reference/kolla-ansible.rst`
