#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
export SCRIPT_DIR

# fugit lives at the repo root; this chart is nested under deploy/helm/.
# shellcheck disable=SC2068
"$SCRIPT_DIR/../../fugit/scripts/helm-update-snapshots.sh" "$@"
