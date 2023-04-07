#!/usr/bin/env bash

HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)
# shellcheck disable=SC1091
source "${HERE}/../common.sh"

PY="$(determine_python)"

_RUSTY_PANTS_PANTS_SHA=7c3ce8bea5595306582cb95173114d0f24dfd3ae
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

PANTS_SHA=${_RUSTY_PANTS_PANTS_SHA} pants export-codegen src/rust/engine:compile_rust
