#!/usr/bin/env bash

set -eou pipefail

source "$(dirname "$0")/libcli.source"

project_daml_yaml="$1"
completion_file="$2"
target_directory="$3"
if [ -z "$project_daml_yaml" ] || [ -z "$completion_file" ]; then
    _error "Usage - $0 <path to versions yaml> <path to .protobufs>"
fi

function yaml_value() {
  local path=$1
  yq -re "$path" "$project_daml_yaml" 2>/dev/null
}

if ! protobuf_url=$(yaml_value '.["protobuf-url"]'); then
  _error "Cannot read protobuf-url from $project_daml_yaml"
fi

if ! protobuf_filename=$(yaml_value '.["protobuf-filename"]'); then
  _error "Cannot read protobuf-filename from $project_daml_yaml"
fi

_info "== Downloading protobuf models ${protobuf_filename}
from: ${protobuf_url}
to: ${target_directory}"

mkdir -p "${target_directory}"

curl --fail -L "${protobuf_url}/${protobuf_filename}" -o "${target_directory}/${protobuf_filename}"

echo "${protobuf_filename}" > "$completion_file"

_info "== Downloaded protobuf models."
