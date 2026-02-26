"""
agents.py — Phase 2: All 10 Strategic Archetypes
=================================================
An expanding roster of Agent subclasses.  Each new strategy
IS-A Agent and lives cleanly in this file so you can add more
any time by just subclassing Agent and implementing choose_move().

Payoff constants (imported wherever needed)
-------------------------------------------
  REWARD     = 3  (mutual cooperation)
  TEMPTATION = 5  (unilateral defection)
  SUCKER     = 0  (being exploited)
  PUNISHMENT = 1  (mutual defection)
"""

from abc import ABC, abstractmethod
import random


# ── Payoff Matrix ────────────────────────────────────────────────────────────
REWARD      = 3
TEMPTATION  = 5
SUCKER      = 0
PUNISHMENT  = 1

COOPERATE = "C"
DEFECT    = "D"


# ── Base Agent ───────────────────────────────────────────────────────────────

class Agent(ABC):
    """
    Abstract base for every strategy.

    State available to strategies
    ------------------------------
    self.my_history  – list of this agent's own *actual* moves (oldest first)
    self.opp_history – list of the opponent's *actual* moves (oldest first)
    self.score       – cumulative points in the current match
    """

    def __init__(self, name: str, color: tuple = (200, 200, 200)):
        self.name        = name
        self.color       = color   # RGB, used by Pygame in Phase 3
        self.score       = 0
        self.my_history  : list[str] = []
        self.opp_history : list[str] = []

    @abstractmethod
    def choose_move(self) -> str:
        ...

    def record_round(self, my_move: str, opp_move: str, points: int) -> None:
        self.my_history.append(my_move)
        self.opp_history.append(opp_move)
        self.score += points

    def reset(self) -> None:
        self.score       = 0
        self.my_history  = []
        self.opp_history = []

    def __repr__(self) -> str:
        return f"<{self.name} | score={self.score}>"


# ══════════════════════════════════════════════════════════════════════════════
#  Phase 1 Baseline Strategies (kept here for the full tournament in Phase 3+)
# ══════════════════════════════════════════════════════════════════════════════

class AlwaysCooperate(Agent):
    """The Dove — cooperates unconditionally."""
    def __init__(self):
        super().__init__("Always Cooperate", color=(52, 211, 153))   # emerald

    def choose_move(self) -> str:
        return COOPERATE


class AlwaysDefect(Agent):
    """The Hawk — defects unconditionally."""
    def __init__(self):
        super().__init__("Always Defect", color=(239, 68, 68))       # red

    def choose_move(self) -> str:
        return DEFECT


# ══════════════════════════════════════════════════════════════════════════════
#  Phase 2: The 10 Strategic Archetypes
# ══════════════════════════════════════════════════════════════════════════════

class TitForTat(Agent):
    """
    Strategy 1 — Tit-for-Tat
    ─────────────────────────
    The classic 'nice, retaliatory, forgiving' strategy by Axelrod.
    • Round 1 : Cooperate (always start nice).
    • Round N : Mirror the opponent's previous move exactly.

    Why it works: rewards cooperation and punishes defection immediately,
    but forgives after one round of retaliation.
    """
    def __init__(self):
        super().__init__("Tit-for-Tat", color=(96, 165, 250))       # blue

    def choose_move(self) -> str:
        if not self.opp_history:
            return COOPERATE
        return self.opp_history[-1]


class Grudger(Agent):
    """
    Strategy 2 — The Grudger (Grim Trigger)
    ────────────────────────────────────────
    Cooperates until the opponent defects even once, then defects
    forever — no forgiveness.

    Demonstrates the darkest side of reciprocity: one mistake ends
    the relationship permanently (relevant in trust/business contexts).
    """
    def __init__(self):
        super().__init__("Grudger", color=(168, 85, 247))            # purple

    def choose_move(self) -> str:
        if DEFECT in self.opp_history:
            return DEFECT
        return COOPERATE


class Pavlov(Agent):
    """
    Strategy 3 — Pavlov (Win-Stay, Lose-Shift)
    ───────────────────────────────────────────
    • If the last round's payoff was 'good' (R or T) → repeat the move.
    • If the last round's payoff was 'bad'  (S or P) → switch.
    • Round 1: Cooperate.

    'Good' is defined as earning ≥ REWARD (3 pts). This makes Pavlov
    self-correcting: it bails out of mutual defection quickly.
    """
    def __init__(self):
        super().__init__("Pavlov", color=(251, 191, 36))             # amber

    def choose_move(self) -> str:
        if not self.my_history:
            return COOPERATE
        last_pts = REWARD  # default neutral
        last_my  = self.my_history[-1]
        last_opp = self.opp_history[-1]
        if   (last_my, last_opp) == (COOPERATE, COOPERATE): last_pts = REWARD
        elif (last_my, last_opp) == (DEFECT,    COOPERATE): last_pts = TEMPTATION
        elif (last_my, last_opp) == (COOPERATE, DEFECT):    last_pts = SUCKER
        else:                                                last_pts = PUNISHMENT
        # Win-stay
        if last_pts >= REWARD:
            return last_my
        # Lose-shift
        return DEFECT if last_my == COOPERATE else COOPERATE


class GenerousTitForTat(Agent):
    """
    Strategy 4 — Generous Tit-for-Tat
    ────────────────────────────────────
    Like Tit-for-Tat but with a 10 % probability of forgiving a
    defection (playing C instead of D).

    Stochastic element: breaks the vicious cycle of mutual retaliation
    that pure TfT can fall into after a noise-induced defection.
    Parameter `forgiveness` is exposed so it can be tuned via the
    Phase 4 UI without touching business logic.
    """
    def __init__(self, forgiveness: float = 0.10):
        super().__init__("Generous TfT", color=(34, 211, 238))       # cyan
        self.forgiveness = forgiveness

    def choose_move(self) -> str:
        if not self.opp_history:
            return COOPERATE
        if self.opp_history[-1] == DEFECT:
            # Probabilistic forgiveness — stochastic element ★
            return COOPERATE if random.random() < self.forgiveness else DEFECT
        return COOPERATE


class TitForTwoTats(Agent):
    """
    Strategy 5 — Tit-for-Two-Tats
    ──────────────────────────────
    Only retaliates after TWO consecutive opponent defections.
    More tolerant than TfT; less exploitable than Always Cooperate.
    Excellent under noisy conditions (Phase 4) because a single
    accidental defection doesn't trigger retaliation.
    """
    def __init__(self):
        super().__init__("Tit-for-Two-Tats", color=(52, 211, 153))   # teal

    def choose_move(self) -> str:
        if len(self.opp_history) >= 2:
            if self.opp_history[-1] == DEFECT and self.opp_history[-2] == DEFECT:
                return DEFECT
        return COOPERATE


class SuspiciousTitForTat(Agent):
    """
    Strategy 6 — Suspicious Tit-for-Tat
    ─────────────────────────────────────
    Identical to TfT except it opens with a DEFECT (i.e., it doesn't
    extend unconditional trust on round 1).

    Earns an extra point if the opponent cooperates on round 1, but
    risks triggering a retaliatory spiral against other TfT variants.
    """
    def __init__(self):
        super().__init__("Suspicious TfT", color=(249, 115, 22))     # orange

    def choose_move(self) -> str:
        if not self.opp_history:
            return DEFECT                   # opens with suspicion
        return self.opp_history[-1]


class Detective(Agent):
    """
    Strategy 7 — The Detective
    ──────────────────────────
    Plays a fixed probe sequence [C, D, C, C] in rounds 1-4.
    Analyses the opponent's response:
    • If the opponent NEVER retaliated (cooperated throughout) →
      switch to Always Defect (exploitation mode).
    • Otherwise → switch to Tit-for-Tat (safe mode).

    After the probe phase, applies the chosen meta-strategy.
    """

    _PROBE = [COOPERATE, DEFECT, COOPERATE, COOPERATE]   # 4-round sequence

    def __init__(self):
        super().__init__("Detective", color=(148, 163, 184))         # slate

    def choose_move(self) -> str:
        r = len(self.my_history)

        # ── Probe phase (rounds 0-3) ─────────────────────────────────────
        if r < len(self._PROBE):
            return self._PROBE[r]

        # ── Analysis: did the opponent ever retaliate? ───────────────────
        probe_opp = self.opp_history[:len(self._PROBE)]
        opponent_is_pushover = DEFECT not in probe_opp

        # ── Exploitation / mimicry ───────────────────────────────────────
        if opponent_is_pushover:
            return DEFECT                   # never punished us → exploit
        else:
            return self.opp_history[-1]     # behave like TfT


class Gradual(Agent):
    """
    Strategy 8 — Gradual
    ─────────────────────
    Escalates punishment in proportion to how many times the opponent
    has defected:
    • After each new opponent defection, schedule N more retaliatory
      defections (where N = total opponent defections so far).
    • Once punishment is served, cooperate for 2 'calm-down' rounds,
      then resume cooperation.

    Models proportional justice — punishment fits the crime.
    """
    def __init__(self):
        super().__init__("Gradual", color=(20, 184, 166))            # teal-600
        self._punishment_remaining = 0
        self._calm_remaining       = 0
        self._prev_opp_defects     = 0   # tracks total observed defections

    def reset(self) -> None:
        super().reset()
        self._punishment_remaining = 0
        self._calm_remaining       = 0
        self._prev_opp_defects     = 0

    def choose_move(self) -> str:
        if self.opp_history:
            total_opp_defects = self.opp_history.count(DEFECT)
            new_defects = total_opp_defects - self._prev_opp_defects
            if new_defects > 0:
                # New defection(s) detected → schedule proportional punishment
                self._punishment_remaining += total_opp_defects
                self._calm_remaining        = 2
                self._prev_opp_defects      = total_opp_defects

        if self._punishment_remaining > 0:
            self._punishment_remaining -= 1
            return DEFECT

        if self._calm_remaining > 0:
            self._calm_remaining -= 1
            return COOPERATE               # calm-down phase

        return COOPERATE


class SoftMajority(Agent):
    """
    Strategy 9 — Soft Majority
    ───────────────────────────
    Cooperates if the opponent's historical cooperation rate is ≥ 50 %.
    Defects otherwise.

    Round 1: Cooperate (ties go to cooperation = 'soft').
    Uses a continuous proportion rather than a binary threshold,
    making it naturally adaptive to the opponent's behaviour over time.
    """
    def __init__(self):
        super().__init__("Soft Majority", color=(163, 230, 53))      # lime

    def choose_move(self) -> str:
        if not self.opp_history:
            return COOPERATE
        coop_rate = self.opp_history.count(COOPERATE) / len(self.opp_history)
        return COOPERATE if coop_rate >= 0.5 else DEFECT


class Random(Agent):
    """
    Strategy 10 — Random
    ─────────────────────
    Flips a fair coin for every move — pure stochastic behaviour.
    `p_cooperate` is exposed so Phase 4 UI can bias the coin.

    Serves as a probabilistic baseline and represents chaotic / 
    irrational actors in the population.
    """
    def __init__(self, p_cooperate: float = 0.5):
        super().__init__("Random", color=(245, 158, 11))             # yellow
        self.p_cooperate = p_cooperate

    def choose_move(self) -> str:
        return COOPERATE if random.random() < self.p_cooperate else DEFECT


# ── Convenience: full roster for Phase 3+ ────────────────────────────────────
def default_roster() -> list[Agent]:
    """Return one fresh instance of every Phase 2 strategy."""
    return [
        TitForTat(),
        Grudger(),
        Pavlov(),
        GenerousTitForTat(),
        TitForTwoTats(),
        SuspiciousTitForTat(),
        Detective(),
        Gradual(),
        SoftMajority(),
        Random(),
    ]
