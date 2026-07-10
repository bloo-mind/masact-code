"""The team's typed state --- Chapter 23's reducers made a type-level fact.

Where ``foundations/journal.py`` folds an event log by hand, LangGraph reads
the per-field merge policy straight off the annotations: an ``Annotated``
reducer where parallel branches must combine, a bare field where a single
writer per superstep overwrites (and a second concurrent writer is rejected at
the merge). The three fields the book prints --- ``findings``, ``status``,
``turn`` --- are here, with the rest the working graph needs.
"""

import operator
from typing import Annotated, TypedDict


class TeamState(TypedDict):
    task: str
    # findings accumulate from every node --- the book's reducer example
    findings: Annotated[list[str], operator.add]
    # the shared treasury: every node debits it, so the writes must sum
    spent: Annotated[int, operator.add]
    # ...and the treasury has a ceiling the nodes enforce before spending
    allowance: int
    diff: str          # bare: one writer per superstep, or the merge raises
    verdict: str       # "accept" | "reject" | ""
    suite: str         # "green" | "red" | ""
    approved: bool
    status: str
    turn: int          # single-writer counter


NO_CAP = 10**9         # the default allowance: effectively uncapped


def initial_state(task: str, allowance: int = NO_CAP) -> TeamState:
    return TeamState(
        task=task, findings=[], spent=0, allowance=allowance, diff="",
        verdict="", suite="", approved=False, status="start", turn=0,
    )
