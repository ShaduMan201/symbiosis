"""
engine.py — Phase 1: Simulation Engine
=======================================
Houses the Simulation class that orchestrates a round-robin
tournament among any list of Agent instances.

Key responsibilities
--------------------
* Apply the Prisoner's Dilemma payoff matrix after every round.
* Run a configurable number of rounds per head-to-head match.
* Accumulate per-agent *tournament* scores (sum of all match scores).
* Provide a clean summary for terminal output (and later, Pygame).
"""

import itertools
from typing import List, Tuple

from agents import (
    Agent,
    COOPERATE, DEFECT,
    REWARD, TEMPTATION, SUCKER, PUNISHMENT,
)


# ── Payoff lookup ────────────────────────────────────────────────────────────
#  _PAYOFF[(my_move, opp_move)] → (my_points, opp_points)
_PAYOFF: dict[Tuple[str, str], Tuple[int, int]] = {
    (COOPERATE, COOPERATE): (REWARD,     REWARD),
    (COOPERATE, DEFECT):    (SUCKER,     TEMPTATION),
    (DEFECT,    COOPERATE): (TEMPTATION, SUCKER),
    (DEFECT,    DEFECT):    (PUNISHMENT, PUNISHMENT),
}


class Simulation:
    """
    Round-robin tournament engine.

    Parameters
    ----------
    agents        : List of Agent instances to pit against each other.
    rounds_per_match : Number of rounds each head-to-head match lasts.
    noise         : Probability [0, 1] that a COOPERATE becomes a DEFECT
                    due to miscommunication (added in Phase 4; wired in
                    from the start to avoid a future refactor).
    """

    def __init__(
        self,
        agents: List[Agent],
        rounds_per_match: int = 200,
        noise: float = 0.0,
    ):
        self.agents           = agents
        self.rounds_per_match = rounds_per_match
        self.noise            = noise

        # tournament_scores[agent] → total points earned across all matches
        self.tournament_scores: dict[Agent, int] = {a: 0 for a in agents}

        # Full log: list of dicts, one per match
        self.match_log: list[dict] = []

    # ── Public API ────────────────────────────────────────────────────────────

    def run_tournament(self) -> None:
        """Run every unique pairing (including self-play) once."""
        # itertools.combinations gives each unique pair exactly once.
        for agent_a, agent_b in itertools.combinations(self.agents, 2):
            result = self._play_match(agent_a, agent_b)
            self.match_log.append(result)

    def results_table(self) -> List[Tuple[str, int]]:
        """Return a list of (name, tournament_score) sorted by score desc."""
        return sorted(
            [(a.name, self.tournament_scores[a]) for a in self.agents],
            key=lambda x: x[1],
            reverse=True,
        )

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _apply_noise(self, move: str, rng) -> str:
        """
        Stochastic noise layer (Phase 4 feature, harmless at noise=0.0).

        If noise > 0 and the intended move is COOPERATE, there is a
        `noise` probability that it is accidentally transmitted as DEFECT.
        DEFECT is never 'accidentally' turned into COOPERATE — the model
        represents *miscommunication*, not random altruism.
        """
        import random
        if move == COOPERATE and random.random() < self.noise:
            return DEFECT
        return move

    def _play_match(self, a: Agent, b: Agent) -> dict:
        """
        Run one head-to-head match of `rounds_per_match` rounds.
        Returns a summary dict for logging/display.
        """
        import random
        rng = random  # pass-through; noise uses module-level random

        a.reset()
        b.reset()

        round_details: list[dict] = []

        for _ in range(self.rounds_per_match):
            # 1. Each agent decides their *intended* move
            intent_a = a.choose_move()
            intent_b = b.choose_move()

            # 2. Apply noise (no-op when self.noise == 0.0)
            actual_a = self._apply_noise(intent_a, rng)
            actual_b = self._apply_noise(intent_b, rng)

            # 3. Look up payoffs
            pts_a, pts_b = _PAYOFF[(actual_a, actual_b)]

            # 4. Record the round for both agents
            #    Note: each agent sees the *actual* (possibly noisy) move
            a.record_round(actual_a, actual_b, pts_a)
            b.record_round(actual_b, actual_a, pts_b)

            round_details.append({
                "move_a": actual_a, "move_b": actual_b,
                "pts_a":  pts_a,    "pts_b":  pts_b,
            })

        # 5. Accumulate tournament scores
        self.tournament_scores[a] += a.score
        self.tournament_scores[b] += b.score

        return {
            "agent_a":  a.name,
            "agent_b":  b.name,
            "score_a":  a.score,
            "score_b":  b.score,
            "rounds":   round_details,
        }
