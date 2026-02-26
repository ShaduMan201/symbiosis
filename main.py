"""
main.py — Phase 2 verification
================================
Runs a round-robin tournament with all 10 strategies and prints
a ranked leaderboard plus per-match results so you can verify
each strategy behaves as designed.
"""

from agents import (
    AlwaysCooperate, AlwaysDefect,
    TitForTat, Grudger, Pavlov, GenerousTitForTat,
    TitForTwoTats, SuspiciousTitForTat, Detective,
    Gradual, SoftMajority, Random,
    REWARD, TEMPTATION, SUCKER, PUNISHMENT,
)
from engine import Simulation

ROUNDS = 200


def divider(char="═", width=65):
    print(char * width)


def main():
    divider()
    print("  SYMBIOSIS — Iterated Prisoner's Dilemma  |  Phase 2")
    divider()
    print(f"  Payoff Matrix  →  R={REWARD}  T={TEMPTATION}  S={SUCKER}  P={PUNISHMENT}")
    print(f"  Rounds per match : {ROUNDS}")
    print(f"  Noise            : 0 % (clean)")
    divider()

    agents = [
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
        AlwaysCooperate(),
        AlwaysDefect(),
    ]

    sim = Simulation(agents, rounds_per_match=ROUNDS, noise=0.0)
    sim.run_tournament()

    # ── Match-by-match table ─────────────────────────────────────────────────
    print("\n  MATCH RESULTS (score_a | score_b)")
    divider("─")
    for m in sim.match_log:
        a, b   = m["agent_a"], m["agent_b"]
        sa, sb = m["score_a"], m["score_b"]
        winner = "TIE" if sa == sb else (a if sa > sb else b)
        print(f"  {a:<22} vs {b:<22}  {sa:>5} | {sb:>5}   [{winner}]")

    # ── Leaderboard ──────────────────────────────────────────────────────────
    print("\n  TOURNAMENT LEADERBOARD")
    divider("─")
    max_pts = sim.results_table()[0][1]
    for rank, (name, total) in enumerate(sim.results_table(), start=1):
        bar = "█" * int(30 * total / max_pts)
        print(f"  #{rank:<2} {name:<22} {total:>6} pts  {bar}")

    # ── Key behavioral checks ────────────────────────────────────────────────
    print("\n  BEHAVIORAL SPOT-CHECKS")
    divider("─")

    scores = {m["agent_a"]: m["score_a"] for m in sim.match_log}
    scores.update({m["agent_b"]: m["score_b"] for m in sim.match_log})

    for m in sim.match_log:
        a, b = m["agent_a"], m["agent_b"]
        sa, sb = m["score_a"], m["score_b"]

        # TfT vs Cooperate → should both get REWARD * ROUNDS
        if a == "Tit-for-Tat" and b == "Always Cooperate":
            exp = REWARD * ROUNDS
            ok  = sa == exp and sb == exp
            print(f"  {'✓' if ok else '✗'}  TfT vs Cooperate  → both should earn {exp}  got ({sa},{sb})")

        # Grudger vs Defect → Grudger defects from round 2 → both get P = 1 except round 1
        if a == "Grudger" and b == "Always Defect":
            # Round 1: Grudger=C, Defect=D → (S=0, T=5). Rounds 2-200: both D → P=1 each
            exp_grudger = SUCKER + PUNISHMENT * (ROUNDS - 1)
            ok = sa == exp_grudger
            print(f"  {'✓' if ok else '✗'}  Grudger vs Defect → Grudger should earn {exp_grudger}  got {sa}")

        # Detective vs Cooperate → Detective exploits after round 4
        if a == "Detective" and b == "Always Cooperate":
            # Rounds 1-4: probe [C,D,C,C], then always D
            # Probe pts: C/C=3, D/C=5, C/C=3, C/C=3 → 14 pts in 4 rounds
            # Rounds 5-200: D vs C each = T=5  → 196 * 5 = 980
            exp_det = 14 + TEMPTATION * (ROUNDS - 4)
            ok = sa == exp_det
            print(f"  {'✓' if ok else '✗'}  Detective vs Coop → Detective should earn {exp_det}  got {sa}")

    divider()
    print("  Phase 2 complete. ✓")
    divider()


if __name__ == "__main__":
    main()
