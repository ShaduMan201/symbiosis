"""
batch.py — Phase 5: Exporting Data from 1,000 Headless Experiments
==================================================================
Runs 1,000 separate simulations without visuals. Each simulation runs
for 50 generations of 200 rounds, and then we record the final 
population distribution of strategies. The average final totals are
then exported to a CSV file.
"""

import csv
import random
from statistics import mean
from collections import defaultdict

from agents import (
    TitForTat, Grudger, Pavlov, GenerousTitForTat, TitForTwoTats,
    SuspiciousTitForTat, Detective, Gradual, SoftMajority, AlwaysCooperate, AlwaysDefect,
    COOPERATE, DEFECT, REWARD, TEMPTATION, SUCKER, PUNISHMENT,
)
from agents import Random as RandomBot

# Setup
N_RUNS = 1000
GENS_PER_RUN = 50
ROUNDS_PER_GEN = 200
NOISE_RATE = 0.05       # 5% baseline
MUTATION_RATE = 0.02    # 2% baseline
CSV_FILE = "symbiosis_batch_results.csv"

STRAT_MK = [
    TitForTat, Grudger, Pavlov, GenerousTitForTat, TitForTwoTats,
    SuspiciousTitForTat, Detective, Gradual, SoftMajority, RandomBot
]

_PAY = {
    (COOPERATE, COOPERATE): (REWARD, REWARD),
    (COOPERATE, DEFECT): (SUCKER, TEMPTATION),
    (DEFECT, COOPERATE): (TEMPTATION, SUCKER),
    (DEFECT, DEFECT): (PUNISHMENT, PUNISHMENT),
}

class AgentWrapper:
    def __init__(self, cls):
        self.cls = cls
        self.agent = cls()
        self.score = 0
        
def run_simulation() -> dict:
    """Run one single full multi-generational simulation."""
    # Build initial population (5 per strategy = 50 total)
    population = []
    for cls in STRAT_MK:
        for _ in range(5):
            population.append(AgentWrapper(cls))
            
    for _ in range(GENS_PER_RUN):
        # Assign pairs
        random.shuffle(population)
        
        # 200 rounds per generation
        for r_idx in range(ROUNDS_PER_GEN):
            for i in range(0, 50, 2):
                a = population[i]
                b = population[i+1]
                
                if r_idx == 0:
                    a.agent.reset()
                    b.agent.reset()
                
                ia, ib = a.agent.choose_move(), b.agent.choose_move()
                # Apply noise
                act_a = DEFECT if (ia == COOPERATE and random.random() < NOISE_RATE) else ia
                act_b = DEFECT if (ib == COOPERATE and random.random() < NOISE_RATE) else ib
                
                pa, pb = _PAY[(act_a, act_b)]
                a.agent.record_round(act_a, act_b, pa)
                b.agent.record_round(act_b, act_a, pb)
                a.score += pa
                b.score += pb
                
        # Evolution End of Gen
        population.sort(key=lambda w: w.score)
        bot_5 = population[:5]
        top_5 = population[-5:]
        
        for i in range(5):
            dead, parent = bot_5[i], top_5[i]
            if random.random() < MUTATION_RATE:
                new_cls = random.choice(STRAT_MK)
            else:
                new_cls = parent.cls
                
            dead.cls = new_cls
            dead.agent = new_cls()
            
        for w in population:
            w.score = 0

    # Final tally
    final_counts = defaultdict(int)
    for w in population:
        final_counts[w.cls.__name__] += 1
    return final_counts

def main():
    print(f"Starting batch simulation... ({N_RUNS} runs, {GENS_PER_RUN} generations/run)")
    print(f"Noise level: {NOISE_RATE*100}%, Mutation rate: {MUTATION_RATE*100}%")
    print("This may take a minute...\n")

    history = {cls.__name__: [] for cls in STRAT_MK}
    
    for i in range(N_RUNS):
        res = run_simulation()
        for strategy_name in history.keys():
            history[strategy_name].append(res.get(strategy_name, 0))
            
        if (i+1) % 100 == 0:
            print(f"Completed {i+1} runs...")

    # Averages
    print(f"\nWriting to {CSV_FILE}...")
    with open(CSV_FILE, mode="w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Strategy", "Average Final Population (50 Max)", "Min Pop", "Max Pop"])
        
        # Sort by best average performance
        avg_results = [(name, mean(counts), min(counts), max(counts)) for name, counts in history.items()]
        avg_results.sort(key=lambda x: x[1], reverse=True)
        
        for name, avg, mmin, mmax in avg_results:
            writer.writerow([name, f"{avg:.2f}", mmin, mmax])
            print(f"  {name:<20}: {avg:.1f}")
            
    print("\nBatch Mode complete! ✓")

if __name__ == "__main__":
    main()
