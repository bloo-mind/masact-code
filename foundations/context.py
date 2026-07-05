"""Context assembly: the engineering of the agent's perception.

The single most consequential hidden opinion in any agent framework ---
what does the model see? --- is, here, a short function with your name on
the commit. Chapter 20 prints ``assemble`` in full.
"""


def assemble(system: str, task: str, history: list[str],
             observations: list[str], limit: int = 8000) -> list[dict]:
    # The system prompt and the task are always kept; the rolling
    # history keeps its recent tail, oldest dropped first; the latest
    # observations always arrive. This is the whole policy.
    context = [{"role": "system", "content": system},
               {"role": "user", "content": task}]
    news = [{"role": "user", "content": o} for o in observations]
    budget = limit - sum(len(m["content"]) for m in context + news)
    tail: list[str] = []
    for step in reversed(history):    # newest first, until the budget
        if budget < len(step):
            break
        tail.insert(0, step)
        budget -= len(step)
    dropped = len(history) - len(tail)
    if dropped:
        tail.insert(0, f"[{dropped} earlier steps compacted]")
    context += [{"role": "assistant", "content": s} for s in tail]
    return context + news
