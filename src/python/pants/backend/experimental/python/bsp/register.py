# Copyright 2023 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from pants.backend.python.bsp import rules as bsp_rules


def rules():
    return [
        *bsp_rules.rules(),
    ]
