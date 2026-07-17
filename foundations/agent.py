"""The agent loop: observe, reason, act --- with three ways to stop.

A loop that cannot stop is not persistent but pathological, so
``run`` carries a goal test (the ``done`` tool), a token budget, and a
turn cap. Chapter
20 prints ``run`` in full: it fits on a page, and the page is mostly the
honest handling of the three ways a turn can end.
"""

import json

from .budget import Budget
from .context import assemble
from .journal import append
from .model import ModelClient
from .tools import Tool, dispatch


def run(agent_id: str, client: ModelClient, tools: list[Tool],
        system: str, task: str, journal_path: str, budget: Budget,
        max_turns: int = 12) -> dict:
    toolbox = {t.name: t for t in tools}
    schemas = [t.schema for t in toolbox.values()]
    if "done" not in toolbox:         # the loop's own verb, always on offer
        schemas.append({"name": "done", "description":
                        "Finish the run; your arguments are the result.",
                        "required": []})
    history: list[str] = []
    observations: list[str] = []
    nudged = False
    append(journal_path, "RunStarted", agent=agent_id, task=task)
    for turn in range(max_turns):
        messages = assemble(system, task, history, observations)
        observations = []
        append(journal_path, "ModelCalled", agent=agent_id, turn=turn)
        response = client.complete(messages, schemas)
        append(journal_path, "ModelResponded", agent=agent_id,
               usage=response.usage)
        append(journal_path, "BudgetDebited", agent=agent_id,
               amount=response.usage)
        budget.debit(response.usage)
        for call in response.tool_calls:
            if call.name == "done":   # finishing is an explicit, typed act
                append(journal_path, "AgentFinished", agent=agent_id)
                result = {**call.args, "status": "done"}
                return result  # harness owns the verdict; later calls drop
            append(journal_path, "ToolDispatched", agent=agent_id,
                   tool=call.name)
            tool = toolbox.get(call.name)
            observation = (dispatch(tool, call.args) if tool else
                           {"tool": call.name, "error": "unknown tool"})
            append(journal_path, "ToolReturned", agent=agent_id,
                   **observation)
            observations.append(json.dumps(observation))
        drifted_again = not response.tool_calls and nudged
        if response.tool_calls:
            history.append(response.text or f"(turn {turn}: tool calls)")
            nudged = False
        elif not nudged:              # plain prose: nudge once, firmly
            history.append(response.text)
            observations.append("Reply with a tool call; "
                                "call done when finished.")
            nudged = True
        if budget.exhausted():        # wind down at the turn boundary
            append(journal_path, "BudgetExhausted", agent=agent_id)
            return {"status": "halted", "turns": turn + 1}
        if drifted_again:             # second consecutive drift: stop
            return {"status": "inconclusive", "turns": turn + 1}
    return {"status": "out_of_turns", "turns": max_turns}
