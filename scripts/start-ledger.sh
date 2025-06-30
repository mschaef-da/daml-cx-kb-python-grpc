#!/usr/bin/env bash
# Copyright 2025 Digital Asset (Switzerland) GmbH and/or its affiliates
# SPDX-License-Identifier: BSD0

set -euo pipefail

source "$(dirname "$0")/libcli.source"

dar_opts=""

for dar_file in "$@"
do
    if [ ! -f ${dar_file} ]; then
        _error "DAR file ${dar_file} not found."
    fi

    dar_opts="${dar_opts} --dar ${dar_file}"
done

mkdir -pv log
mkdir -pv target

pid_file="target/canton.pid"
if [ -f "$pid_file" ]; then
    pid=$(<"$pid_file")

    if ps -p $pid > /dev/null; then
        _info "Ledger already running. (PID: $pid)"
        exit 0
    else
        _warning "Stale PID file found, but process not running. Cleaning up $pid_file and starting ledger."
        rm "$pid_file"
    fi
fi

daml sandbox --debug \
     ${dar_opts} \
     --json-api-port 8089 \
     &> log/canton-console.log &
echo $! > "$pid_file"

pid=$(<"$pid_file")

_info "Started Canton ledger (PID: $pid) with log output in log/"

_info "Waiting 30 seconds for startup..."

sleep 30

_info "...Ledger running"
