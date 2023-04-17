# Copyright 2023 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).
from pants.base.build_root import BuildRoot
from pants.bsp.util_rules.targets import BSPResourcesRequest, BSPResourcesResult
from pants.engine.rules import collect_rules


async def python_bsp_resources(
    request: BSPResourcesRequest, build_root: BuildRoot
) -> BSPResourcesResult:
    raise NotImplementedError("Not implemented yet")


def rules():
    return [
        *collect_rules(),
    ]
