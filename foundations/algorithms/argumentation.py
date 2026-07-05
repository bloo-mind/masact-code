"""Dung's abstract argumentation, from Chapter 14.

An abstract argumentation framework <A, R_attacks> is a set of arguments
together with an attack relation, and the standing of any claim is a
property of that graph rather than of its rhetoric. This module computes
the *grounded extension* --- the sceptical, uniquely determined position a
rational judge is forced to accept --- as the least fixed point of the
defence function, iterated from the empty set on a finite graph.

`grounded` is reproduced verbatim from the book so that a reader copying
the listing lands on the identical function; `is_conflict_free` and
`is_admissible` are the standing predicates behind it. Preferred
extensions are deliberately left to the chapter's exercise.
"""

__all__ = ["grounded", "is_conflict_free", "is_admissible"]


def grounded(A: set[str], R_attacks: set[tuple[str, str]]) -> set[str]:
    def defends(E: set[str], a: str) -> bool:
        return all(any((c, b) in R_attacks for c in E)
                   for (b, x) in R_attacks if x == a)
    E: set[str] = set()
    while True:
        D = {a for a in A if defends(E, a)}
        if D == E:
            return E
        E = D


def is_conflict_free(
    E: set[str], R_attacks: set[tuple[str, str]]
) -> bool:
    """Does E hold no argument together with one it attacks?

    Conflict-freeness inspects only the pairs internal to E: the set is
    conflict-free when no ``(a, b)`` with both ``a`` and ``b`` in E is an
    attack (Dung 1995).
    """
    return not any((a, b) in R_attacks for a in E for b in E)


def is_admissible(
    E: set[str], A: set[str], R_attacks: set[tuple[str, str]]
) -> bool:
    """Is E an admissible position in the framework <A, R_attacks>?

    A subset E of A is *admissible* when it is conflict-free and defends
    each of its own members --- every attacker of a member is itself
    attacked by some member of E (Dung 1995). The grounded extension is
    the least such position; this predicate is what its fixpoint climbs
    towards.
    """
    defended = all(
        all(any((c, b) in R_attacks for c in E)
            for (b, x) in R_attacks if x == a)
        for a in E
    )
    return E <= A and is_conflict_free(E, R_attacks) and defended
