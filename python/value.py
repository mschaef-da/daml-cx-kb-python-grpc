# Copyright (c) 2025 Digital Asset (Switzerland) GmbH and/or its
# affiliates. All rights reserved.
#
# Copyright 2025 Digital Asset (Switzerland) GmbH and/or its affiliates
# SPDX-License-Identifier: BSD0

import datetime
import decimal
import json

import com.daml.ledger.api.v2.command_service_pb2 as command_service_pb2
import com.daml.ledger.api.v2.commands_pb2 as commands_pb2
import com.daml.ledger.api.v2.event_pb2 as event_pb2
import com.daml.ledger.api.v2.state_service_pb2 as state_service_pb2
import com.daml.ledger.api.v2.transaction_pb2 as transaction_pb2
import com.daml.ledger.api.v2.update_service_pb2 as update_service_pb2
import com.daml.ledger.api.v2.value_pb2 as value_pb2

from dataclasses import dataclass

from .util import FAIL

MICROSEC_PER_SEC = 1000000

NumericStr = str

DA_TYPES_ID = "5aee9b21b8e9a4c4975b5f4c4198e6e6e8469df49e2010820e792f393db870f4"

REL_TIME_ID = value_pb2.Identifier(
    package_id="b70db8369e1c461d5c70f1c86f526a29e9776c655e6ffc2560f95b05ccb8b946",
    module_name="DA.Time.Types",
    entity_name="RelTime",
)


### Value Encoding


@dataclass(frozen=True)
class Party:
    party: "str"


def party(party):
    return Party(party=party)


def reltime(microseconds=0, milliseconds=0, seconds=0):
    return record(
        {
            "__record_id": REL_TIME_ID,
            "microseconds": ((seconds * 1000) + milliseconds) * 1000 + microseconds,
        }
    )


def optional(v):
    if v:
        return value_pb2.Value(optional=value_pb2.Optional(value=v))
    else:
        return value_pb2.Value(optional=value_pb2.Optional())


def numeric(n, precision=10):
    if isinstance(n, int):
        return numeric(str(n))
    elif isinstance(n, float) or isinstance(n, decimal.Decimal):
        return numeric(format(n, f".{precision}f"))
    else:
        return value_pb2.Value(numeric=n)


def contract_id(n):
    return value_pb2.Value(contract_id=n)


def variant(variant_id, constructor, v):
    return value_pb2.Variant(constructor=constructor, value=v)


def _encode_genmap(v):
    return value_pb2.GenMap(
        entries=[
            value_pb2.GenMap.Entry(key=value(key), value=value(v[key]))
            for key in v.keys()
        ]
    )


def _encode_list(v):
    return value_pb2.List(elements=[value(el) for el in v])


def _encode_tuple(v):
    arity = len(v)

    if arity < 1 or arity > 20:
        FAIL(f"No tuple type with {arity} slots")

    type_id = value_pb2.Identifier(
        package_id=DA_TYPES_ID, module_name="DA.Types", entity_name=f"Tuple{arity}"
    )

    return record(
        {
            "__record_id": type_id,
            **{f"_{index}": value for (value, index) in zip(v, range(1, arity + 1))},
        }
    )


def value(v):
    if isinstance(v, value_pb2.Value):
        return v

    elif isinstance(v, bool):
        return value_pb2.Value(bool=v)

    elif isinstance(v, int):
        return value_pb2.Value(int64=v)

    elif isinstance(v, str):
        return value_pb2.Value(text=v)

    elif isinstance(v, datetime.datetime):
        return value_pb2.Value(timestamp=int(v.timestamp() * MICROSEC_PER_SEC))

    elif isinstance(v, Party):
        return value_pb2.Value(party=v.party)

    elif isinstance(v, dict):
        return value_pb2.Value(gen_map=_encode_genmap(v))

    elif isinstance(v, list):
        return value_pb2.Value(list=_encode_list(v))

    elif isinstance(v, tuple):
        return value_pb2.Value(record=_encode_tuple(v))

    elif isinstance(v, value_pb2.Record):
        return value_pb2.Value(record=v)

    elif isinstance(v, value_pb2.Variant):
        return value_pb2.Value(variant=v)

    else:
        FAIL(f"Cannot encode value: {v}")


def record(fields):
    fields = fields.copy()
    record_id = fields.pop("__record_id", None)

    return value_pb2.Record(
        record_id=record_id,
        fields=[
            value_pb2.RecordField(label=key, value=value(fields[key]))
            for key in fields.keys()
        ],
    )


### Value Decoding


def DECODE_FAIL(v, message=None):
    extra_msg = f"({message}) " if message else ""

    FAIL(f"Cannot decode value. {extra_msg}Type: {type(v)}")


def decode_active_contract(v):
    return {
        "reassignment_counter": v.reassignment_counter,
        **decode(v.created_event),
    }


def decode_party_list(parties):
    return [party(p) for p in parties]


def decode_archived_event(v):
    return {
        "event": "archived",
        "offset": v.offset,
        "contract_id": v.contract_id,
        "template_id": decode(v.template_id),
        "witness_parties": decode_party_list(v.witness_parties),
        "package_name": v.package_name,
    }


def decode_created_event(v):
    return {
        "event": "created",
        "offset": v.offset,
        "contract_id": v.contract_id,
        "template_id": decode(v.template_id),
        "witness_parties": decode_party_list(v.witness_parties),
        "signatories": decode_party_list(v.signatories),
        "observers": decode_party_list(v.observers),
        "package_name": v.package_name,
        "interface_views": v.interface_views,
        "create_arguments": decode(v.create_arguments),
        "created_event_blob": v.created_event_blob,
    }


def disclosure(c):
    return commands_pb2.DisclosedContract(
        template_id=value_pb2.Identifier(**c["template_id"]),
        contract_id=c["contract_id"],
        created_event_blob=c["created_event_blob"],
    )


def decode_identifier(v):
    return {
        "package_id": v.package_id,
        "module_name": v.module_name,
        "entity_name": v.entity_name,
    }


def decode_list(v):
    return [decode(e) for e in v.elements]


def get_tuple_arity(rid):
    if rid.module_name == "DA.Types" and rid.entity_name.startswith("Tuple"):
        return int(rid.entity_name[5:])
    else:
        return None


def decode_record(v):
    tuple_arity = get_tuple_arity(v.record_id)

    record_dict = {
        #'__record_id': v.record_id,
        **{f.label: decode(f.value) for f in v.fields}
    }

    if tuple_arity:
        return tuple([record_dict[f"_{index}"] for index in range(1, tuple_arity + 1)])
    else:
        return record_dict


def decode_genmap(v):
    return {decode(e.key): decode(e.value) for e in v.entries}


def decode_optional(v):
    if v.HasField("value"):
        return decode(v.value)
    else:
        return None


def decode_timestamp(v):
    return datetime.datetime.fromtimestamp(
        v / MICROSEC_PER_SEC, tz=datetime.timezone.utc
    )


def decode_numeric(v):
    return decimal.Decimal(v)


def decode_party(v):
    return Party(party=v)


def decode_value(v):
    if v.HasField("bool"):
        return v.bool

    elif v.HasField("int64"):
        return v.int64

    elif v.HasField("text"):
        return v.text

    elif v.HasField("timestamp"):
        return decode_timestamp(v.timestamp)

    elif v.HasField("party"):
        return decode_party(v.party)

    elif v.HasField("contract_id"):
        return v.contract_id

    elif v.HasField("optional"):
        return decode_optional(v.optional)

    elif v.HasField("numeric"):
        return decode_numeric(v.numeric)

    elif v.HasField("gen_map"):
        return decode_genmap(v.gen_map)

    elif v.HasField("list"):
        return decode(v.list)

    elif v.HasField("record"):
        return decode_record(v.record)

    else:
        return v


def decode_event(v):
    if v.HasField("created"):
        return decode(v.created)
    elif v.HasField("archived"):
        return decode(v.archived)
    else:
        DECODE_FAIL(v)


def decode_transaction(v):
    return {
        "update_id": v.update_id,
        "command_id": v.command_id,
        "workflow_id": v.workflow_id,
        "offset": v.offset,
        "events": [decode_event(e) for e in v.events],
    }


def decode_updates_response(v):
    if v.HasField("transaction"):
        return decode_transaction(v.transaction)
    elif v.HasField("reassignment"):
        DECODE_FAIL(v, "domain reassignments not currently supported")
    else:
        DECODE_FAIL(v)


def decode(v):
    if isinstance(v, state_service_pb2.ActiveContract):
        return decode_active_contract(v)
    elif isinstance(v, event_pb2.ArchivedEvent):
        return decode_archived_event(v)
    elif isinstance(v, event_pb2.CreatedEvent):
        return decode_created_event(v)
    elif isinstance(v, value_pb2.Identifier):
        return decode_identifier(v)
    elif isinstance(v, value_pb2.Record):
        return decode_record(v)
    elif isinstance(v, value_pb2.List):
        return decode_list(v)
    elif isinstance(v, value_pb2.Value):
        return decode_value(v)
    elif isinstance(v, event_pb2.Event):
        return decode_event(v)
    elif isinstance(v, transaction_pb2.Transaction):
        return decode_transaction(v)
    elif isinstance(v, command_service_pb2.SubmitAndWaitForTransactionResponse):
        return decode(v.transaction)
    elif isinstance(v, update_service_pb2.GetUpdatesResponse):
        return decode_updates_response(v)
    else:
        DECODE_FAIL(v)


###


class Package:
    def __init__(self, package_id):
        self.package_id = package_id

    def id(self, module_name, entity_name):
        return value_pb2.Identifier(
            package_id=self.package_id, module_name=module_name, entity_name=entity_name
        )
