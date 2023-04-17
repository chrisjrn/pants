# Copyright 2023 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).
from __future__ import annotations

from dataclasses import dataclass

from pants.bsp.spec.base import BuildTargetIdentifier

# -----------------------------------------------------------------------------------------------
# Python Options Request
# See https://build-server-protocol.github.io/docs/extensions/python.html#python-options-request
# -----------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class PythonOptionsParams:
    targets: tuple[BuildTargetIdentifier, ...]

    @classmethod
    def from_json_dict(cls, d):
        return cls(
            targets=tuple(BuildTargetIdentifier.from_json_dict(x) for x in d["targets"]),
        )

    def to_json_dict(self):
        return {
            "targets": [tgt.to_json_dict() for tgt in self.targets],
        }


@dataclass(frozen=True)
class PythonOptionsItem:
    target: BuildTargetIdentifier

    # Attributes added to the interpreter command
    # For example, -E.
    linkopts: tuple[str, ...]

    def to_json_dict(self):
        return {
            "target": self.target.to_json_dict(),
            "linkopts": self.options,
        }


@dataclass(frozen=True)
class PythonOptionsResult:
    items: tuple[PythonOptionsItem, ...]

    def to_json_dict(self):
        return {"items": [item.to_json_dict() for item in self.items]}
