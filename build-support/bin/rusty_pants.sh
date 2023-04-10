#!/usr/bin/env bash
# Copyright 2023 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)
# shellcheck disable=SC1091
source "${HERE}/../common.sh"

PY="$(determine_python)"

_RUSTY_PANTS_PANTS_VERSION=2.17.0.dev1
_RUSTY_PANTS_CARGO_DIR="$(dirname "$(which cargo)")"
_RUSTY_PANTS_RUSTUP_DIR="$(dirname "$(which rustup)")"
_RUSTY_PANTS_PYTHON_DIR="$(dirname "$(which "$PY")")"
_RUSTY_PANTS_PYTHON_BINARY="$(basename "$(which "$PY")")"

export _RUSTY_PANTS_CARGO_DIR
export _RUSTY_PANTS_RUSTUP_DIR
export _RUSTY_PANTS_PYTHON_DIR
export _RUSTY_PANTS_PYTHON_BINARY

if ! command -v pants &> /dev/null; then
  die "Please install the Pants Native Binary (\"scie-pants\") and ensure \`pants\` is on your PATH."
fi

PANTS_VERSION=${_RUSTY_PANTS_PANTS_VERSION} \
    PANTS_BACKEND_PACKAGES="[
        'pants.backend.docker',        
        'pants.backend.experimental.adhoc',
        'pants.backend.python',
        'pants.backend.shell',
    ]" \
    pants --no-pantsd --no-verify-config --no-delegate-bootstrap export-codegen src/rust/engine:compile_rust
