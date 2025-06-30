# Copyright (c) 2025 Digital Asset (Switzerland) GmbH and/or its
# affiliates. All rights reserved.
#
# Copyright 2025 Digital Asset (Switzerland) GmbH and/or its affiliates
# SPDX-License-Identifier: BSD0

import time
import grpc
import pprint
import uuid

import com.daml.ledger.api.v2.admin.party_management_service_pb2 as party_management_service_pb2
import com.daml.ledger.api.v2.admin.party_management_service_pb2_grpc as party_management_service_pb2_grpc
import com.daml.ledger.api.v2.command_service_pb2 as command_service_pb2
import com.daml.ledger.api.v2.command_service_pb2_grpc as command_service_pb2_grpc
import com.daml.ledger.api.v2.commands_pb2 as commands_pb2
import com.daml.ledger.api.v2.package_service_pb2 as package_service_pb2
import com.daml.ledger.api.v2.package_service_pb2_grpc as package_service_pb2_grpc
import com.daml.ledger.api.v2.state_service_pb2 as state_service_pb2
import com.daml.ledger.api.v2.state_service_pb2_grpc as state_service_pb2_grpc
import com.daml.ledger.api.v2.transaction_filter_pb2 as transaction_filter_pb2
import com.daml.ledger.api.v2.value_pb2 as value_pb2
import com.daml.ledger.api.v2.version_service_pb2 as version_service_pb2
import com.daml.ledger.api.v2.version_service_pb2_grpc as version_service_pb2_grpc
import com.daml.ledger.api.v2.update_service_pb2 as update_service_pb2
import com.daml.ledger.api.v2.update_service_pb2_grpc as update_service_pb2_grpc


from .util import FAIL
from .value import record, value, decode


def _ensure_list(p):
    if p:
        return p if isinstance(p, list) else [p]
    else:
        return []


class LedgerConnection:
    def __init__(self, addr, *, user_id="default"):
        self.addr = addr
        self.user_id = user_id
        self.channel = None

    def __enter__(self):
        self.open()

        return self

    def __exit__(self, exception_type, exception_value, exception_traceback):
        self.close()

    def open(self):
        if self.channel is not None:
            raise Exception(f"Cannot open a channel twice: {self}")

        channel = grpc.insecure_channel(self.addr)

        self.channel = channel

        self._version_service = version_service_pb2_grpc.VersionServiceStub(channel)
        self._package_service = package_service_pb2_grpc.PackageServiceStub(channel)
        self._party_management_service = (
            party_management_service_pb2_grpc.PartyManagementServiceStub(channel)
        )
        self._state_service = state_service_pb2_grpc.StateServiceStub(channel)
        self._command_service = command_service_pb2_grpc.CommandServiceStub(channel)
        self._update_service = update_service_pb2_grpc.UpdateServiceStub(channel)

        return self

    def close(self):
        if self.channel is None:
            raise Exception(f"Channel cannot be closed (not open): {self}")

        self.channel.close()
        self.channel = None

    def _gen_command_id(self):
        return uuid.uuid4().hex

    def get_ledger_version(self):
        req = version_service_pb2.GetLedgerApiVersionRequest()

        return self._version_service.GetLedgerApiVersion(req).version

    def get_ledger_end(self):
        req = state_service_pb2.GetLedgerEndRequest()

        return self._state_service.GetLedgerEnd(req).offset

    def get_ledger_packages(self):
        req = package_service_pb2.ListPackagesRequest()

        return self._package_service.ListPackages(req)

    def get_ledger_parties(self):
        req = party_management_service_pb2.ListKnownPartiesRequest()

        return [
            {"party": p.party, "is_local": p.is_local}
            for p in self._party_management_service.ListKnownParties(req).party_details
        ]

    def get_ledger_local_parties(self):
        return [p for p in self.get_ledger_parties() if p["is_local"]]

    def lookup_local_party_id(self, party_name):
        for p in self.get_ledger_local_parties():
            if party_name == p["party"].split(":")[0] or party_name == p["party"]:
                return p["party"]

        return None

    def allocate_party(self, party_id_hint):
        req = party_management_service_pb2.AllocatePartyRequest(
            party_id_hint=party_id_hint
        )

        return self._party_management_service.AllocateParty(req)

    def _get_transaction_filter(self, party, template_ids=[]):
        def template_filter(tid):
            return transaction_filter_pb2.CumulativeFilter(
                template_filter=transaction_filter_pb2.TemplateFilter(
                    template_id=tid
                )
            )


        return transaction_filter_pb2.TransactionFilter(
            filters_by_party={
                party: transaction_filter_pb2.Filters(
                    cumulative=[
                        template_filter(tid) for tid in _ensure_list(template_ids)
                    ]
                )
            }
        )

    def get_active_contracts(self, party, template_ids=[]):
        req = state_service_pb2.GetActiveContractsRequest(
            filter=self._get_transaction_filter(party, template_ids), verbose=True
        )

        return [
            decode(c.active_contract)
            for c in self._state_service.GetActiveContracts(req)
            if not c.offset
        ]


    def submit(
        self,
        act_as,
        commands,
        *,
        command_id=None,
        deduplication_offset=None,
        disclosed_contracts=[],
    ):
        commands = commands_pb2.Commands(
            user_id=self.user_id,
            command_id=command_id or self._gen_command_id(),
            act_as=_ensure_list(act_as),
            commands=_ensure_list(commands),
            deduplication_offset=deduplication_offset,
            disclosed_contracts=disclosed_contracts,
        )

        req = command_service_pb2.SubmitAndWaitRequest(commands=commands)

        return decode(self._command_service.SubmitAndWaitForTransaction(req))

    def _get_updates(self, begin_exclusive, end_inclusive, party, template_ids=[]):
        req = update_service_pb2.GetUpdatesRequest(
            begin_exclusive=begin_exclusive,
            end_inclusive=end_inclusive,
            filter=self._get_transaction_filter(party, template_ids),
            verbose=True,
        )

        for u in self._update_service.GetUpdates(req):
            yield decode(u)

    def get_updates(self, party, template_ids=[]):
        offset_end = self.get_ledger_end()
        return self._get_updates(0, offset_end, party, template_ids)

    def get_update_stream(self, party, template_ids=[]):
        offset_end = self.get_ledger_end()
        return self._get_updates(offset_end, None, party, template_ids)


def create_contract(tid, create_arguments):
    return commands_pb2.Command(
        create=commands_pb2.CreateCommand(
            template_id=tid, create_arguments=record({**create_arguments})
        )
    )


def exercise_contract_choice(tid, cid, choice, choice_arguments):
    return commands_pb2.Command(
        exercise=commands_pb2.ExerciseCommand(
            template_id=tid,
            contract_id=cid,
            choice=choice,
            choice_argument=value(record(choice_arguments)),
        )
    )


def create_contract_and_exercise(tid, create_arguments, choice, choice_arguments):
    return commands_pb2.Command(
        create_and_exercise=commands_pb2.CreateAndExerciseCommand(
            template_id=tid,
            create_arguments=record({**create_arguments}),
            choice=choice,
            choice_argument=value(record(choice_arguments)),
        )
    )


RETRYABLE_STATUS_CODES = [
    grpc.StatusCode.UNIMPLEMENTED,  # Possible at startup due to Canton initialization order
    grpc.StatusCode.UNAVAILABLE,
    grpc.StatusCode.NOT_FOUND,
    grpc.StatusCode.ALREADY_EXISTS,
    grpc.StatusCode.FAILED_PRECONDITION,
    grpc.StatusCode.DEADLINE_EXCEEDED,
    grpc.StatusCode.ABORTED,
    grpc.StatusCode.UNAUTHENTICATED,
    grpc.StatusCode.PERMISSION_DENIED,  # Possible if token expired
]


def retry_ledger_op(opfn, attempt_limit=3, retry_delay_sec=2):
    current_error = None

    attempt_num = 0
    while attempt_num < attempt_limit:
        attempt_num = attempt_num + 1

        try:
            return opfn()
        except grpc.RpcError as e:
            if e.code() in RETRYABLE_STATUS_CODES:
                print("Retryable Error:", e)
                current_error = e
            else:
                print("Non-retryable Error:", e)
                raise e

        time.sleep(retry_delay_sec)

    print(f"Limit on number of attempts ({attempt_limit}) exhausted. Not retrying")
    raise current_error
