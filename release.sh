#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
export SCRIPT_DIR

function release_custom_hook {
    # shellcheck disable=SC2154
    echo "Running custom hook for ${version_tag}"

    msg="# managed by release.sh"
    # NOTE: this invalidates the docker cache for each new release.
    sed -E -i "s/^version = .* $msg$/version = \"${version_tag#v}\"  $msg/" "./pyproject.toml"
    uv sync
    git add ./pyproject.toml ./uv.lock

    sed -E -i "s/^version: .* $msg$/version: ${version_tag#v}-SET-BY-CICD  $msg/" "./deploy/helm/Chart.yaml"
    git add ./deploy/helm/Chart.yaml
}

export -f release_custom_hook
# Last commit covered by the hand-written CHANGELOG-legacy.md.
export START_COMMIT="86b9ddd33c5a1315bda84050dc21529c7c3613ba"
export RELEASE_CUSTOM_HOOK=release_custom_hook
export REPO_NAME=IFRCGo/go-api
export DEFAULT_BRANCH=develop
export VERSION_TAG_PREFIX_MODE=require

export GIT_CLIFF__REMOTE__GITHUB__OWNER=IFRCGo
export GIT_CLIFF__REMOTE__GITHUB__REPO=go-api

# Overrides the footer from fugit/configs/cliff.toml
# to link the hand-written changelog that predates release.sh.
export GIT_CLIFF__CHANGELOG__FOOTER='
## Older releases

For changes before the git-cliff generated changelog (releases up to `1.1.509` and its "Unreleased" section), see [CHANGELOG-legacy.md](./CHANGELOG-legacy.md).
'

# Forward the argument - used for pre-fill version
"$SCRIPT_DIR/fugit/scripts/release.sh" "${@:-}"
