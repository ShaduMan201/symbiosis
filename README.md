# Symbiosis: The Iterated Prisoner's Dilemma

Welcome to **Symbiosis**, an interactive evolutionary experiment decoding the mathematical basis of trust. This project explores the Prisoner's Dilemma through a robust simulation engine featuring various strategic archetypes that compete in evolving tournament environments.

## Overview

The iterated Prisoner's Dilemma illustrates why individuals might not mutually cooperate, even when it appears in their best interest to do so. In this simulation, different computational "agents" represent varying behavioral strategies. These agents play iterated matches to accumulate points, evolving across generations.

The project is structured in escalating phases:
* **Phase 1: Simulation Engine** (`engine.py`) - The core mechanism for orchestrating head-to-head match-ups and round-robin tournaments.
* **Phase 2: Roster & Verification** (`agents.py` & `main.py`) - Implementation of 10 classic game-theory archetypes and terminal-based verification tournaments.
* **Phase 3 & 4: Interactive UI** (`visualization.py`) - A polished Pygame interface featuring a 1v1 Faceoff mode and an evolutionary Tournament mode with Noise injection.
* **Phase 5: Batch Experiments** (`batch.py`) - Headless data export running thousands of generational simulations, analyzing how population demographics evolve.

## Strategies

The simulation includes a diverse roster of 10 primary evolutionary strategies, along with pure baseline strategies:

1. **Always Cooperate (The Dove):** Unconditionally cooperative.
2. **Always Defect (The Hawk):** Unconditionally predatory.
3. **Tit-for-Tat:** Starts nice, mirrors opponent's last move.
4. **Grudger (Grim Trigger):** Cooperates until betrayed, then defects forever.
5. **Pavlov (Win-Stay, Lose-Shift):** Repeats last move if payoff was good; switches otherwise.
6. **Generous Tit-for-Tat:** Like Tit-for-Tat, but stochastically forgives 10% of defections.
7. **Tit-for-Two-Tats:** Only retaliates after two consecutive defections. Highly tolerant.
8. **Suspicious Tit-for-Tat:** Identical to Tit-for-Tat but opens with defection.
9. **Detective:** Probes the opponent with a [C, D, C, C] sequence, then exploits or mimics based on the opponent's response.
10. **Gradual:** Retaliates repeatedly in proportion to opponent's total defections in the match.
11. **Soft Majority:** Cooperates if the opponent's historical cooperation rate is ≥ 50%.
12. **Random:** Flips a coin for every move.

## Setup & Dependencies

* Python 3.9+
* `pygame` for the graphical interface (`visualization.py`).

Install requirements using `pip`:
```bash
pip install pygame
```

## Running the Simulation

You can run the different phases of the simulation using the following entry points:

### 1. Verification Tournament (CLI)
To run a headless round-robin tournament displaying leaderboards and analytical behavioral checks, run:
```bash
python main.py
```

### 2. Interactive Graphical User Interface (Pygame)
To launch the visual simulation with interactive Faceoff and Evolutionary Tournament modes:
```bash
python visualization.py
```
* **Faceoff Mode:** Pit any two agents against each other to visualize their strategies interactively.
* **Tournament Mode:** Initialize a population of agents, apply miscommunication constraints (`Noise`), and watch the demographics evolve across generations.

### 3. Batch headless experiment
To export rigorous simulation data via headless execution (simulating thousands of generational cycles):
```bash
python batch.py
```
This generates a `symbiosis_batch_results.csv` logging the average final populations for each agent type over 1,000 runs.

## Real-World Impact
To understand how these mathematical strategies apply to tangible concepts in nature, economics, and diplomacy, see the documentation in `real_world_impact.md`.
