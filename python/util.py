# Copyright (c) 2024 Digital Asset (Switzerland) GmbH and/or its
# affiliates. All rights reserved.
#
# This code is DA Background Intellectual Property as defined in the
# Master Product Agreement between DA and the client.


def FAIL(msg):
    raise RuntimeError(msg)


def to_boolean(x):
    if isinstance(x, bool):
        return x
    elif isinstance(x, int):
        return x != 0
    elif isinstance(x, str):
        return x.lower() in ["y", "yes", "1", "t", "true"]
    elif x is None:
        return False
    else:
        raise Exception(f"Invalid argument for to_boolean: {x}")
