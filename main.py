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
from analytics import EvolutionTracker

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
        TitForTat(), Grudger(), Pavlov(), GenerousTitForTat(),
        TitForTwoTats(), SuspiciousTitForTat(), Detective(),
        Gradual(), SoftMajority(), Random(), AlwaysCooperate(), AlwaysDefect()
    ]
    agent_names = [a.name for a in agents]
    tracker = EvolutionTracker(agent_names)

    NUM_GENERATIONS = 5

    for gen in range(1, NUM_GENERATIONS + 1):
        # Use a tiny bit of noise after gen 1 to see rank changes
        noise_level = 0.0 if gen == 1 else 0.05
        sim = Simulation(agents, rounds_per_match=ROUNDS, noise=noise_level)
        sim.run_tournament()

        if gen == 1:
            # ── Match-by-match table ─────────────────────────────────────────────────
            print("\n  MATCH RESULTS (score_a | score_b) - Gen 1")
            divider("─")
            for m in sim.match_log:
                a, b   = m["agent_a"], m["agent_b"]
                sa, sb = m["score_a"], m["score_b"]
                winner = "TIE" if sa == sb else (a if sa > sb else b)
                print(f"  {a:<22} vs {b:<22}  {sa:>5} | {sb:>5}   [{winner}]")

            # ── Key behavioral checks ────────────────────────────────────────────────
            print("\n  BEHAVIORAL SPOT-CHECKS (Gen 1)")
            divider("─")
            for m in sim.match_log:
                a, b = m["agent_a"], m["agent_b"]
                sa, sb = m["score_a"], m["score_b"]

                if a == "Tit-for-Tat" and b == "Always Cooperate":
                    exp = REWARD * ROUNDS
                    ok  = sa == exp and sb == exp
                    print(f"  {'✓' if ok else '✗'}  TfT vs Cooperate  → both should earn {exp}  got ({sa},{sb})")

                if a == "Grudger" and b == "Always Defect":
                    exp_grudger = SUCKER + PUNISHMENT * (ROUNDS - 1)
                    ok = sa == exp_grudger
                    print(f"  {'✓' if ok else '✗'}  Grudger vs Defect → Grudger should earn {exp_grudger}  got {sa}")

                if a == "Detective" and b == "Always Cooperate":
                    exp_det = 14 + TEMPTATION * (ROUNDS - 4)
                    ok = sa == exp_det
                    print(f"  {'✓' if ok else '✗'}  Detective vs Coop → Detective should earn {exp_det}  got {sa}")

        # Feed the generation into our analytics tracker
        tracker.process_generation(gen, sim.match_log, sim.results_table())

    # Finally, print the evolution trends
    tracker.print_evolution_trends()

    divider()
    print("  Analytics test complete. ✓")
    divider()


if __name__ == "__main__":
    main()
