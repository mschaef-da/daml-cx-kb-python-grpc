# Copyright (c) 2025 Digital Asset (Switzerland) GmbH and/or its
# affiliates. All rights reserved.
#
# Copyright 2025 Digital Asset (Switzerland) GmbH and/or its affiliates
# SPDX-License-Identifier: BSD0

import sys

from .ledger import LedgerConnection
from .config import Config, load_config

from .commands import (
    init_context,
    cmd_allocate_party,
    cmd_archive_asset,
    cmd_give_asset,
    cmd_issue_asset,
    cmd_ledger_end,
    cmd_list_contracts,
    cmd_list_local_parties,
    cmd_list_packages,
    cmd_list_parties,
    cmd_list_updates,
    cmd_stream_updates,
    cmd_version,
)


def cmd_repeatedly(ctx, count, *args):
    for _ in range(0, int(count)):
        do_command(ctx, args)


COMMAND_HANDLERS = {
    "allocate-party": cmd_allocate_party,
    "archive-asset": cmd_archive_asset,
    "give-asset": cmd_give_asset,
    "issue-asset": cmd_issue_asset,
    "ledger-end": cmd_ledger_end,
    "list-contracts": cmd_list_contracts,
    "list-local-parties": cmd_list_local_parties,
    "list-packages": cmd_list_packages,
    "list-parties": cmd_list_parties,
    "list-updates": cmd_list_updates,
    "repeatedly": cmd_repeatedly,
    "stream-updates": cmd_stream_updates,
    "version": cmd_version,
}


def cmd_help(ledger, *_):
    print("Available subcommands:")
    for cmd in list(COMMAND_HANDLERS.keys()):
        print("  ", cmd)


def do_command(ctx, args):
    command = args[0] if len(args) > 0 else "help"
    COMMAND_HANDLERS.get(command, cmd_help)(ctx, *args[1:])


def main():
    config = load_config()

    with LedgerConnection(config.ledgerAddress) as ledger:
        ctx = init_context(config, ledger)

        do_command(ctx, sys.argv[1:])
