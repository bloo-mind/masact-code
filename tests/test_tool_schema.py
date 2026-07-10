"""Tests for Chapter 6's tool-as-data dispatcher.

The two demonstrations in the book trace the branches a dispatcher must
cover: a well-formed call runs and returns an observation, and a
malformed one comes back as an ``error`` dictionary rather than a raised
exception.  The ``# ->`` values in the listing are asserted exactly.
"""

import pytest

from foundations.algorithms.tool_schema import (
    dispatch,
    run_tests,
    run_tests_tool,
    suite,
    types,
)


def test_happy_path_returns_the_suite_result() -> None:
    args = {"path": "tests/test_auth.py"}
    result = dispatch(run_tests_tool, run_tests, args)
    assert result == {"passed": 5, "failed": 0}  # -> book's first arrow


def test_wrong_type_returns_error_observation() -> None:
    result = dispatch(run_tests_tool, run_tests, {"path": 42})
    assert result == {"error": "path must be string"}  # -> second arrow


def test_missing_required_field_returns_error_dict() -> None:
    result = dispatch(run_tests_tool, run_tests, {})
    assert "error" in result
    assert result == {"error": "missing field: path"}


def test_error_is_returned_not_raised() -> None:
    # A malformed call must never raise: the model reads the observation.
    result = dispatch(run_tests_tool, run_tests, {"path": True})
    assert result == {"error": "path must be string"}


def test_undeclared_field_gap_is_deliberate() -> None:
    # TAUGHT-AS-FLAW (do not fix): the validation loop walks declared
    # properties only, so an undeclared argument reaches ``fn(**args)``
    # and raises --- the gap Chapter 6's Exercise 2 has the reader find
    # and close. This test pins the flaw so nobody repairs it by
    # accident and silently invalidates the exercise.
    args = {"path": "tests/test_auth.py", "verbose": True}
    with pytest.raises(TypeError):
        dispatch(run_tests_tool, run_tests, args)


def test_types_map_covers_the_schema_primitives() -> None:
    assert types == {"string": str, "integer": int, "boolean": bool}


def test_schema_shape_matches_the_book_listing() -> None:
    assert run_tests_tool["name"] == "run_tests"
    assert run_tests_tool["parameters"]["required"] == ["path"]
    props = run_tests_tool["parameters"]["properties"]
    assert props["path"] == {"type": "string"}
    assert suite == {"tests/test_auth.py": {"passed": 5, "failed": 0}}
