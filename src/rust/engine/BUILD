# Copyright 2023 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

_CARGO_BIN = f"{env('HOME')}/.cargo/bin"
_PYTHON_SEARCH_PATH = f"{env('HOME')}/.pyenv/shims"
_RUST_MODE = [] if env("MODE") == "debug" else ["--release"]

system_binary(
    name="rustup",
    binary_name="rustup",
    description="The `rustup` binary",
    extra_search_paths=[
        _CARGO_BIN,
    ],
    fingerprint_args=["-V"],
)

system_binary(
    name="cargo",
    binary_name="cargo",
    description="The `cargo` binary",
    extra_search_paths=[
        _CARGO_BIN,
    ],
)

system_binary(
    name="cc",
    binary_name="cc",
    fingerprint_args=["--version"],
)

system_binary(
    name="python3",
    binary_name="python3.9",
    fingerprint_args=["--version"],
    extra_search_paths=[
        _PYTHON_SEARCH_PATH,
    ],
)

system_binary(
    name="ar",
    binary_name="ar",
    fingerprint_args=["-qc", "foo.ar", "/dev/null"],  # _sigh_
)

files(
    name="rust_sources",
    sources=[
        "Cargo.lock",
        "build.rs",
        "**/Cargo.toml",
        "rustfmt.toml",
        "**/*.rs",
        "**/*.proto",
        ".cargo/config",
    ],
)

adhoc_tool(
    name="compile_rust",
    runnable=":cargo",
    execution_dependencies=[
        ":rust_sources",
        "//:rust_toolchain",
    ],
    args=[
        "build",
        "--features=extension-module",
    ]
    + _RUST_MODE
    + [
        "-p",
        "engine",
        "-p",
        "client",
    ],
    runnable_dependencies=[
        ":rustup",
        ":cc",
        ":ar",
        ":python3",
    ],
    output_directories=[
        "target",
    ],
    log_output=True,
)

adhoc_tool(
    name="announce_rust",
    runnable=":rustup",
    execution_dependencies=[
        "//:rust_toolchain",
    ],
    args=[
        "show",
    ],
    log_output=True,
)
