# Copyright 2020 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from textwrap import dedent

from pants.testutil.pants_integration_test import run_pants, setup_tmpdir

EMPTY_RESOLVE = """
# --- BEGIN PANTS LOCKFILE METADATA: DO NOT EDIT OR REMOVE ---
# {{
#   "version": 1,
#   "generated_with_requirements": [
#   ]
# }}
# --- END PANTS LOCKFILE METADATA ---
"""


def test_java() -> None:
    sources = {
        "src/org/pantsbuild/test/Hello.java": dedent(
            """\
            package org.pantsbuild.test;

            public class Hello {{
                public static void main(String[] args) {{
                    System.out.println("Hello, World!");
                }}
            }}
            """
        ),
        "src/org/pantsbuild/test/BUILD": dedent(
            """\
            java_sources()
            deploy_jar(
                name="test_deploy_jar",
                main="org.pantsbuild.test.Hello",
                dependencies=[":test"],
            )
            """
        ),
        "lockfile": EMPTY_RESOLVE,
    }
    with setup_tmpdir(sources) as tmpdir:
        args = [
            "--backend-packages=pants.backend.experimental.java",
            f"--source-root-patterns=['{tmpdir}/src']",
            "--pants-ignore=__pycache__",
            f'--jvm-resolves={{"empty": "{tmpdir}/lockfile"}}',
            "--jvm-default-resolve=empty",
            "run",
            f"{tmpdir}/src/org/pantsbuild/test:test_deploy_jar",
        ]
        result = run_pants(args)
        assert result.stdout.strip() == "Hello, World!"


def test_scala() -> None:
    sources = {
        "src/org/pantsbuild/test/Hello.scala": dedent(
            """\
            package org.pantsbuild.test;

            object Hello {{
                def main(args: Array[String]): Unit = {{
                    println("Hello, World!")
                }}
            }}

            """
        ),
        "src/org/pantsbuild/test/BUILD": dedent(
            """\
            scala_sources()
            deploy_jar(
                name="test_deploy_jar",
                main="org.pantsbuild.test.Hello",
                dependencies=[":test"],
            )
            """
        ),
        "lockfile": EMPTY_RESOLVE,
    }
    with setup_tmpdir(sources) as tmpdir:
        args = [
            "--backend-packages=pants.backend.experimental.scala",
            f"--source-root-patterns=['{tmpdir}/src']",
            "--pants-ignore=__pycache__",
            f'--jvm-resolves={{"empty": "{tmpdir}/lockfile"}}',
            "--jvm-default-resolve=empty",
            "run",
            f"{tmpdir}/src/org/pantsbuild/test:test_deploy_jar",
        ]
        result = run_pants(args)
        assert result.stdout.strip() == "Hello, World!"
