#!/usr/bin/env bash

_RUSTY_PANTS_PANTS_SHA=7c3ce8bea5595306582cb95173114d0f24dfd3ae
_RUSTY_PANTS_CARGO_DIR=`dirname \`which cargo\`` 
_RUSTY_PANTS_RUSTUP_DIR=`dirname \`which rustup\``
_RUSTY_PANTS_PYTHON_DIR=`dirname \`which $PY\``
_RUSTY_PANTS_PYTHON_BINARY=`basename \`which $PY\``

export _RUSTY_PANTS_CARGO_DIR
export _RUSTY_PANTS_RUSTUP_DIR
export _RUSTY_PANTS_PYTHON_DIR
export _RUSTY_PANTS_PYTHON_BINARY

PANTS_SHA=${_RUSTY_PANTS_PANTS_SHA} pants export-codegen src/rust/engine:compile_rust