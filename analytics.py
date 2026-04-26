"""
analytics.py
================================
Provides EvolutionTracker for generating tournament analytics:
- Head-to-Head Matrix
- Rank Progression
- Trend Analysis
"""

class EvolutionTracker:
    def __init__(self, agent_names):
        self.agent_names = agent_names
        self.evolution_history = {name: [] for name in agent_names}
        self.previous_ranking = {}

    def process_generation(self, generation_index, match_log, results_table):
        # 1. Print Head-to-Head
        self._print_head_to_head_matrix(generation_index, match_log)
        
        # 2. Compute current ranking 
        # results_table is a list of (name, points) sorted descending by points
        current_ranking = {name: rank for rank, (name, _) in enumerate(results_table, start=1)}
        
        # 3. Print Generation Evolution
        self._print_generation_evolution(generation_index, current_ranking)
        
        # 4. Update History
        for name, points in results_table:
            self.evolution_history[name].append(points)
            
        self.previous_ranking = current_ranking

    def _print_head_to_head_matrix(self, generation_index, match_log):
        print(f"\nHEAD-TO-HEAD MATRIX (Tournament {generation_index})")
        
        # Compute the scores in a 2D dict
        matrix = {a: {b: "-" for b in self.agent_names} for a in self.agent_names}
        row_sums = {a: 0 for a in self.agent_names}
        
        for m in match_log:
            a, b = m["agent_a"], m["agent_b"]
            sa, sb = m["score_a"], m["score_b"]
            # Assign if they are distinct or if self-play is allowed (assuming not '-' if they played)
            matrix[a][b] = sa
            matrix[b][a] = sb
            row_sums[a] += sa
            row_sums[b] += sb
            
        # Optional formatting: align columns
        col_width = 6
        header = "".ljust(22) + "".join([b[:col_width].ljust(col_width) for b in self.agent_names]) + " | Total"
        print(header)
        print("-" * len(header))
        
        for a in self.agent_names:
            row_str = f"{a:<22}"
            for b in self.agent_names:
                val = matrix[a][b]
                val_str = str(val) if val != "-" else "-"
                row_str += val_str.ljust(col_width)
            row_str += f" | {row_sums[a]}"
            print(row_str)

    def _print_generation_evolution(self, generation_index, current_ranking):
        if generation_index == 1:
            # No previous generation to compare to
            print(f"\nGENERATION EVOLUTION REPORT (Gen 1 baseline)")
            for name, rank in sorted(current_ranking.items(), key=lambda x: x[1]):
                print(f"{name:<22} Rank {rank}")
            return
            
        print(f"\nGENERATION EVOLUTION REPORT (Gen {generation_index - 1} → Gen {generation_index})")
        
        # Sort by current rank for clean output
        for name, current_rank in sorted(current_ranking.items(), key=lambda x: x[1]):
            previous_rank = self.previous_ranking.get(name, current_rank)
            
            if current_rank < previous_rank:
                diff = previous_rank - current_rank
                print(f"{name:<22} 🟢 ↑ +{diff} (improved)")
            elif current_rank > previous_rank:
                diff = current_rank - previous_rank
                print(f"{name:<22} 🔴 ↓ -{diff} (declined)")
            else:
                print(f"{name:<22} 🟡 → (stable)")

    def print_evolution_trends(self):
        print("\nEVOLUTION TRENDS (All Generations)")
        
        for name in self.agent_names:
            history = self.evolution_history[name]
            if not history:
                continue
                
            first_score = history[0]
            last_score = history[-1]
            trend = last_score - first_score
            
            if trend > 0:
                print(f"{name:<22} 📈 +{trend} ({first_score} → {last_score})")
            elif trend < 0:
                print(f"{name:<22} 📉 {trend} ({first_score} → {last_score})")
            else:
                print(f"{name:<22} ➖ stable")
