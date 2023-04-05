# Copyright 2023 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

system_binary(
    name="rustup",
    binary_name="rustup",
    description="The `rustup` binary",
    extra_search_paths=[
        "/Users/chrisjrn/.cargo/bin",
    ],
    fingerprint_args=["-V"],
)

system_binary(
    name="cargo",
    binary_name="cargo",
    description="The `cargo` binary",
    extra_search_paths=[
        "/Users/chrisjrn/.cargo/bin",
    ],
)

system_binary(
    name="cc",
    binary_name="cc",
    fingerprint_args=["--version"],
)

system_binary(
    name="python3",
    binary_name="python3",
    fingerprint_args=["--version"],
    extra_search_paths=[
        "/Users/chrisjrn/.pyenv/shims",
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
        # "--release",
        "-p",
        "engine",
        "-p",
        "client",
    ],
    extra_env_vars=[
        "PY=/Users/chrisjrn/.pyenv/shims/python3.9",
        "PY03_PYTHON=/Users/chrisjrn/.pyenv/shims/python3.9",
        "PYTHON_SYS_EXECUTABLE=/Users/chrisjrn/.pyenv/shims/python3.9",
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

"""

PY="$(determine_python)"
export PY
export PYO3_PYTHON="${PY}"
export PYTHON_SYS_EXECUTABLE="${PY}" # Consumed by the cpython crate.

"${REPO_ROOT}/cargo" build \
    --features=extension-module \
    ${MODE_FLAG} \
    -p engine \
    -p client 
    
"""
