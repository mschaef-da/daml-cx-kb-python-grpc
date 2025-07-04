#!/usr/bin/env bash
# Copyright 2025 Digital Asset (Switzerland) GmbH and/or its affiliates
# SPDX-License-Identifier: BSD0

set -euo pipefail

source "$(dirname "$0")/libcli.source"

pid_file="target/canton.pid"
if [ -f "$pid_file" ]; then
    pid=$(<"$pid_file")

    if ps -p $pid > /dev/null; then
        _info "Killing ledger running. (PID: $pid)"
        kill "$pid"
        rm "$pid_file"
    else
        _warning "Stale PID file found, but process not running. Cleaning up $pid_file."
        rm "$pid_file"
    fi
else
    _warning "$pid_file not found, ledger assumed not running."
fi
