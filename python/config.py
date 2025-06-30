# Copyright (c) 2025 Digital Asset (Switzerland) GmbH and/or its
# affiliates. All rights reserved.
#
# Copyright 2025 Digital Asset (Switzerland) GmbH and/or its affiliates
# SPDX-License-Identifier: BSD0

import json
import os

from dacite import from_dict
from dataclasses import dataclass
from mergedeep import merge
from pathlib import Path
from typing import Optional

from .util import FAIL
from .value import NumericStr


@dataclass(frozen=True)
class Config:
    ledgerAddress: "str"


def load_json(filename: str):
    p = Path(filename)

    if p.is_file():
        with open(p) as f:
            return json.load(f)
    else:
        FAIL(f"Config file does not exist: {filename}")


def load_config() -> "Config":
    data = load_json("config.json")

    extra_config_file = os.environ.get("EXTRA_CONFIG", None)
    if extra_config_file:
        data = merge(data, load_json(extra_config_file))

    return from_dict(data_class=Config, data=data)
