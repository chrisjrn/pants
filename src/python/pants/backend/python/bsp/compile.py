# Copyright 2023 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).
from pants.bsp.util_rules.targets import BSPCompileRequest, BSPCompileResult
from pants.engine.rules import collect_rules


async def python_bsp_compile(request: BSPCompileRequest) -> BSPCompileResult:
    raise NotImplementedError("Not implemented yet")


def rules():
    return [
        *collect_rules(),
    ]
