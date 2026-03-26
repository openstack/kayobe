---
name: sync-kolla-inventory
description: "Synchronise Kayobe overcloud inventory templates with Kolla Ansible multinode inventory. Use when: updating for a new OpenStack/Kolla release, copying inventory group changes from kolla-ansible, and validating top-level/components/services split in Kayobe templates."
---

# Sync Kolla Inventory

## When to Use

- Preparing Kayobe for a new Kolla Ansible release
- Syncing inventory changes from kolla-ansible multinode inventory
- Verifying new/removed inventory groups are reflected in the correct Kayobe
  template

Last validated for `2026.1`.

## Source and Targets

- Source inventory in kolla-ansible:
  - `ansible/inventory/multinode`
- Kayobe targets:
  - `ansible/roles/kolla-ansible/templates/overcloud-top-level.j2`
  - `ansible/roles/kolla-ansible/templates/overcloud-components.j2`
  - `ansible/roles/kolla-ansible/templates/overcloud-services.j2`

Kayobe splits multinode inventory into three parts.

## Boundary Rules

### Top level

Target: `ansible/roles/kolla-ansible/templates/overcloud-top-level.j2`

- This file is heavily templated and does not typically need changes.
- Look for changes in multinode before the `[baremetal]` group.
- If there are changes in that region, port them carefully while preserving
  existing Kayobe templating.

### Components

Target: `ansible/roles/kolla-ansible/templates/overcloud-components.j2`

- Includes multinode groups from `[baremetal]` down to this marker:

```text
# Additional control implemented here. These groups allow you to control which
# services run on which hosts at a per-service level.
```

- This file maps components to top-level groups.

### Services

Target: `ansible/roles/kolla-ansible/templates/overcloud-services.j2`

- Includes multinode groups from the marker above to end of file.
- This file maps service containers to components.
- Keep Kayobe-specific small changes in this section unless intentionally
  removed.

## Procedure

### 1. Get the source inventory snapshot

Prompt for the target `<release>` (for example `2026.1`), then ensure the
kolla-ansible checkout exists under `${KAYOBE_AGENT_WORKDIR}` in
`kolla-ansible/`.

Before cloning or reusing the checkout, source `.agents/scripts/agent-environment.sh` to set
`KAYOBE_AGENT_WORKDIR`.

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

### 2. Compare multinode against Kayobe split templates

Review group additions/removals/renames in the source and map each change by
section boundary:

- Before `[baremetal]` -> `overcloud-top-level.j2`
- `[baremetal]` to marker -> `overcloud-components.j2`
- Marker to end -> `overcloud-services.j2`

### 3. Apply updates to the correct Kayobe template

Port each relevant change into the appropriate file while preserving existing
Kayobe templating and comments.

### 4. Validate new services are placed correctly

When new services appear in multinode:

- Add top-level component groups to `overcloud-components.j2` when appropriate.
- Add per-service container groups to `overcloud-services.j2`.
- Sub-services/exporters of an existing component generally belong in
  `overcloud-services.j2` only.

### 5. Re-check Kayobe-specific behavior

After sync, confirm intentional Kayobe differences are still present and valid,
particularly in `overcloud-services.j2`.

## Checklist

- [ ] Prompted for target `<release>`
- [ ] Ensured `kolla-ansible/` exists in repo root on `stable/<release>`
- [ ] Confirmed `kolla-ansible/` has no uncommitted changes before checkout
- [ ] Aborted all sync checks if `kolla-ansible/` was dirty
- [ ] Compared kolla-ansible `ansible/inventory/multinode` with Kayobe templates
- [ ] Reviewed pre-`[baremetal]` changes for `overcloud-top-level.j2`
- [ ] Synced component groups into `overcloud-components.j2`
- [ ] Synced service groups into `overcloud-services.j2`
- [ ] Verified new services are in the correct file(s)
- [ ] Preserved intentional Kayobe-specific service-section changes
