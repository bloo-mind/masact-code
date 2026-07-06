"""The frontier layer: dated laboratories on live agent platforms.

Chapters 19, 21, 22, and 27 each pose an empirical question --- which
framework, which topology, which protocol, how many agents --- and answer it
with a laboratory rather than an assertion. This layer is those laboratories.
It shares one measurement rig (:mod:`frontier.rig`) and one workload
(:mod:`frontier.tasks`); each lab is an instrument over them.

Being the frontier, it is *dated*: the runners plug into vendor SDKs that
rename their APIs at leisure, so the labs record the versions they were last
run against and are expected to need updating. The durable content is the
*method* --- the four columns, the flat maximum, the failure census --- not
the numbers.
"""

from .rig import RunResult, Runner, four_columns, mean, run_timed
from .runners import (
    claude_agent_runner, langgraph_runner, plain_runner, scripted_runner,
)
from .tasks import (
    COUPLED_TASK, ISSUE_BATCH, Issue, coupled_task, parallel_task,
)

__all__ = [
    "RunResult", "Runner", "four_columns", "mean", "run_timed",
    "scripted_runner", "langgraph_runner", "plain_runner",
    "claude_agent_runner", "Issue", "ISSUE_BATCH", "COUPLED_TASK",
    "parallel_task", "coupled_task",
]
