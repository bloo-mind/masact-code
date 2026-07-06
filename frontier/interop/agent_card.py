"""The agent altitude (Section 22.4): the A2A Agent Card.

An Agent Card is a machine-readable self-description an agent publishes at a
well-known address, so a peer can discover what it is and what it can do
before addressing it. This module builds one for the Chapter 20 coding team
directly from the A2A JSON shape as dataclasses, emitting the spec's
camelCase keys --- rather than pulling in ``a2a-sdk``, whose protobuf surface
is awkward for a teaching artefact.

NOTE: a card is an *advertisement*. Like any advertisement it is subject to
the winner's curse --- the agent whose card most overstates its competence
wins the task it is least fit for --- and to staleness, since the card and
the running system drift apart. So an advertised capability must be
*probed*, not believed: the card tells you what to test, not what is true.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

WELL_KNOWN_PATH = "/.well-known/agent-card.json"


class TaskState(Enum):
    """The A2A task lifecycle the book names."""

    SUBMITTED = "submitted"
    WORKING = "working"
    INPUT_REQUIRED = "input-required"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True)
class AgentSkill:
    """One advertised skill: an id, a name, a description, and tags."""

    id: str
    name: str
    description: str
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "tags": list(self.tags),
        }


@dataclass(frozen=True)
class AgentCard:
    """An A2A Agent Card --- the self-description published for discovery."""

    name: str
    description: str
    url: str
    version: str
    protocol_version: str
    capabilities: dict
    default_input_modes: list[str]
    default_output_modes: list[str]
    skills: list[AgentSkill]
    provider: dict

    def to_dict(self) -> dict:
        """Emit the spec's camelCase JSON keys."""
        return {
            "name": self.name,
            "description": self.description,
            "url": self.url,
            "version": self.version,
            "protocolVersion": self.protocol_version,
            "capabilities": dict(self.capabilities),
            "defaultInputModes": list(self.default_input_modes),
            "defaultOutputModes": list(self.default_output_modes),
            "skills": [s.to_dict() for s in self.skills],
            "provider": dict(self.provider),
        }


def agent_card_for_team() -> AgentCard:
    """The Agent Card for the Chapter 20 coding team."""
    skills = [
        AgentSkill(
            "fix-failing-test", "Fix a failing test",
            "Propose the smallest diff that turns a red suite green.",
            ["coding", "debugging"]),
        AgentSkill(
            "review-diff", "Review a diff",
            "Accept or reject a proposed change with a reason.",
            ["review", "quality"]),
        AgentSkill(
            "run-tests", "Run the test suite",
            "Run the suite against a diff and report green or red.",
            ["testing", "verification"]),
    ]
    return AgentCard(
        name="masact-coding-team",
        description=(
            "A supervised coding team: coder, reviewer, tester, working a "
            "bounded token budget to ship a verified diff."),
        url="https://example.invalid/masact-coding-team",
        version="1.0.0",
        protocol_version="0.3.0",
        capabilities={"streaming": True, "pushNotifications": False},
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain"],
        skills=skills,
        provider={"organization": "masact", "url": "https://example.invalid"},
    )


def discovery(card: AgentCard) -> tuple[str, dict]:
    """Where a peer fetches the card, and what it gets --- the discovery
    step a peer runs before addressing the agent."""
    return WELL_KNOWN_PATH, card.to_dict()
