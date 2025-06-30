#!/usr/bin/env bash
# Copyright 2025 Digital Asset (Switzerland) GmbH and/or its affiliates
# SPDX-License-Identifier: BSD0


set -eou pipefail

source "$(dirname "$0")/libcli.source"

versions_yaml="$1"
output="$2"
if [ -z "$versions_yaml" ] || [ -z "$output" ]; then
    _error "Usage - $0 <path to versions yaml> <path to .protobufs>"
fi

function yaml_value() {
  local path=$1
  yq -re "$path" "$versions_yaml" 2>/dev/null
}

if ! daml_version=$(yaml_value '.["sdk-version"]'); then
  _error "Cannot read Daml SDK version from $versions_yaml"
fi
if ! daml_tag=$(yaml_value '.["sdk-tag"]'); then
  _error "Cannot read Daml SDK tag from $versions_yaml"
fi

protobufs="protobufs-$daml_tag.zip"
url="https://github.com/digital-asset/daml/releases/download/v$daml_version/$protobufs"

mkdir -p target

_info "== Downloading protobuf models $daml_version
from: $url
to: target/$protobufs"

curl --fail -L "$url" -o "target/$protobufs"

echo "$daml_tag" > "$output"

_info "== Downloaded protobuf models."
