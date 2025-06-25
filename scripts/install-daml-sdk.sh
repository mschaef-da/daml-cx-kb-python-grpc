#!/usr/bin/env bash

# A script to install the snapshot releases of the Daml SDK that we use in this repo.

source "$(dirname "$0")/libcli.source"

versions_yaml="$1"
completion_file="$2"
if [ -z "$versions_yaml" ] || [ -z "$completion_file" ]; then
    _error "Usage - $0 <path to versions yaml> <path to .damlsdk>"
fi

set -eou pipefail

artifactory="https://digitalasset.jfrog.io/artifactory"

function yaml_value() {
  local path=$1
  yq -re "$path" "$versions_yaml" 2>/dev/null
}

if ! daml_version=$(yaml_value '.["sdk-version"]'); then
  _error "Cannot read Daml SDK version from $versions_yaml"
fi

if ! daml_sdk_tag=$(yaml_value '.["sdk-tag"]'); then
    _error "Cannot read Daml SDK tag from $versions_yaml"
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

# Determine the operating system
if [[ "$(uname -s)" == "Linux" ]]; then
    os="linux"
elif [[ "$(uname -s)" == "Darwin" ]]; then
    os="macos"
else
    _error "OS not supported for development in this repo."
fi

if [[ "$daml_version" =~ .*"snapshot".* ]]; then
    os="$os-x86_64"
fi

url="$artifactory/sdk-ee/$daml_sdk_tag/daml-sdk-$daml_sdk_tag-$os-ee.tar.gz"

# Download tarball at URL to a temporary directory
tmp_dir=$(mktemp -d)
tarball="$tmp_dir/daml-sdk.tar.gz"

_info "== Downloading Daml SDK $daml_version (tag: $daml_sdk_tag) for $os
from: $url
to: $tarball"

curl --fail -u "$ARTIFACTORY_READONLY_USER:$ARTIFACTORY_READONLY_PASSWORD" \
     -L "$url" \
     -o "$tarball"

# Install the Daml SDK
_info "== Installing Daml SDK version: $daml_version"
tar -xf "$tarball" -C "$tmp_dir"

"$tmp_dir/sdk-$daml_sdk_tag/install.sh" --install-assistant yes

# Cleanup temp dir
rm -rf "$tmp_dir"

# Mark the installation as complete

complete_installation
