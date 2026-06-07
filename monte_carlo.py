"""
Monte Carlo Tournament Simulator — FIFA World Cup 2026
=======================================================
Simulates the complete WC 2026 tournament:
  - 12 groups of 4 teams (3 matches per team)
  - Top 2 per group + 8 best 3rd-placed teams → Round of 32
  - Knockout: R32 → R16 → QF → SF → Final

Each match: sample goals from Poisson(λ_A) and Poisson(λ_B)
where λ comes from the Neural Poisson model.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Callable, Optional
from collections import defaultdict
from dataclasses import dataclass, field
import json


# ─── WC 2026 GROUPS ─────────────────────────────────────────────────────────

GROUPS = {
    'A': ['Mexico', 'South Africa', 'South Korea', 'Czech Republic'],
    'B': ['Canada', 'Bosnia and Herzegovina', 'Qatar', 'Switzerland'],
    'C': ['Brazil', 'Morocco', 'Haiti', 'Scotland'],
    'D': ['United States', 'Paraguay', 'Australia', 'Turkey'],
    'E': ['Germany', 'Curaçao', 'Ivory Coast', 'Ecuador'],
    'F': ['Netherlands', 'Japan', 'Sweden', 'Tunisia'],
    'G': ['Belgium', 'Egypt', 'Iran', 'New Zealand'],
    'H': ['Spain', 'Cape Verde', 'Saudi Arabia', 'Uruguay'],
    'I': ['France', 'Senegal', 'Iraq', 'Norway'],
    'J': ['Argentina', 'Algeria', 'Austria', 'Jordan'],
    'K': ['Portugal', 'DR Congo', 'Uzbekistan', 'Colombia'],
    'L': ['England', 'Croatia', 'Ghana', 'Panama'],
}

# FIFA's bracket structure for R32 (based on group positions)
# Format: (group_position, group_letter)
# The bracket is designed so top-ranked teams are on opposite sides
# Pathway 1: Groups A-F winners/runners-up + 3rd place teams
# Pathway 2: Groups G-L winners/runners-up + 3rd place teams

R32_MATCHUPS = [
    # Pathway 1 (left bracket)
    ('A1', '3rd_ABCD_1'),   # Group A winner vs best 3rd
    ('B1', '3rd_ABCD_2'),   # Group B winner vs 2nd best 3rd
    ('C1', 'C2_vs_D2_w'),   # Simplified: Group C winner
    ('D1', 'D2_vs_C2_w'),   # Group D winner
    ('E1', '3rd_EFGH_1'),   # Group E winner vs 3rd
    ('F1', '3rd_EFGH_2'),   # Group F winner vs 3rd
    # Pathway 2 (right bracket)
    ('G1', '3rd_GHIJ_1'),
    ('H1', '3rd_GHIJ_2'),
    ('I1', '3rd_IJKL_1'),
    ('J1', '3rd_IJKL_2'),
    ('K1', '3rd_KLEF_1'),
    ('L1', '3rd_KLEF_2'),
]

# Simplified bracket pairings for R32
# Each tuple: (team_slot_1, team_slot_2)
# Where slot format is "GroupLetter_Position" e.g., "A_1" = Group A winner


@dataclass
class MatchResult:
    team_a: str
    team_b: str
    goals_a: int
    goals_b: int
    lambda_a: float
    lambda_b: float
    stage: str
    penalties: bool = False
    
    @property
    def winner(self) -> str:
        if self.goals_a > self.goals_b:
            return self.team_a
        elif self.goals_b > self.goals_a:
            return self.team_b
        return 'draw'


@dataclass
class GroupStanding:
    team: str
    points: int = 0
    gf: int = 0
    ga: int = 0
    gd: int = 0
    wins: int = 0
    draws: int = 0
    losses: int = 0
    played: int = 0


@dataclass
class SimulationResult:
    champion: str
    finalist: str
    semifinalists: List[str]
    quarterfinalists: List[str]
    r16_teams: List[str]
    r32_teams: List[str]
    group_results: Dict[str, List[MatchResult]]
    knockout_results: List[MatchResult]
    group_standings: Dict[str, List[GroupStanding]]


class TournamentSimulator:
    """
    Monte Carlo simulator for FIFA World Cup 2026.
    
    Uses a match prediction function (either Neural Poisson or Elo baseline)
    to generate λ values, then samples goals from Poisson distributions.
    """

    def __init__(self, predict_fn: Callable, seed: int = None):
        """
        Args:
            predict_fn: Function(team_a, team_b, stage) -> (lambda_a, lambda_b)
            seed: Random seed for reproducibility
        """
        self.predict_fn = predict_fn
        self.rng = np.random.RandomState(seed)

    def simulate_match(self, team_a: str, team_b: str,
                       stage: str = 'group',
                       allow_draw: bool = True) -> MatchResult:
        """
        Simulate a single match.
        
        For knockout matches (allow_draw=False), if drawn after 90min,
        simulate extra time, then penalties.
        """
        lambda_a, lambda_b = self.predict_fn(team_a, team_b, stage)
        
        goals_a = self.rng.poisson(lambda_a)
        goals_b = self.rng.poisson(lambda_b)
        
        penalties = False
        
        if not allow_draw and goals_a == goals_b:
            # Extra time: ~1/3 of normal match intensity
            et_goals_a = self.rng.poisson(lambda_a * 0.33)
            et_goals_b = self.rng.poisson(lambda_b * 0.33)
            goals_a += et_goals_a
            goals_b += et_goals_b
            
            if goals_a == goals_b:
                # Penalties: ~50/50 with slight advantage to "better" team
                p_a = 0.5 + 0.05 * np.sign(lambda_a - lambda_b)
                if self.rng.random() < p_a:
                    goals_a += 1
                else:
                    goals_b += 1
                penalties = True
        
        return MatchResult(
            team_a=team_a, team_b=team_b,
            goals_a=int(goals_a), goals_b=int(goals_b),
            lambda_a=lambda_a, lambda_b=lambda_b,
            stage=stage, penalties=penalties
        )

    def simulate_group(self, group_name: str,
                       teams: List[str]) -> Tuple[List[GroupStanding], List[MatchResult]]:
        """
        Simulate all matches in a group and return standings.
        
        Each team plays every other team once (6 matches per group).
        """
        standings = {team: GroupStanding(team=team) for team in teams}
        matches = []
        
        # Round-robin: each pair plays once
        for i in range(len(teams)):
            for j in range(i + 1, len(teams)):
                result = self.simulate_match(teams[i], teams[j], stage='group')
                matches.append(result)
                
                # Update standings
                sa, sb = standings[teams[i]], standings[teams[j]]
                sa.played += 1
                sb.played += 1
                sa.gf += result.goals_a
                sa.ga += result.goals_b
                sb.gf += result.goals_b
                sb.ga += result.goals_a
                
                if result.goals_a > result.goals_b:
                    sa.points += 3
                    sa.wins += 1
                    sb.losses += 1
                elif result.goals_a < result.goals_b:
                    sb.points += 3
                    sb.wins += 1
                    sa.losses += 1
                else:
                    sa.points += 1
                    sb.points += 1
                    sa.draws += 1
                    sb.draws += 1
        
        # Update GD
        for s in standings.values():
            s.gd = s.gf - s.ga
        
        # Sort: points → GD → GF → random (simplified tiebreaker)
        sorted_standings = sorted(
            standings.values(),
            key=lambda s: (s.points, s.gd, s.gf, self.rng.random()),
            reverse=True
        )
        
        return sorted_standings, matches

    def get_best_third_placed(self, 
                               all_standings: Dict[str, List[GroupStanding]],
                               n: int = 8) -> List[str]:
        """
        Select the 8 best third-placed teams across all 12 groups.
        
        Ranking: points → GD → GF
        """
        third_placed = []
        for group_name, standings in all_standings.items():
            if len(standings) >= 3:
                third = standings[2]
                third_placed.append((group_name, third))
        
        # Sort by points, then GD, then GF
        third_placed.sort(
            key=lambda x: (x[1].points, x[1].gd, x[1].gf, self.rng.random()),
            reverse=True
        )
        
        return [tp[1].team for tp in third_placed[:n]]

    def simulate_knockout(self, teams_r32: List[str]) -> Tuple[str, str, List[str], List[str], List[str], List[MatchResult]]:
        """
        Simulate the knockout stage: R32 → R16 → QF → SF → Final.
        
        Args:
            teams_r32: 32 teams ordered by bracket position
            
        Returns:
            champion, finalist, semifinalists, quarterfinalists, r16_teams, all_matches
        """
        all_matches = []
        
        # R32: 16 matches (32 → 16)
        r16_teams = []
        for i in range(0, 32, 2):
            result = self.simulate_match(
                teams_r32[i], teams_r32[i + 1],
                stage='R32', allow_draw=False
            )
            all_matches.append(result)
            r16_teams.append(result.winner)
        
        # R16: 8 matches (16 → 8)
        qf_teams = []
        for i in range(0, 16, 2):
            result = self.simulate_match(
                r16_teams[i], r16_teams[i + 1],
                stage='R16', allow_draw=False
            )
            all_matches.append(result)
            qf_teams.append(result.winner)
        
        # QF: 4 matches (8 → 4)
        sf_teams = []
        for i in range(0, 8, 2):
            result = self.simulate_match(
                qf_teams[i], qf_teams[i + 1],
                stage='QF', allow_draw=False
            )
            all_matches.append(result)
            sf_teams.append(result.winner)
        
        # SF: 2 matches (4 → 2)
        finalists = []
        for i in range(0, 4, 2):
            result = self.simulate_match(
                sf_teams[i], sf_teams[i + 1],
                stage='SF', allow_draw=False
            )
            all_matches.append(result)
            finalists.append(result.winner)
        
        # Final
        final = self.simulate_match(
            finalists[0], finalists[1],
            stage='Final', allow_draw=False
        )
        all_matches.append(final)
        
        return (
            final.winner,
            finalists[0] if final.winner == finalists[1] else finalists[1],
            sf_teams,
            qf_teams,
            r16_teams,
            all_matches
        )

    def build_bracket(self, all_standings: Dict[str, List[GroupStanding]],
                      best_thirds: List[str]) -> List[str]:
        """
        Build the R32 bracket from group standings and best third-placed teams.
        
        FIFA's bracket structure ensures top-seeded teams are on opposite sides.
        Simplified version based on the 2026 format.
        """
        bracket = []
        
        # Group winners and runners-up
        group_order = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L']
        
        winners = {g: all_standings[g][0].team for g in group_order}
        runners = {g: all_standings[g][1].team for g in group_order}
        
        # Distribute third-placed teams across the bracket
        thirds = list(best_thirds)
        self.rng.shuffle(thirds)
        
        # Build bracket: winner vs third, runner-up vs runner-up (cross-groups)
        # Simplified FIFA bracket structure
        matchups = [
            # Left half
            (winners['A'], thirds[0] if len(thirds) > 0 else runners['A']),
            (runners['C'], runners['D']),
            (winners['B'], thirds[1] if len(thirds) > 1 else runners['B']),
            (runners['A'], runners['B']),
            (winners['C'], thirds[2] if len(thirds) > 2 else runners['C']),
            (runners['E'], runners['F']),
            (winners['D'], thirds[3] if len(thirds) > 3 else runners['D']),
            (runners['G'], runners['H']),
            # Right half
            (winners['E'], thirds[4] if len(thirds) > 4 else runners['E']),
            (runners['I'], runners['J']),
            (winners['F'], thirds[5] if len(thirds) > 5 else runners['F']),
            (runners['K'], runners['L']),
            (winners['G'], thirds[6] if len(thirds) > 6 else runners['G']),
            (runners['A'], runners['L']),
            (winners['H'], thirds[7] if len(thirds) > 7 else runners['H']),
            (winners['I'], runners['I']),
        ]
        
        # Flatten to list of 32
        for a, b in matchups:
            bracket.extend([a, b])
        
        # Ensure no duplicates (safety check)
        seen = set()
        deduped = []
        for team in bracket:
            if team not in seen:
                deduped.append(team)
                seen.add(team)
        
        # Pad if needed (shouldn't happen with correct logic)
        while len(deduped) < 32:
            for g in group_order:
                for s in all_standings[g]:
                    if s.team not in seen:
                        deduped.append(s.team)
                        seen.add(s.team)
                    if len(deduped) >= 32:
                        break
                if len(deduped) >= 32:
                    break
        
        return deduped[:32]

    def simulate_tournament(self) -> SimulationResult:
        """Simulate one complete FIFA World Cup 2026 tournament."""
        # Phase 1: Group stage
        all_standings = {}
        all_group_results = {}
        
        for group_name, teams in GROUPS.items():
            standings, matches = self.simulate_group(group_name, teams)
            all_standings[group_name] = standings
            all_group_results[group_name] = matches
        
        # Phase 2: Determine R32 teams
        best_thirds = self.get_best_third_placed(all_standings, n=8)
        
        # Phase 3: Build bracket and simulate knockout
        bracket = self.build_bracket(all_standings, best_thirds)
        
        champion, finalist, sf_teams, qf_teams, r16_teams, ko_matches = \
            self.simulate_knockout(bracket)
        
        return SimulationResult(
            champion=champion,
            finalist=finalist,
            semifinalists=sf_teams,
            quarterfinalists=qf_teams,
            r16_teams=r16_teams,
            r32_teams=bracket,
            group_results=all_group_results,
            knockout_results=ko_matches,
            group_standings=all_standings,
        )


def run_monte_carlo(predict_fn: Callable, n_simulations: int = 10000,
                    seed: int = 42, label: str = "Model") -> Dict:
    """
    Run full Monte Carlo simulation of the tournament.
    
    Returns comprehensive statistics including:
    - Win probability for each team
    - Probability of reaching each stage
    - Most likely group outcomes
    - Match-level predictions
    """
    print(f"\n{'='*60}")
    print(f"  Monte Carlo: {label} — {n_simulations:,} simulations")
    print(f"{'='*60}")
    
    # Counters
    champion_count = defaultdict(int)
    finalist_count = defaultdict(int)
    semifinal_count = defaultdict(int)
    quarterfinal_count = defaultdict(int)
    r16_count = defaultdict(int)
    r32_count = defaultdict(int)
    group_advance_count = defaultdict(int)
    
    # Track group winners
    group_winner_count = {g: defaultdict(int) for g in GROUPS}
    group_runner_count = {g: defaultdict(int) for g in GROUPS}
    
    # Track match-level stats (for group stage)
    match_goals = defaultdict(list)
    match_results = defaultdict(lambda: {'w_a': 0, 'draw': 0, 'w_b': 0})
    
    for sim in range(n_simulations):
        if (sim + 1) % 2000 == 0:
            print(f"  Simulation {sim + 1:,}/{n_simulations:,}...")
        
        simulator = TournamentSimulator(predict_fn, seed=seed + sim)
        result = simulator.simulate_tournament()
        
        # Count outcomes
        champion_count[result.champion] += 1
        finalist_count[result.finalist] += 1
        finalist_count[result.champion] += 1  # Champion is also finalist
        
        for team in result.semifinalists:
            semifinal_count[team] += 1
        for team in result.quarterfinalists:
            quarterfinal_count[team] += 1
        for team in result.r16_teams:
            r16_count[team] += 1
        for team in result.r32_teams:
            r32_count[team] += 1
        
        # Group stage stats
        for group_name, standings in result.group_standings.items():
            group_winner_count[group_name][standings[0].team] += 1
            group_runner_count[group_name][standings[1].team] += 1
            # Top 2 advance automatically
            group_advance_count[standings[0].team] += 1
            group_advance_count[standings[1].team] += 1
        
        # Match-level tracking (first simulation only for predicted scores)
        if sim == 0:
            for group_name, matches in result.group_results.items():
                for m in matches:
                    key = f"{m.team_a} vs {m.team_b}"
                    match_goals[key] = {
                        'team_a': m.team_a, 'team_b': m.team_b,
                        'lambda_a': m.lambda_a, 'lambda_b': m.lambda_b,
                        'sample_score': f"{m.goals_a}-{m.goals_b}",
                        'group': group_name,
                    }
        
        # Track W/D/L for each group match
        for group_name, matches in result.group_results.items():
            for m in matches:
                key = f"{m.team_a} vs {m.team_b}"
                if m.goals_a > m.goals_b:
                    match_results[key]['w_a'] += 1
                elif m.goals_a == m.goals_b:
                    match_results[key]['draw'] += 1
                else:
                    match_results[key]['w_b'] += 1
    
    # Compile results
    n = n_simulations
    all_teams = sorted(set(t for g in GROUPS.values() for t in g))
    
    team_probs = {}
    for team in all_teams:
        team_probs[team] = {
            'champion': champion_count[team] / n,
            'finalist': finalist_count[team] / n,
            'semifinal': semifinal_count[team] / n,
            'quarterfinal': quarterfinal_count[team] / n,
            'r16': r16_count[team] / n,
            'r32': r32_count[team] / n,
            'group_advance': group_advance_count[team] / n,
        }
    
    # Group predictions
    group_predictions = {}
    for g in GROUPS:
        group_predictions[g] = {
            'winner_probs': {t: group_winner_count[g][t] / n for t in GROUPS[g]},
            'runner_probs': {t: group_runner_count[g][t] / n for t in GROUPS[g]},
        }
    
    # Match predictions with W/D/L probabilities
    match_predictions = {}
    for key, data in match_goals.items():
        mr = match_results[key]
        data['prob_win_a'] = mr['w_a'] / n
        data['prob_draw'] = mr['draw'] / n
        data['prob_win_b'] = mr['w_b'] / n
        match_predictions[key] = data
    
    # Print top 10
    sorted_champs = sorted(team_probs.items(), key=lambda x: x[1]['champion'], reverse=True)
    print(f"\nTop 10 — Probabilidad de ser Campeón ({label}):")
    for i, (team, probs) in enumerate(sorted_champs[:10]):
        bar = '█' * int(probs['champion'] * 100)
        print(f"  {i+1:2d}. {team:25s} {probs['champion']*100:5.1f}% {bar}")
    
    return {
        'team_probs': team_probs,
        'group_predictions': group_predictions,
        'match_predictions': match_predictions,
        'n_simulations': n_simulations,
        'label': label,
    }
