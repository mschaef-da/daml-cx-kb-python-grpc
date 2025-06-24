#!/usr/bin/env bash

# Copied & adapted from the `canton-network-node` repo

# A script to install the snapshot releases of the Daml SDK that we use in this repo.

cd "$REPO_ROOT"

source "$(dirname "$0")/libcli.source"

project_daml_yaml="$1"
completion_file="$2"
if [ -z "$project_daml_yaml" ] || [ -z "$completion_file" ]; then
    _error "Usage - $0 <path to versions yaml> <path to .damlsdk>"
fi

set -eou pipefail

function yaml_value() {
  local path=$1
  yq -re "$path" "$project_daml_yaml" #2>/dev/null
}

if ! daml_version=$(yaml_value '.["sdk-version"]'); then
  _error "Cannot read Daml SDK version from $project_daml_yaml"
fi


function complete_installation() {
  echo "$daml_version" > "$completion_file"
  _info "== Installation complete. (version: $daml_version)"
  exit 0
}

if command -v daml > /dev/null 2>&1 && daml version | grep --quiet "$daml_version"; then
  _info "== Daml SDK $daml_version is installed."
  complete_installation
fi

# Install the SDK version and mark the installation as complete
daml install "$daml_version"


complete_installation
