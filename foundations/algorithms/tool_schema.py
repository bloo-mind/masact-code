"""Chapter 6's tool-as-data demonstration: a tool is just data.

A tool is declared to a model as data --- a name, a plain-language
description, and a JSON-Schema list of typed parameters --- and the
dispatcher that stands between model and world is a handful of ordinary
lines.  This module reproduces that listing verbatim.  ``dispatch``
validates a call's required fields and its argument types, returning an
``error`` dictionary (the model's next observation) rather than raising,
because the model has to read the result and retry against it, not catch
a stack trace.

This is the pre-runtime Chapter 6 demonstration and is deliberately kept
separate from ``foundations.tools``: it neither imports nor references the
runtime ``Tool``/``dispatch``, so a reader copying the listing from the
book finds exactly this, self-contained.  Standard library only.
"""

from collections.abc import Callable

run_tests_tool = {
    "name": "run_tests",
    "description": "Run the suite at a path; use to check the code.",
    "parameters": {"type": "object", "required": ["path"],
                   "properties": {"path": {"type": "string"}}}}
suite = {"tests/test_auth.py": {"passed": 5, "failed": 0}}
types = {"string": str, "integer": int, "boolean": bool}


def run_tests(path: str) -> dict:
    return suite[path]  # a real runner would shell out here


def dispatch(tool: dict, fn: Callable[..., dict], args: dict) -> dict:
    for field, spec in tool["parameters"]["properties"].items():
        if field in tool["parameters"]["required"] and field not in args:
            return {"error": f"missing field: {field}"}
        if field in args and not isinstance(args[field], types[spec["type"]]):
            return {"error": f"{field} must be {spec['type']}"}
    return fn(**args)
