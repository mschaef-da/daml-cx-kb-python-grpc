# Copyright (c) 2025 Digital Asset (Switzerland) GmbH and/or its
# affiliates. All rights reserved.
#
# Copyright 2025 Digital Asset (Switzerland) GmbH and/or its affiliates
# SPDX-License-Identifier: BSD0

import decimal
import grpc
import pprint
import sys
import time
import jwt
import base64
import json

from dataclasses import dataclass

from .util import FAIL, to_boolean

from .ledger import create_contract, exercise_contract_choice
from .value import Package, party

ASSET_MODEL = Package("#asset-model")

ASSET_ID = ASSET_MODEL.id("Main", "Asset")

#### Top level context


@dataclass(frozen=True)
class Context:
    config: "Config"
    ledger: "LedgerConnection"

    def lookup_local_party_id(self, party_name):
        party = self.ledger.lookup_local_party_id(party_name)

        if party is None:
            FAIL(f"No party found for basename: {party_name}")
        else:
            return party


def init_context(config: "Config", ledger: "LedgerConnection") -> "Context":
    return Context(
        config=config,
        ledger=ledger,
    )


#### Commands


def format_cid(cid):
    if len(cid) > 16:
        return f"{cid[:8]}...{cid[-8:]}"
    else:
        return cid


def format_tid(tid):
    return f'{tid["module_name"]}:{tid["entity_name"]}'


def show_output(txns):
    if isinstance(txns, list):
        for txn in txns:
            pprint.pprint(txn)
        print("n=", len(txns))
    else:
        show_output([txns])


def pprint_indented(v, width=80):
    string = pprint.pformat(v, width=width)

    for line in string.splitlines():
        print("      ", line)


def show_tx_events(txn):
    if txn is None:
        print("None")
    else:
        for evt in txn["events"]:
            event = evt["event"]

            print(
                "  === EVENT: ",
                event,
                format_tid(evt["template_id"]),
                evt["contract_id"],
            )
            if event == "created":
                pprint_indented(evt["create_arguments"])
                print()


### Diagnostic Commands


def cmd_version(ctx):
    print(ctx.ledger.get_ledger_version())

def cmd_ledger_end(ctx):
    print(ctx.ledger.get_ledger_end())

def cmd_list_contracts(ctx, party_name):
    party = ctx.lookup_local_party_id(party_name)

    show_output(ctx.ledger.get_active_contracts(party))


def show_transaction_stream(s, *, show_tx_fn=show_tx_events):
    for tx in s:
        print(
            f"===== Transaction ofs: {tx['offset']}, command_id: {tx['command_id']}, wfid: {tx['workflow_id']}"
        )
        show_tx_fn(tx)
        print()


def cmd_list_updates(ctx, party_name):
    party = ctx.lookup_local_party_id(party_name)

    show_transaction_stream(ctx.ledger.get_updates(party))


def cmd_stream_updates(ctx, party_name):
    party = ctx.lookup_local_party_id(party_name)

    show_transaction_stream(ctx.ledger.get_update_stream(party))


def cmd_allocate_party(ctx, base_name):
    existing_party = ctx.ledger.lookup_local_party_id(base_name)

    if existing_party is not None:
        return existing_party

    resp = ctx.ledger.allocate_party(base_name)

    show_output(resp)
    return resp.party_details.party


def cmd_list_parties(ctx):
    show_output(ctx.ledger.get_ledger_parties())


def cmd_list_packages(ctx):
    show_output(ctx.ledger.get_ledger_packages())

def cmd_list_local_parties(ctx):
    show_output(ctx.ledger.get_ledger_local_parties())

def cmd_issue_asset(ctx, issuer, name):
    issuer_party = ctx.ledger.lookup_local_party_id(issuer)

    return ctx.ledger.submit(
        issuer_party,
        create_contract(
            ASSET_ID,
            {
                "issuer": party(issuer_party),
                "owner": party(issuer_party),
                "name": name
            }
        ),
    )

def cmd_give_asset(ctx, asset_cid, owner, new_owner):
    owner_party = ctx.ledger.lookup_local_party_id(owner)
    new_owner_party = ctx.ledger.lookup_local_party_id(new_owner)

    return ctx.ledger.submit(
        owner_party,
        exercise_contract_choice(
            ASSET_ID,
            asset_cid,
            "Give",
            {
                "newOwner": party(new_owner_party)
            }
        ),
    )

def cmd_archive_asset(ctx, asset_cid, issuer):
    issuer_party = ctx.ledger.lookup_local_party_id(issuer)

    return ctx.ledger.submit(
        issuer_party,
        exercise_contract_choice(
            ASSET_ID,
            asset_cid,
            "Archive",
            {
            }
        ),
    )



