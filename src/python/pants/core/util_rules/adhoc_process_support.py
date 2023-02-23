# Copyright 2023 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).
from __future__ import annotations

import dataclasses
import logging
import os
import shlex
from dataclasses import dataclass
from textwrap import dedent  # noqa: PNT20
from typing import Iterable, Mapping, TypeVar, Union

from pants.base.deprecated import warn_or_error
from pants.build_graph.address import Address
from pants.core.goals.package import BuiltPackage, EnvironmentAwarePackageRequest, PackageFieldSet
from pants.core.goals.run import RunFieldSet, RunInSandboxRequest
from pants.core.target_types import FileSourceField
from pants.core.util_rules.source_files import SourceFiles, SourceFilesRequest
from pants.core.util_rules.system_binaries import BashBinary
from pants.engine.addresses import Addresses, UnparsedAddressInputs
from pants.engine.env_vars import EnvironmentVars, EnvironmentVarsRequest
from pants.engine.fs import (
    EMPTY_DIGEST,
    CreateDigest,
    Digest,
    Directory,
    FileContent,
    MergeDigests,
    Snapshot,
)
from pants.engine.internals.native_engine import RemovePrefix
from pants.engine.process import FallibleProcessResult, Process, ProcessResult, ProductDescription
from pants.engine.rules import Get, MultiGet, collect_rules, rule
from pants.engine.target import (
    FieldSetsPerTarget,
    FieldSetsPerTargetRequest,
    SourcesField,
    Targets,
    TransitiveTargets,
    TransitiveTargetsRequest,
)
from pants.util.frozendict import FrozenDict

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AdhocProcessRequest:
    description: str
    address: Address
    working_directory: str
    root_output_directory: str
    argv: tuple[str, ...]
    timeout: int | None
    input_digest: Digest
    immutable_input_digests: FrozenDict[str, Digest] | None
    append_only_caches: FrozenDict[str, str] | None
    output_files: tuple[str, ...]
    output_directories: tuple[str, ...]
    fetch_env_vars: tuple[str, ...]
    supplied_env_var_values: FrozenDict[str, str] | None
    log_on_process_errors: FrozenDict[int, str] | None
    log_output: bool


@dataclass(frozen=True)
class AdhocProcessResult:
    process_result: ProcessResult
    adjusted_digest: Digest


@dataclass(frozen=True)
class ResolveExecutionDependenciesRequest:
    address: Address
    execution_dependencies: tuple[str | runnable, ...] | None
    dependencies: tuple[str, ...] | None  # can go away after 2.17.0.dev0 per deprecation


@dataclass(frozen=True)
class ResolvedExecutionDependencies:
    digest: Digest
    runnable_dependencies: RunnableDependencies | None


@dataclass(frozen=True)
class runnable:
    """Allows for an execution dependency to be specified as `runnable`.

    When resolved, the dependency will be available on the `PATH` with the name `name`.

    `runnable` dependencies are not resolved transitively, and must be defined on the target that
    wants to run those dependencies.
    """

    name: str
    address: str


@dataclass(frozen=True)
class RunnableDependencies:
    path_component: str
    immutable_input_digests: FrozenDict[str, Digest]
    append_only_caches: FrozenDict[str, str]


@rule
async def resolve_execution_environment(
    request: ResolveExecutionDependenciesRequest,
    bash: BashBinary,
) -> ResolvedExecutionDependencies:

    target_address = request.address
    raw_execution_dependencies = request.execution_dependencies
    raw_regular_dependencies = request.dependencies

    any_dependencies_defined = raw_regular_dependencies is not None

    # Always include the execution dependencies that were specified
    if raw_execution_dependencies is not None:
        _descr = f"the `execution_dependencies` from the target {target_address}"
        strings = (i for i in raw_execution_dependencies if isinstance(i, str))
        runnables = tuple(i for i in raw_execution_dependencies if isinstance(i, runnable))

        execution_dependencies = await Get(
            Addresses,
            UnparsedAddressInputs(
                strings,
                owning_address=target_address,
                description_of_origin=_descr,
            ),
        )
        runnables_digest, runnable_dependencies = await _resolve_runnable_dependencies(
            bash, runnables, target_address, _descr
        )
    elif any_dependencies_defined:
        # If we're specifying the `dependencies` as relevant to the execution environment, then
        # include this command as a root for the transitive dependency search for execution
        # dependencies.
        execution_dependencies = Addresses((target_address,))
        warn_or_error(
            "2.17.0.dev0",
            "Using `dependencies` to specify execution-time dependencies for `shell_command` ",
            (
                "To clear this warning, use the `output_dependencies` and `execution_dependencies`"
                "fields. Set `execution_dependencies=()` if you have no execution-time "
                "dependencies."
            ),
            print_warning=True,
        )
        runnables_digest, runnable_dependencies = EMPTY_DIGEST, None
    else:
        execution_dependencies = Addresses((target_address,))
        runnables_digest, runnable_dependencies = EMPTY_DIGEST, None

    transitive = await Get(
        TransitiveTargets,
        TransitiveTargetsRequest(execution_dependencies),
    )

    all_dependencies = (
        *(i for i in transitive.roots if i.address is not target_address),
        *transitive.dependencies,
    )

    sources, pkgs_per_target = await MultiGet(
        Get(
            SourceFiles,
            SourceFilesRequest(
                sources_fields=[tgt.get(SourcesField) for tgt in all_dependencies],
                for_sources_types=(SourcesField, FileSourceField),
                enable_codegen=True,
            ),
        ),
        Get(
            FieldSetsPerTarget,
            FieldSetsPerTargetRequest(PackageFieldSet, all_dependencies),
        ),
    )

    packages = await MultiGet(
        Get(BuiltPackage, EnvironmentAwarePackageRequest(field_set))
        for field_set in pkgs_per_target.field_sets
    )

    dependencies_digest = await Get(
        Digest,
        MergeDigests(
            [sources.snapshot.digest, runnables_digest, *(pkg.digest for pkg in packages)]
        ),
    )

    return ResolvedExecutionDependencies(dependencies_digest, runnable_dependencies)


async def _resolve_runnable_dependencies(
    bash: BashBinary, deps: tuple[runnable, ...], owning: Address, origin: str
) -> tuple[Digest, RunnableDependencies]:
    addresses = await Get(
        Addresses,
        UnparsedAddressInputs(
            (dep.address for dep in deps),
            owning_address=owning,
            description_of_origin=origin,
        ),
    )

    targets = await Get(Targets, Addresses, addresses)

    fspt = (
        await Get(
            FieldSetsPerTarget,
            FieldSetsPerTargetRequest(RunFieldSet, targets),
        ),
    )

    runnables = await MultiGet(
        Get(RunInSandboxRequest, RunFieldSet, field_set) for field_set in fspt
    )

    digests: list[Digest] = []
    shims: list[FileContent] = []
    immutable_input_digests: dict[str, Digest] = {}
    append_only_caches: dict[str, str] = {}

    for dep, runnable in zip(deps, runnables):
        digests.append(runnable.digest)
        shims.append(
            FileContent(
                dep.name,
                _runnable_dependency_shim(bash.path, runnable.args, runnable.extra_env),
                is_executable=True,
            )
        )

        try:
            _safe_update(immutable_input_digests, runnable.immutable_input_digests or {})
            _safe_update(append_only_caches, runnable.append_only_caches or {})
        except ValueError:
            # This error message could use improvement, but this is experimental for now *shrug*
            raise ValueError(
                "One or more runnable dependencies have mutually incompatible environments."
            )
        
    digest, shim_digest = await MultiGet(
        Get(Digest, MergeDigests(digests)), Get(Digest, CreateDigest(shims))
    )
    shim_digest_path = f"shims_{shim_digest.fingerprint}"

    immutable_input_digests[shim_digest_path] = shim_digest

    return (
        digest,
        RunnableDependencies(
            shim_digest_path,
            FrozenDict(immutable_input_digests),
            FrozenDict(append_only_caches),
        ),
    )


K = TypeVar("K")
V = TypeVar("V")


def _safe_update(d1: dict[K, V], d2: Mapping[K, V]) -> None:
    for k, v in d2.items():
        if k in d1 and d1[k] != v:
            raise ValueError("Beep")
        d1[k] = v


def _runnable_dependency_shim(
    bash: str, args: Iterable[str], extra_env: Mapping[str, str]
) -> bytes:
    """The binary shim script to be placed in the output directory for the digest."""
    binary = " ".join(shlex.quote(arg) for arg in args)
    env_str = "\n".join(
        f"export {shlex.quote(key)}={shlex.quote(value)}" for (key, value) in extra_env.items()
    )
    return dedent(
        f"""\
        #!{bash}
        {env_str}
        exec {binary} "$@"
        """
    ).encode()


@rule
async def run_adhoc_process(
    request: AdhocProcessRequest,
) -> AdhocProcessResult:
    process = await Get(Process, AdhocProcessRequest, request)

    fallible_result = await Get(FallibleProcessResult, Process, process)

    log_on_errors = request.log_on_process_errors or FrozenDict()
    error_to_log = log_on_errors.get(fallible_result.exit_code, None)
    if error_to_log:
        logger.error(error_to_log)

    result = await Get(
        ProcessResult,
        {
            fallible_result: FallibleProcessResult,
            ProductDescription(request.description): ProductDescription,
        },
    )

    if request.log_output:
        if result.stdout:
            logger.info(result.stdout.decode())
        if result.stderr:
            logger.warning(result.stderr.decode())

    working_directory = _parse_relative_directory(request.working_directory, request.address)
    root_output_directory = _parse_relative_directory(
        request.root_output_directory, working_directory
    )

    adjusted = await Get(Digest, RemovePrefix(result.output_digest, root_output_directory))

    return AdhocProcessResult(result, adjusted)


@rule
async def prepare_adhoc_process(
    request: AdhocProcessRequest,
    bash: BashBinary,
) -> Process:
    # currently only used directly by `experimental_test_shell_command`

    description = request.description
    address = request.address
    working_directory = _parse_relative_directory(request.working_directory or "", address)
    argv = request.argv
    timeout: int | None = request.timeout
    output_files = request.output_files
    output_directories = request.output_directories
    fetch_env_vars = request.fetch_env_vars
    supplied_env_vars = request.supplied_env_var_values or FrozenDict()
    append_only_caches = request.append_only_caches or FrozenDict()
    immutable_input_digests = request.immutable_input_digests or FrozenDict()

    command_env: dict[str, str] = {}

    extra_env = await Get(EnvironmentVars, EnvironmentVarsRequest(fetch_env_vars))
    command_env.update(extra_env)

    if supplied_env_vars:
        command_env.update(supplied_env_vars)

    input_snapshot = await Get(Snapshot, Digest, request.input_digest)

    if not working_directory or working_directory in input_snapshot.dirs:
        # Needed to ensure that underlying filesystem does not change during run
        work_dir = EMPTY_DIGEST
    else:
        work_dir = await Get(Digest, CreateDigest([Directory(working_directory)]))

    input_digest = await Get(Digest, MergeDigests([request.input_digest, work_dir]))

    proc = Process(
        argv=argv,
        description=f"Running {description}",
        env=command_env,
        input_digest=input_digest,
        output_directories=output_directories,
        output_files=output_files,
        timeout_seconds=timeout,
        working_directory=working_directory,
        append_only_caches=append_only_caches,
        immutable_input_digests=immutable_input_digests,
    )

    return _output_at_build_root(proc, bash)


def _output_at_build_root(process: Process, bash: BashBinary) -> Process:

    working_directory = process.working_directory or ""

    output_directories = process.output_directories
    output_files = process.output_files
    if working_directory:
        output_directories = tuple(os.path.join(working_directory, d) for d in output_directories)
        output_files = tuple(os.path.join(working_directory, d) for d in output_files)

    cd = f"cd {shlex.quote(working_directory)} && " if working_directory else ""
    shlexed_argv = " ".join(shlex.quote(arg) for arg in process.argv)
    new_argv = (bash.path, "-c", f"{cd}{shlexed_argv}")

    return dataclasses.replace(
        process,
        argv=new_argv,
        working_directory=None,
        output_directories=output_directories,
        output_files=output_files,
    )


def _parse_relative_directory(workdir_in: str, relative_to: Union[Address, str]) -> str:
    """Convert the `workdir` field into something that can be understood by `Process`."""

    if isinstance(relative_to, Address):
        reldir = relative_to.spec_path
    else:
        reldir = relative_to

    if workdir_in == ".":
        return reldir
    elif workdir_in.startswith("./"):
        return os.path.join(reldir, workdir_in[2:])
    elif workdir_in.startswith("/"):
        return workdir_in[1:]
    else:
        return workdir_in


def rules():
    return collect_rules()
