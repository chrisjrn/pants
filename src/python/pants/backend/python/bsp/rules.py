# Copyright 2023 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).
import logging
from dataclasses import dataclass

from pants.backend.python.bsp.compile import python_bsp_compile
from pants.backend.python.bsp.compile import rules as python_compile_rules
from pants.backend.python.bsp.resources import python_bsp_resources
from pants.backend.python.bsp.resources import rules as python_resources_rules
from pants.backend.python.bsp.spec import (
    PythonOptionsItem,
    PythonOptionsParams,
    PythonOptionsResult,
)
from pants.backend.python.goals.run_python_source import PythonSourceFieldSet
from pants.backend.python.target_types import PythonResolveField, PythonSourceField
from pants.base.build_root import BuildRoot
from pants.bsp.protocol import BSPHandlerMapping
from pants.bsp.spec.base import BuildTargetIdentifier
from pants.bsp.util_rules.lifecycle import BSPLanguageSupport
from pants.bsp.util_rules.targets import (
    BSPBuildTargetsMetadataRequest,
    BSPBuildTargetsMetadataResult,
    BSPCompileRequest,
    BSPCompileResult,
    BSPResourcesRequest,
    BSPResourcesResult,
)
from pants.engine.internals.selectors import Get, MultiGet
from pants.engine.rules import collect_rules, rule
from pants.engine.target import FieldSet
from pants.engine.unions import UnionRule

LANGUAGE_ID = "python"

_logger = logging.getLogger(__name__)


class PythonBSPLanguageSupport(BSPLanguageSupport):
    language_id = LANGUAGE_ID
    can_compile = False
    can_provide_resources = True


@dataclass(frozen=True)
class PythonMetadataFieldSet(FieldSet):
    required_fields = (PythonSourceField, PythonResolveField)

    source: PythonSourceField
    resolve: PythonResolveField


class PythonBSPBuildTargetsMetadataRequest(BSPBuildTargetsMetadataRequest):
    language_id = LANGUAGE_ID
    can_merge_metadata_from = ()
    field_set_type = PythonMetadataFieldSet

    resolve_prefix = "python"
    resolve_field = PythonResolveField


@rule
async def bsp_resolve_python_metadata(
    _: PythonBSPBuildTargetsMetadataRequest,
) -> BSPBuildTargetsMetadataResult:
    return BSPBuildTargetsMetadataResult()


# -----------------------------------------------------------------------------------------------
# Python Options Request
# See https://build-server-protocol.github.io/docs/extensions/python.html#python-options-request
# -----------------------------------------------------------------------------------------------


class PythonOptionsHandlerMapping(BSPHandlerMapping):
    method_name = "buildTarget/pythonOptions"
    request_type = PythonOptionsParams
    response_type = PythonOptionsResult


@dataclass(frozen=True)
class HandlePythonOptionsRequest:
    bsp_target_id: BuildTargetIdentifier


@dataclass(frozen=True)
class HandlePythonOptionsResult:
    item: PythonOptionsItem


@rule
async def handle_bsp_python_options_request(
    request: HandlePythonOptionsRequest,
    # build_root: BuildRoot,
) -> HandlePythonOptionsResult:
    return HandlePythonOptionsResult(
        PythonOptionsItem(
            target=request.bsp_target_id,
            linkopts=(),
        )
    )


@rule
async def bsp_python_options_request(request: PythonOptionsParams) -> PythonOptionsResult:
    results = await MultiGet(
        Get(HandlePythonOptionsResult, HandlePythonOptionsRequest(btgt)) for btgt in request.targets
    )
    return PythonOptionsResult(items=tuple(result.item for result in results))


# -----------------------------------------------------------------------------------------------
# Compile Request
# -----------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class PythonBSPCompileRequest(BSPCompileRequest):
    field_set_type = PythonSourceFieldSet


@rule
async def bsp_python_compile_request(request: PythonBSPCompileRequest) -> BSPCompileResult:
    result: BSPCompileResult = await python_bsp_compile(request)
    return result


# -----------------------------------------------------------------------------------------------
# Resources Request
# -----------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class PythonBSPResourcesRequest(BSPResourcesRequest):
    field_set_type = PythonSourceFieldSet


@rule
async def bsp_python_resources_request(
    request: PythonBSPResourcesRequest,
    build_root: BuildRoot,
) -> BSPResourcesResult:
    result: BSPResourcesResult = await python_bsp_resources(request, build_root)
    return result


def rules():
    return (
        *collect_rules(),
        *python_compile_rules(),
        *python_resources_rules(),
        UnionRule(BSPLanguageSupport, PythonBSPLanguageSupport),
        UnionRule(BSPBuildTargetsMetadataRequest, PythonBSPBuildTargetsMetadataRequest),
        UnionRule(BSPHandlerMapping, PythonOptionsHandlerMapping),
        UnionRule(BSPCompileRequest, PythonBSPCompileRequest),
        UnionRule(BSPResourcesRequest, PythonBSPResourcesRequest),
    )
