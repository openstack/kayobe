#!/bin/bash

oldstate=$(set +o)

set -eu
set -o pipefail

# Resolve the Kayobe checkout root and set the default agent workdir beneath it.

PARENT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENTS_ROOT="$(dirname "${PARENT}")"
REPO_ROOT="$(dirname "${AGENTS_ROOT}")"

export KAYOBE_AGENT_WORKDIR="${KAYOBE_AGENT_WORKDIR:-${REPO_ROOT}/.agents/workdir}"

eval "$oldstate"
